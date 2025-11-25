import threading
import time
import json
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

class LogRetrievalWorker:
    def __init__(self, controller, base_url, date_filter, time_filter):
        self.controller = controller
        self.base_url = base_url
        self.date_filter = date_filter
        self.time_filter = time_filter
        self.log_queue = queue.Queue() # For log messages (timings)
        self.data_queue = queue.Queue() # For final data
        self.running = False

    def start(self):
        self.running = True
        t = threading.Thread(target=self._run_process, daemon=True)
        t.start()

    def _log(self, msg):
        self.log_queue.put(msg)

    def _run_process(self):
        start_t = time.time()
        self._log(f"Starting retrieval. Date: {self.date_filter}, Time: {self.time_filter}")

        # 1. Get Packages
        try:
            resp = self.controller.mvcm.getalllogs(self.base_url)
            packages = resp.json()
        except Exception as e:
            self._log(f"Error fetching packages: {e}")
            return

        # 2. Get Lists
        logs_to_download = []
        for i, package in enumerate(packages, 1):
            try:
                r = self.controller.mvcm.getalllogs(f'{self.base_url}/{i}')
                files = r.json().get('logFiles', [])
                for f in files:
                    d_mod = f.get('dateModified')
                    if not self.date_filter or self.date_filter == "0000-00-00" or (d_mod and d_mod >= self.date_filter):
                        logs_to_download.append((i, f.get('parent'), f.get('name'), package.get('name')))
            except: pass

        self._log(f"Found {len(logs_to_download)} logs.")

        # 3. Download in Parallel
        results = {}
        with ThreadPoolExecutor(max_workers=10) as exe:
            futures = {exe.submit(self._download_one, item): item for item in logs_to_download}
            
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        results[res['name']] = res
                except Exception as e:
                    self._log(f"Error: {e}")

        total_t = time.time() - start_t
        self._log(f"Finished in {total_t:.2f}s")
        self.data_queue.put(results)

    def _download_one(self, item):
        idx, parent, name, l_type = item
        # Simplified download logic for brevity
        url = f'{self.base_url}/download/{idx}/{parent}/{name}' if parent else f'{self.base_url}/download/{idx}/{name}'
        
        # Here you would implement your cache check (omitted for brevity, can pass cache in __init__)
        resp = self.controller.mvcm.getalllogs(url)
        content = resp.text
        
        # Simple Filter
        if self.time_filter and self.time_filter not in content:
            return None # Skip if time not found
            
        return {'name': name, 'type': l_type, 'content': content}
