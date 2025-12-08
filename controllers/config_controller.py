import os
import threading
import tempfile
from services.mvcm import Mvcm  # Import Mvcm class to create new connections for merging

class ConfigController:
    def __init__(self, mvcm_service):
        self.mvcm = mvcm_service

    def connect_to_new_host(self, hostname, user, pwd):
        """Used by ActionPanel to switch the active global connection"""
        self.mvcm.connect(hostname, user, pwd)

    def get_saved_configurations(self):
        try:
            r = self.mvcm.get("/saved-configurations", "application/json")
            return r.json() if r.ok else []
        except Exception:
            return []

    def download_configuration(self, config_name, download_location):
        try:
            r = self.mvcm.getzip('/saved-configurations/' + config_name, 'zip')
            if r.status_code == 200:
                # Ensure directory exists
                os.makedirs(os.path.dirname(download_location), exist_ok=True)
                with open(download_location, 'wb') as f:
                    f.write(r.content)
                return True
            return False
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def restore_configuration(self, config_name):
        try:
            response = self.mvcm.post(f'/saved-configurations/{config_name}/operations/restore', None)
            return response.ok
        except Exception:
            return False

    def upload_configuration(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False
            response = self.mvcm.postbinary('/saved-configurations', file_path)
            return response.ok
        except Exception:
            return False

    def create_configuration(self, name, description):
        try:
            data = {"name": name, "description": description if description else None}
            response = self.mvcm.post('/saved-configurations/' + name, data)
            return response.ok
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Update / Merge Logic (Moved from BusinessController)
    # -------------------------------------------------------------------------
    def run_update_async(self, source_host, target_host, username, password, callback):
        """
        Runs the update process in a separate thread to prevent UI freezing.
        callback(success: bool, message: str) is called upon completion.
        """
        def task():
            try:
                success = self._perform_merge_logic(source_host, target_host, username, password)
                if success:
                    callback(True, "Update process completed successfully!")
                else:
                    callback(False, "Update process failed (Check console/logs).")
            except Exception as e:
                callback(False, f"Update Exception: {str(e)}")

        t = threading.Thread(target=task, daemon=True)
        t.start()

    def _perform_merge_logic(self, source_hostname, target_hostname, username, password):
        """
        The complex logic originally in BusinessController.update_configuration.
        """
        try:
            with tempfile.TemporaryDirectory() as merge_base_dir:
                # Setup directories
                source_extract_dir = os.path.join(merge_base_dir, "sourceExtracted")
                target_extract_dir = os.path.join(merge_base_dir, "targetExtracted")
                merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
                
                os.makedirs(source_extract_dir, exist_ok=True)
                os.makedirs(target_extract_dir, exist_ok=True)
                os.makedirs(merge_file_dir, exist_ok=True)
                
                # Create NEW connections for this specific task
                source_conn = Mvcm()
                target_conn = Mvcm()
                source_conn.connect(source_hostname, username, password)
                target_conn.connect(target_hostname, username, password)
                
                # Cleanup old temp configs on servers
                self._safe_delete(source_conn, '/saved-configurations/source_Merge')
                self._safe_delete(target_conn, '/saved-configurations/target_Merge')
                
                # Create temp configs
                source_conn.post('/saved-configurations/source_Merge', 
                               {"name": 'source_Merge', "description": 'Temp source config'})
                target_conn.post('/saved-configurations/target_Merge', 
                               {"name": 'target_Merge', "description": 'Temp target config'})

                # Download zips
                src_resp = source_conn.getzip('/saved-configurations/source_Merge', 'zip')
                tgt_resp = target_conn.getzip('/saved-configurations/target_Merge', 'zip')
                
                if not src_resp.ok or not tgt_resp.ok:
                    return False

                source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
                target_zip = os.path.join(merge_base_dir, "target_Merge.zip")
                
                with open(source_zip, 'wb') as f: f.write(src_resp.content)
                with open(target_zip, 'wb') as f: f.write(tgt_resp.content)
                    
                # Perform the file merge (Using the logic inside Mvcm class)
                # Note: We use source_conn to call merge_configurations, but it's a utility method really.
                merged_zip_path = source_conn.merge_configurations(
                    username, source_hostname, target_hostname,
                    merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir
                )
                
                # Upload result to target
                if os.path.exists(merged_zip_path):
                    response = target_conn.postbinary('/saved-configurations', merged_zip_path)
                    return response.ok
                    
                return False

        except Exception as e:
            print(f"Error in _perform_merge_logic: {str(e)}")
            return False

    def _safe_delete(self, connection, path):
        try:
            connection.delete(path)
        except Exception:
            pass
