import threading
import queue
from concurrent.futures import ThreadPoolExecutor

class VerificationWorker:
    def __init__(self, mvcm_inst, server_list):
        self.mvcm = mvcm_inst
        self.servers = server_list
        self.result_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.futures = []

    def start(self):
        """Starts the verification process."""
        for server in self.servers:
            if not server: continue
            future = self.executor.submit(self._verify_one, server)
            future.add_done_callback(self._on_done)
            self.futures.append(future)

    def _verify_one(self, server_name):
        """Runs in background thread."""
        try:
            # Start server
            endpoint = f"/api/ccs/servers/{server_name}/operations/start"
            self.mvcm.post(endpoint) 
            
            # Get Logs
            r = self.mvcm.getlog(server_name)
            log_text = r.text
            lines = log_text.splitlines()

            is_success = False
            if len(lines) >= 3:
                third_last = lines[-3]
                is_success = "Error exit" not in third_last
            
            error_msg = lines[-4] if len(lines) >= 4 else "Unknown Error"

            return {
                'server_name': server_name,
                'success': is_success,
                'error': not is_success,
                'error_code': error_msg,
                'logText': log_text
            }
        except Exception as e:
            return {
                'server_name': server_name,
                'success': False,
                'error': True,
                'error_code': str(e),
                'logText': ""
            }

    def _on_done(self, future):
        """Puts result into queue for UI to pick up."""
        try:
            res = future.result()
            self.result_queue.put(res)
        except Exception:
            pass

    def check_progress(self):
        """Returns (is_done, list_of_new_results)"""
        results = []
        try:
            while True:
                results.append(self.result_queue.get_nowait())
        except queue.Empty:
            pass
        
        is_done = all(f.done() for f in self.futures)
        return is_done, results
