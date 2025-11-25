# core/api_service.py
import os
import tempfile
import mvcm  # Assuming this is your custom library
from core.utils import printResponseError

class ApiService:
    def __init__(self, mvcm_instance):
        self.mvcm = mvcm_instance

    def connect(self, hostname, username, password):
        try:
            return self.mvcm.connect(hostname, username, password)
        except Exception:
            pass

    def loop_logon(self, username, password, servers):
        for server in servers:
            try:
                resp = self.mvcm.connect(server[1], username, password)
                if resp.status_code == 200:
                    return 200
                elif resp.status_code == 403:
                    return 403
            except Exception:
                pass
        return 500

    def get_saved_configurations(self):
        r = self.mvcm.get("/saved-configurations", "application/json")
        return r.json() if r.ok else []
    
    def download_configuration(self, config_name, download_location):
        r = self.mvcm.getzip('/saved-configurations/' + config_name, 'zip')
        if r.status_code == 200:
            with open(download_location, 'wb') as f:
                f.write(r.content)
            return True
        else:
            return False

    def restore_configuration(self, config_name):
        response = self.mvcm.post(f'/saved-configurations/{config_name}/operations/restore', None)
        if not response.ok:
            printResponseError(response)
        return response.ok

    def upload_configuration(self, file_path):
        response = self.mvcm.postbinary('/saved-configurations', file_path)
        return response.ok

    def create_configuration(self, name, description):
        data = {"name": name, "description": description if description else None}
        response = self.mvcm.post('/saved-configurations/' + name, data)
        return response.ok

    def update_configuration(self, source_hostname, target_hostname, username, password):
        try:
            with tempfile.TemporaryDirectory() as merge_base_dir:
                source_extract_dir = os.path.join(merge_base_dir, "sourceExtracted")
                target_extract_dir = os.path.join(merge_base_dir, "targetExtracted")
                merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
                
                os.makedirs(source_extract_dir, exist_ok=True)
                os.makedirs(target_extract_dir, exist_ok=True)
                os.makedirs(merge_file_dir, exist_ok=True)
                
                source_connection = mvcm.Mvcm()
                target_connection = mvcm.Mvcm()
                source_connection.connect(source_hostname, username, password)
                target_connection.connect(target_hostname, username, password)
                
                # Cleanup existing
                try: source_connection.delete('/saved-configurations/source_Merge')
                except: pass
                try: target_connection.delete('/saved-configurations/target_Merge')
                except: pass
                
                # Create temp configs
                source_connection.post('/saved-configurations/source_Merge', {"name": 'source_Merge', "description": 'Source merge temp'})
                target_connection.post('/saved-configurations/target_Merge', {"name": 'target_Merge', "description": 'Target merge temp'})

                # Download
                s_resp = source_connection.getzip('/saved-configurations/source_Merge', 'zip')
                t_resp = target_connection.getzip('/saved-configurations/target_Merge', 'zip')
                
                source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
                target_zip = os.path.join(merge_base_dir, "target_Merge.zip")
                
                with open(source_zip, 'wb') as f: f.write(s_resp.content)
                with open(target_zip, 'wb') as f: f.write(t_resp.content)
                    
                # Merge logic (assuming merge_configurations is part of mvcm library based on your code)
                merged_zip_path = source_connection.merge_configurations(
                    username, source_hostname, target_hostname,
                    merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir
                )
                
                if os.path.exists(merged_zip_path):
                    response = target_connection.postbinary('/saved-configurations', merged_zip_path)
                    return response.ok
                return False
        except Exception as e:
            print(f"Error in update_configuration: {str(e)}")
            return False

    # --- Moved Logic from Excel Parser ---
    
    def create_ccs_servers_batch(self, json_list):
        """Processes a list of server dictionaries and uploads them."""
        for json_obj in json_list:
            name = json_obj.pop('name', None)
            if name:
                url = f'/ccs/servers/{name}'
                response = self.mvcm.post(url, json_obj)
                if not response.ok:
                    printResponseError(response)
                    print(f"Failed to create CCS server for {name}")
                    return False
            else:
                return False
        return True

    def create_ccs_consoles_batch(self, json_list):
        """Processes a list of console dictionaries and uploads them."""
        for json_obj in json_list:
            serverName = json_obj.pop('Server', None)
            sessionName = json_obj.pop('name', None)
            # Remove keys we don't need for the payload
            json_obj.pop('DR?', None)
            json_obj.pop('LPAR', None)
            json_obj.pop('CU Address', None)
            
            if serverName and sessionName:
                url = f'/ccs/servers/{serverName}/sessions/{sessionName}'
                response = self.mvcm.post(url, json_obj)
                if not response.ok:
                    print(f"Failed to create CCS session {sessionName} for {serverName}")
                    return False
            else:
                return False
        return True
