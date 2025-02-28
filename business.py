import mvcm
import os


def printResponseError(response):
    # Print all details about the response
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.content}")
    print(f"Text: {response.text}")
    print(f"JSON: {response.json() if response.headers['Content-Type'] == 'application/json' else 'Not a JSON response'}")
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
        user_docs = os.path.join(os.path.expanduser('~'),
                                "OneDrive - Fiserv Corp", "Documents", "MergedSaveConfig")
        os.makedirs(user_docs, exist_ok=True)
        
        source_connection = mvcm.Mvcm()
        target_connection = mvcm.Mvcm()
        source_connection.connect(source_hostname, username, password)
        target_connection.connect(target_hostname, username, password)
        
        # Try to delete existing files on server first, ignoring any errors
        try:
            source_connection.delete('/saved-configurations/source_Merge')
        except Exception:
            pass
            
        try:
            target_connection.delete('/saved-configurations/target_Merge')
        except Exception:
            pass
        
        #Then create them
        data = {"name": 'source_Merge', "description": 'Newly created source config to be merged'}
        response = source_connection.post('/saved-configurations/source_Merge', data)
        data = {"name": 'target_Merge', "description": 'Newly created target config to be merged'}
        response = target_connection.post('/saved-configurations/target_Merge', data)

        #Now download them
        source_response = source_connection.getzip('/saved-configurations/source_Merge', 'zip')
        target_response = target_connection.getzip('/saved-configurations/target_Merge', 'zip')
        source_zip = os.path.join(user_docs, "source_Merge.zip")
        target_zip = os.path.join(user_docs, "target_Merge.zip")
        
        with open(source_zip, 'wb') as f:
            f.write(source_response.content)
        with open(target_zip, 'wb') as f:
            f.write(target_response.content)
            
        merged_zip_path = source_connection.merge_configurations(username, source_hostname, target_hostname)
        if os.path.exists(merged_zip_path):
            response = target_connection.postbinary('/saved-configurations', merged_zip_path)
            success = response.ok
        else:
            success = False
            
        try:
            if os.path.exists(merged_zip_path):
                os.remove(merged_zip_path)
        except Exception:
            pass
            
        return success
    
    def printResponseError(response):
        # Print all details about the response
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Content: {response.content}")
        print(f"Text: {response.text}")
        print(f"JSON: {response.json() if response.headers['Content-Type'] == 'application/json' else 'Not a JSON response'}")
        print(f"URL: {response.url}")
        print(f"Elapsed Time: {response.elapsed}")
        print(f"Request Headers: {response.request.headers}")
        print(f"Request Method: {response.request.method}")
        print(f"Request URL: {response.request.url}")