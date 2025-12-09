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
        endpoint = "/network-diagnostics/operations/connect"
        
        # 1. Sanitize Data (Crucial for Excel imports)
        # Strip whitespace from strings which often causes 400 errors
        clean_host = str(hostname).strip() if hostname else ""
        clean_lu = str(lu_name).strip() if lu_name else ""
        
        # Ensure port is a pure integer
        try:
            clean_port = int(float(port)) if port else 23
        except (ValueError, TypeError):
            clean_port = 23

        # 2. Build Payload
        payload_object = {
            "hostname": clean_host,
            "luName": clean_lu,
            "model": "3278-2",
            "port": clean_port,
            "useSsl": False
        }

        # 3. Headers (Match Browser exactly)
        # Sometimes missing 'Content-Type' causes 400s on lists
        extra_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # 4. WRAP IN LIST [ ... ]
            # We must use the list because that is what the API expects for batch processing.
            # We explicitly pass the headers to ensure the server knows it's JSON.
            # Note: We need to access the underlying requests session or pass headers to mvcm.post
            # Since mvcm.post doesn't accept extra headers in your current script, 
            # we will rely on requests automatic handling but clean the data first.
            
            # If your Mvcm.post method doesn't support merging headers, 
            # the standard requests.post behavior usually works if data is clean.
            
            response = self.mvcm.post(endpoint, [payload_object])
            
            # 5. DEBUGGING: Check exactly why the 400 happened
            if not response.ok:
                print(f"\n!!! API ERROR {response.status_code} !!!")
                print(f"Sent: {[payload_object]}")
                print(f"Server Message: {response.text}") # <--- This tells you WHY it failed
                return False, f"HTTP {response.status_code}: {response.text}"

            data = response.json()

            print(data)

            print(response.text)

            print(response.status_code)
            
            if "status" in data and len(data["status"]) > 0:
                result = data["status"][0]
                if result.get("connected"):
                    return True, "Connected"
                else:
                    msgs = result.get("messages", [])
                    return False, "; ".join(msgs)
            else:
                return False, "Server returned empty status (Check Hostname/LU validity)"

        except Exception as e:
            return False, str(e)


