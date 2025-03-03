import mvcm
import os
import tempfile

def printResponseError(response):
    # Print all details about the response
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.content}")
    print(f"Text: {response.text}")
    print(f"JSON: {response.json() if response.headers.get('Content-Type') == 'application/json' else 'Not a JSON response'}")
    print(f"URL: {response.url}")
    print(f"Elapsed Time: {response.elapsed}")
    print(f"Request Headers: {response.request.headers}")
    print(f"Request Method: {response.request.method}")
    print(f"Request URL: {response.request.url}")

class BusinessController:
    def __init__(self, mvcm_instance):
        self.mvcm = mvcm_instance

    def connect(self, hostname, username, password):
        self.mvcm.connect(hostname, username, password)

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
        filename = os.path.basename(file_path)
        response = self.mvcm.postbinary('/saved-configurations', file_path)
        return response.ok

    def create_configuration(self, name, description):
        data = {"name": name, "description": description if description else None}
        response = self.mvcm.post('/saved-configurations/' + name, data)
        return response.ok

    def update_configuration(self, source_hostname, target_hostname, username, password):
        try:
            # Create a temporary directory for the merge process
            with tempfile.TemporaryDirectory() as merge_base_dir:
                # Create subdirectories for extraction and merging
                source_extract_dir = os.path.join(merge_base_dir, "sourceExtracted")
                target_extract_dir = os.path.join(merge_base_dir, "targetExtracted")
                merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
                
                os.makedirs(source_extract_dir, exist_ok=True)
                os.makedirs(target_extract_dir, exist_ok=True)
                os.makedirs(merge_file_dir, exist_ok=True)
                
                # Create MVCM connections
                source_connection = mvcm.Mvcm()
                target_connection = mvcm.Mvcm()
                source_connection.connect(source_hostname, username, password)
                target_connection.connect(target_hostname, username, password)
                
                # Try to delete existing configurations on servers
                try:
                    source_connection.delete('/saved-configurations/source_Merge')
                except Exception:
                    pass
                    
                try:
                    target_connection.delete('/saved-configurations/target_Merge')
                except Exception:
                    pass
                
                # Create new configurations
                source_data = {"name": 'source_Merge', "description": 'Newly created source config to be merged'}
                target_data = {"name": 'target_Merge', "description": 'Newly created target config to be merged'}
                
                source_connection.post('/saved-configurations/source_Merge', source_data)
                target_connection.post('/saved-configurations/target_Merge', target_data)

                # Download configurations
                source_response = source_connection.getzip('/saved-configurations/source_Merge', 'zip')
                target_response = target_connection.getzip('/saved-configurations/target_Merge', 'zip')
                
                # Save downloaded zip files in the temporary directory
                source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
                target_zip = os.path.join(merge_base_dir, "target_Merge.zip")
                
                with open(source_zip, 'wb') as f:
                    f.write(source_response.content)
                with open(target_zip, 'wb') as f:
                    f.write(target_response.content)
                    
                # Merge configurations using the temporary directories
                merged_zip_path = source_connection.merge_configurations(
                    username, source_hostname, target_hostname,
                    merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir
                )
                
                # Upload merged configuration if the merged zip file exists
                success = False
                if os.path.exists(merged_zip_path):
                    response = target_connection.postbinary('/saved-configurations', merged_zip_path)
                    success = response.ok
                    
                # Temporary files and directories are automatically removed here
                return success

        except Exception as e:
            print(f"Error in update_configuration: {str(e)}")
            return False