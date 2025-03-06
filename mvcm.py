#!/usr/bin/python

import atexit
import requests
import json
import sys
from http import HTTPStatus
from datetime import datetime
import shutil
import os
import zipfile
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

#
# This class manages the connection to the BMC AMI Console Management
# server. 
#
class Mvcm:
    _traceon = False


    #
    # Connect to the server (host) with the username and password
    # 
    def connect(self, host, user, password):
        self.traceon = Mvcm._traceon
        self.traceon = False
        print(f'mvcm connect traceon = {self.traceon}')

        requests.packages.urllib3.disable_warnings()

        self.trace(f"connect {host} {user} {password}")
        self.encrypted = True
        self.host = host
        self.user = user
        self.password = password

        self.apiSession = ''
        self.cookies = {}  # Changed to regular dictionary

        # GET of the product info to get initial cookies
        r = self.get('/productinfo')
        self.trace(f'seed status = {r.status_code}')

        # Parse Set-Cookie header
        if 'Set-Cookie' in r.headers:
            cookies_header = r.headers['Set-Cookie'].split(', ')
            for cookie in cookies_header:
                if 'JSESSIONID=' in cookie:
                    self.jsessionid = cookie.split(';')[0].split('=')[1]
                    self.cookies['JSESSIONID'] = self.jsessionid
                elif 'XSRF-TOKEN=' in cookie:
                    self.xsrf_token = cookie.split(';')[0].split('=')[1]
                    self.cookies['XSRF-TOKEN'] = self.xsrf_token

        # Perform logon
        self.logon()

        atexit.register(self.exiting)


    def logon(self):
        self.trace("logon================================================")
        j = {'userid': self.user, 'password': self.password}
        r = self.post('/viewerlogon', j)
        
        if r.status_code == 200:
            print("Logon Successful")
            # Parse Set-Cookie header for x-api-session
            if 'Set-Cookie' in r.headers:
                cookie_header = r.headers['Set-Cookie']
                if 'x-api-session=' in cookie_header:
                    self.apiSession = cookie_header.split(';')[0].split('=')[1]
                    self.cookies['x-api-session'] = self.apiSession

            self.trace("saving cookies " + str(self.cookies))
        else:
            print('Logon error: ' + str(r.status_code))
            self.trace(str(r.content))
            sys.exit(1)

        return self.apiSession

    #
    # Performs an HTTP GET
    #
    def get(self, path, contentType = 'application/json'):

        self.trace('=======================================================================')
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 
        
        headers['Accept'] = contentType

        self.trace(f'GET /mvcm-api{path}' )
        self.traceheaders(headers)
        self.trace('')

        #self.trace('cookie is ' + str(self.cookies))
        fullurl = self.mkurl(path)
        #self.trace(f'URL: {fullurl}')
        r = requests.get(url=fullurl ,headers = headers, verify=False, cookies=self.cookies)
        self.cookies.update(r.cookies)
        self.trace(f'{r.status_code} {HTTPStatus(r.status_code).phrase}')
        self.traceheaders(r.headers)
        self.trace('')
        if not r.ok:
            print(f'HTTP: {r.status_code} from {self.mkurl(path)}')
        self.trace('content: ' + str(r.content)    )
        data = r.json()
        self.trace(json.dumps(data, indent=2))    
        self.trace('=======================================================================')
        return r
    
    def getzip(self, path, contentType = 'zip'):
        self.trace('=======================================================================')
        headers = {}
        if self.apiSession is not None:
            headers['x-api-session'] = self.apiSession 
        
        headers['Accept'] = 'application/zip'

        self.trace(f'GET /mvcm-api{path}')
        self.traceheaders(headers)
        self.trace('')

        fullurl = self.mkurl(path)
        r = requests.get(url=fullurl, headers=headers, verify=False, cookies=self.cookies)
        self.cookies.update(r.cookies)
        self.trace(f'{r.status_code} {HTTPStatus(r.status_code).phrase}')
        self.traceheaders(r.headers)
        self.trace('')
        if not r.ok:
            print(f'HTTP: {r.status_code} from {self.mkurl(path)}')
        self.trace('content: ' + str(r.content))
        self.trace('=======================================================================')
        return r
    #
    # Performs an HTTP PUT which updates the entity
    #
    def put(self, path, data):
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']
        
        self.trace(f'PUT /mvcm-api{path}' )
        self.trace('Headers')
        self.traceheaders(headers)
        self.trace('Cookies')
        self.traceheaders(self.cookies)
        self.trace('')
        self.trace(json.dumps(data, indent=2))

        r = requests.put(url=self.mkurl(path) ,headers = headers, verify=False, json=data, cookies=self.cookies)
        self.trace(f'{r.status_code} {HTTPStatus(r.status_code).phrase}')
        self.traceheaders(r.headers)
        self.trace('')
        if not r.ok:
            print(f'HTTP: {r.status_code} from {self.mkurl(path)}')
        return r

    #
    # Performs an HTTP POST, which creates an entity
    #
    def post(self, path, content):
        headers = {}
        if self.apiSession is not None:  # Changed to match postbinary's check
            headers['x-api-session'] = self.apiSession

        if 'XSRF-TOKEN' in self.cookies:  # Changed to match postbinary's check
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']
        
        self.trace(f'POST /mvcm-api{path}')
        self.trace('Headers')
        self.traceheaders(headers)
        self.trace('Cookies')
        self.traceheaders(self.cookies)
        self.trace('')
        self.trace('Content: ' + str(content))
        self.trace(json.dumps(content, indent=2))
        
        try:  # Added try-except block like postbinary
            r = requests.post(
                url=self.mkurl(path),
                headers=headers,
                json=content,
                cookies=self.cookies,
                verify=False
            )

            # Update cookies directly from response cookies like postbinary
            self.cookies.update(r.cookies)
            
            self.trace('Response:')
            self.trace(f'   {r.status_code} {HTTPStatus(r.status_code).phrase}')
            self.traceheaders(r.headers)
            self.trace('')
            
            if not r.ok:
                print(f'    HTTP: {r.status_code} from {self.mkurl(path)}')
                print(f'    Request headers sent: {headers}')
                print(f'    Response headers: {dict(r.headers)}')
                print(f'    Response content: {r.text}')
                
            return r

        except Exception as e:
            print(f"Exception during POST request: {str(e)}")
            raise


    def postbinary(self, path, file_path):
        headers = {}
        if self.apiSession is not None:
            headers['x-api-session'] = self.apiSession 

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']

        self.trace(f'POST /mvcm-api{path}')
        self.trace('Headers')
        self.traceheaders(headers)
        self.trace('Cookies')
        self.traceheaders(self.cookies)
        self.trace('')

        try:
            # Check if file exists and is not empty
            if os.path.getsize(file_path) == 0:
                raise ValueError("File is empty. No data to upload.")

            self.trace(f'File size: {os.path.getsize(file_path)} bytes')

            # Create the multipart encoder
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                
                # Send the request
                r = requests.post(
                    self.mkurl(path),
                    headers=headers,
                    files=files,
                    cookies=self.cookies,
                    verify=False
                )

            self.cookies.update(r.cookies)
            self.trace('Response:')
            self.trace(f'   {r.status_code} {HTTPStatus(r.status_code).phrase}')
            self.traceheaders(r.headers)
            
            if not r.ok:
                print(f'    HTTP: {r.status_code} from {self.mkurl(path)}')
                print(f'    Request headers sent: {headers}')
                print(f'    Response headers: {dict(r.headers)}')
                print(f'    Response content: {r.text}')
                
            return r

        except Exception as e:
            print(f"Exception during POST request: {str(e)}")
            raise

    
    #
    # Performs an HTTP DELETE, which removes the entity
    #
    def delete(self, path):
        headers = {}
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']

        self.trace(f'DELETE /mvcm-api{path}' )
        self.traceheaders(headers)
        self.trace('')
        r = requests.delete(url=self.mkurl(path) ,headers = headers, verify=False, cookies=self.cookies)
        self.trace(f'{r.status_code} {HTTPStatus(r.status_code).phrase}')
        return r

    def merge_configurations(self, username, source_hostname, target_hostname, merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir):
        def clear_directory(directory):
            # Walk the directory tree from the bottom up
            for root, dirs, files in os.walk(directory, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        # Ensure the file is writable
                        os.chmod(file_path, 0o777)
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Could not delete file {file_path}: {e}")
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.chmod(dir_path, 0o777)
                        os.rmdir(dir_path)
                    except Exception as e:
                        print(f"Could not delete directory {dir_path}: {e}")

        try:

            # Optionally clear the directories without admin rights
            for dir_path in [source_extract_dir, target_extract_dir, merge_file_dir]:
                if os.path.exists(dir_path):
                    clear_directory(dir_path)  # use the helper function defined above

            # Define source and target zip paths within the base directory
            source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
            target_zip = os.path.join(merge_base_dir, "target_Merge.zip")

            print(f"\nSource zip size: {os.path.getsize(source_zip)} bytes")
            print(f"Target zip size: {os.path.getsize(target_zip)} bytes")

            print("\nExtracting source zip...")
            with zipfile.ZipFile(source_zip, 'r') as zip_ref:
                zip_ref.extractall(source_extract_dir)

            print("\nExtracting target zip...")
            with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                zip_ref.extractall(target_extract_dir)

            print("\nCopying all files from source...")
            for item in os.listdir(source_extract_dir):
                s = os.path.join(source_extract_dir, item)
                d = os.path.join(merge_file_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

            print("\nDeleting directories from merge that will be replaced:")
            directories_to_replace = ['licensemanager', 'tomcat', 'security']
            for directory in directories_to_replace:
                merged_dir_path = os.path.join(merge_file_dir, directory)
                if os.path.exists(merged_dir_path):
                    print(f"- Deleting /{directory}")
                    shutil.rmtree(merged_dir_path)

            print("\nCopying directories from target:")
            for directory in directories_to_replace:
                target_dir_path = os.path.join(target_extract_dir, directory)
                merged_dir_path = os.path.join(merge_file_dir, directory)
                if os.path.exists(target_dir_path):
                    print(f"- Copying /{directory}")
                    shutil.copytree(target_dir_path, merged_dir_path)

            # Create merged zip file with specific naming convention
            current_date = datetime.now().strftime("%d%b%Y").upper()
            version = "4.1.05"
            source_server = source_hostname.split('.')[0].upper()
            target_server = target_hostname.split('.')[0].upper()
            merged_zip_name = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"

            # Update descriptor.xml if it exists
            descriptor_path = os.path.join(merge_file_dir, "descriptor.xml")
            if os.path.exists(descriptor_path):
                print("\nUpdating descriptor.xml...")
                # Read the current content
                with open(descriptor_path, 'r') as file:
                    content = file.read()
                
                # Parse XML
                root = ET.fromstring(content)
                
                # Update the name field
                name_element = root.find('name')
                if name_element is not None:
                    name_element.text = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"
                    print(f"Updated name in descriptor.xml to: {name_element.text}")

                # Update the description field
                description_element = root.find('description')
                if description_element is not None:
                    description_element.text = f"Config from {source_server} brought to {target_server} on {current_date}"
                    print(f"Updated description in descriptor.xml to: {description_element.text}")

                # Write back the modified XML
                tree = ET.ElementTree(root)
                tree.write(descriptor_path, encoding='utf-8', xml_declaration=True)
                
                # Format the XML file with proper indentation
                with open(descriptor_path, 'r') as file:
                    xml_content = file.read()
                dom = xml.dom.minidom.parseString(xml_content)
                pretty_xml = dom.toprettyxml(indent="    ")
                with open(descriptor_path, 'w') as file:
                    file.write(pretty_xml)
            else:
                print("Warning: descriptor.xml not found in merge directory")

            merged_zip_path = os.path.join(merge_base_dir, merged_zip_name)

            # Clean up any existing zip file
            if os.path.exists(f"{merged_zip_path}.zip"):
                os.remove(f"{merged_zip_path}.zip")

            print("\nCreating merged zip file...")
            # Change to the parent directory of mergeFile
            original_dir = os.getcwd()
            os.chdir(merge_base_dir)
            
            # Create the zip file using shutil.make_archive
            shutil.make_archive(merged_zip_path, 'zip', 'mergeFile')
            
            # Change back to the original directory
            os.chdir(original_dir)

            print(f"\nMerged zip contents:")
            with zipfile.ZipFile(f"{merged_zip_path}.zip", 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print(f"Total files: {len(file_list)}")
                print("Key directories:")
                for d in directories_to_replace:
                    files = [f for f in file_list if f.startswith(f"{d}/")]
                    print(f"- /{d}/: {len(files)} files")

            # Create a copy with a 'c' prefix NO COPY CREATED 
            copy_zip_name = f"c{merged_zip_name}.zip"
            copy_zip_path = os.path.join(merge_base_dir, copy_zip_name)

            print(f"\nMerged zip files created:")
            print(f"- Original Location: {merged_zip_path}.zip")
            print(f"- Size: {os.path.getsize(f'{merged_zip_path}.zip')} bytes")

            return f"{merged_zip_path}.zip"

        except Exception as e:
            print(f"Error during merge: {str(e)}")
            raise
    #
    # Exit hook. You can perform more cleanup here.
    #
    def exiting(self):
        self.trace('exiting')


    #
    # Prints a debugging message if traceon is true
    #
    def trace(self, msg):
        if self.traceon == True:
            print(f'[Mvcm] : {msg}')

    #
    # Prints the HTTP headers, if traceon is true
    def traceheaders(self, headers):
        for k in headers.keys():
            self.trace(f'    {k}: {headers[k]}' )


    #
    # Creates a full URL from the partial path
    #
    def mkurl(self, path):
        if self.encrypted:
            url = 'https://' + self.host + '/mvcm-api' + path
        else:
            url = 'http://' + self.host  + '/mvcm-api' + path
        return url



    #
    # Extracts a cookie from the returned headers
    #
    def extractCookie(self, r, cookieName):
        cookies = r.headers['set-cookie']
        return cookies

    #
    # Removes a cookie from our jar
    #
    def removeCookie(self, cookieName):
        self.cookies.pop(cookieName)



'''if __name__ == "__main__":
    connector = Mvcm()
    connectInfo = ConnectInfo()

    connector.connect(connectInfo.host, connectInfo.user, connectInfo.password) '''