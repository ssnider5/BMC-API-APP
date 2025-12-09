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
            # Remove unused fields
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
        Sanitizes data, wraps it in a list, and calls Mvcm.post_diagnostic
        to handle the strict header requirements.
        """
        # 1. Prepare Data
        clean_host = str(hostname).strip() if hostname else ""
        clean_lu = str(lu_name).strip() if lu_name else ""
        try:
            clean_port = int(float(port)) if port else 23
        except (ValueError, TypeError):
            clean_port = 23

        # 2. Build List Payload (required by API)
        payload_list = [{
            "hostname": clean_host,
            "luName": clean_lu,
            "model": "3278-2",
            "port": clean_port,
            "useSsl": False
        }]

        try:
            # 3. Call the specialized MVCM method
            response = self.mvcm.post_diagnostic(payload_list)

            if not response.ok:
                return False, f"HTTP Error {response.status_code}"

            data = response.json()
            
            if "status" in data and len(data["status"]) > 0:
                result = data["status"][0]
                if result.get("connected"):
                    return True, "Connected"
                else:
                    msgs = result.get("messages", [])
                    return False, "; ".join(msgs)
            else:
                return False, "Server returned empty status"

        except Exception as e:
            return False, str(e)
