class ServerController:
    def __init__(self, mvcm_service):
        self.mvcm = mvcm_service

    def create_ccs_servers_from_json(self, json_list):
        """
        Iterates through JSON data to create servers.
        Returns: (success_count, list_of_error_messages)
        """
        success_count = 0
        errors = []

        # We work on a copy so we don't mutate the original data in the UI
        import copy
        data_to_process = copy.deepcopy(json_list)

        for json_obj in data_to_process:
            # Extract 'name' to build the URL
            name = json_obj.pop('name', None)
            
            if name:
                url = f'/ccs/servers/{name}'
                try:
                    response = self.mvcm.post(url, json_obj)
                    if response.ok:
                        success_count += 1
                    else:
                        errors.append(f"Failed to create {name}: {response.status_code} - {response.text}")
                except Exception as e:
                    errors.append(f"Exception creating {name}: {str(e)}")
            else:
                errors.append("Skipped row: No 'name' key found.")
        
        return success_count, errors

    def create_consoles_from_json(self, json_list):
        """
        Iterates through JSON data to create consoles.
        Returns: (success_count, list_of_error_messages)
        """
        success_count = 0
        errors = []
        
        import copy
        data_to_process = copy.deepcopy(json_list)

        for json_obj in data_to_process:
            # Extract required fields
            server_name = json_obj.pop('Server', None)
            session_name = json_obj.pop('name', None)
            
            json_obj.pop('DR?', None)
            json_obj.pop('LPAR', None)
            json_obj.pop('CU Address', None)
            
            if server_name and session_name:
                url = f'/ccs/servers/{server_name}/sessions/{session_name}'
                try:
                    response = self.mvcm.post(url, json_obj)
                    if response.ok:
                        success_count += 1
                    else:
                        errors.append(f"Failed {session_name} on {server_name}: {response.status_code}")
                except Exception as e:
                    errors.append(f"Exception {session_name}: {str(e)}")
            else:
                errors.append("Skipped row: Missing 'Server' or 'name' fields.")

        return success_count, errors

    def verify_server_start(self, server_name):
        """
        Starts a server, downloads the log, and checks for 'Error exit'.
        Returns: (bool is_success, str message)
        """
        try:
            # 1. Start Server
            endpoint = f"/api/ccs/servers/{server_name}/operations/start"
            self.mvcm.post(endpoint)

            # 2. Get Log
            r = self.mvcm.getlog(server_name)
            if not r.ok:
                return False, f"Failed to retrieve log: {r.status_code}"

            # 3. Parse Log Logic (Moved from View)
            log_text = r.text
            lines = log_text.splitlines()

            if len(lines) >= 3:
                third_to_last = lines[-3]
                if "Error exit" in third_to_last:
                    return False, "Log contains 'Error exit'"
                else:
                    return True, "Success"
            else:
                return False, "Log file too short to verify"
                
        except Exception as e:
            return False, f"Verification Exception: {str(e)}"
