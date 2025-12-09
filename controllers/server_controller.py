class ServerController:
    def __init__(self, mvcm_service):
        self.mvcm = mvcm_service

    def create_ccs_servers_from_json(self, json_list):
        success_count = 0
        errors = []
        import copy
        data_to_process = copy.deepcopy(json_list)

        for json_obj in data_to_process:
            name = json_obj.pop('name', None)
            if name:
                url = f'/ccs/servers/{name}'
                try:
                    response = self.mvcm.post(url, json_obj)
                    if response.ok:
                        success_count += 1
                    else:
                        errors.append(f"Failed to create {name}: {response.status_code}")
                except Exception as e:
                    errors.append(f"Exception creating {name}: {str(e)}")
            else:
                errors.append("Skipped row: No 'name' key found.")
        return success_count, errors

    def create_consoles_from_json(self, json_list):
        success_count = 0
        errors = []
        import copy
        data_to_process = copy.deepcopy(json_list)

        for json_obj in data_to_process:
            server_name = json_obj.pop('Server', None)
            session_name = json_obj.pop('name', None)
            # Remove unused fields for creation
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
                        errors.append(f"Failed {session_name}: {response.status_code}")
                except Exception as e:
                    errors.append(f"Exception {session_name}: {str(e)}")
            else:
                errors.append("Skipped row: Missing 'Server' or 'name'.")

        return success_count, errors

    def verify_console_connectivity(self, hostname, lu_name, port):
        """
        Hits the network-diagnostics endpoint to check connectivity.
        Payload:
        {
          "hostname": "123.456.789",
          "luName": "TESTBMC",
          "model": "3278-2",
          "port": 9004,
          "useSsl": false
        }
        """
        endpoint = "/network-diagnostics/operations/connect"
                
        payload = {        
            "hostname": "123.456.789",
            "luName": "TESTBMC",
            "model": "3278-2",
            "port": 9004,
            "useSsl": False
        }
        

        print(payload)

        try:
            response = self.mvcm.post(endpoint, payload)
            
            if not response.ok:
                return False, f"HTTP Error {response.status_code}"

            # Parse the response
            # Response structure:
            # { "status": [ { "connected": false, "hostname": "...", "messages": [...] } ] }
            data = response.json()

            print(data)

            print(response.text)

            print(response.status_code)
            
            if "status" in data and len(data["status"]) > 0:
                result = data["status"][0]
                is_connected = result.get("connected", False)
                messages = result.get("messages", [])
                
                if is_connected:
                    return True, "Connected"
                else:
                    return False, "; ".join(messages)
            else:
                return False, "Invalid response format"

        except Exception as e:
            return False, str(e)
