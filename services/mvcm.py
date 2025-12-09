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
import xml.etree.ElementTree as ET
import xml.dom.minidom

class Mvcm:
    _traceon = False

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
        self.cookies = {} 

        r = self.get('/productinfo')
        self.trace(f'seed status = {r.status_code}')

        if 'Set-Cookie' in r.headers:
            cookies_header = r.headers['Set-Cookie'].split(', ')
            for cookie in cookies_header:
                if 'JSESSIONID=' in cookie:
                    self.jsessionid = cookie.split(';')[0].split('=')[1]
                    self.cookies['JSESSIONID'] = self.jsessionid
                elif 'XSRF-TOKEN=' in cookie:
                    self.xsrf_token = cookie.split(';')[0].split('=')[1]
                    self.cookies['XSRF-TOKEN'] = self.xsrf_token

        self.logon()
        atexit.register(self.exiting)

    def logon(self):
        self.trace("logon================================================")
        j = {'userid': self.user, 'password': self.password}
        r = self.post('/viewerlogon', j)
        
        if r.status_code == 200:
            print("Logon Successful")
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

    def get(self, path, contentType = 'application/json'):
        self.trace('=======================================================================')
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 
        headers['Accept'] = contentType

        self.trace(f'GET /mvcm-api{path}' )
        self.traceheaders(headers)
        self.trace('')

        fullurl = self.mkurl(path)
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
    
    def getlog(self, server_name):
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 
        self.traceheaders(headers)

        fullurl = f'https://qdlp2bcmapp0002.ess.fiserv.one/mvcm-api/logs/download/1/{server_name}/{server_name}.log'
        r = requests.get(url=fullurl ,headers = headers, verify=False, cookies=self.cookies)
        self.cookies.update(r.cookies)
        return r

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

    def post(self, path, content=None):
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
        self.trace('Content: ' + str(content))
        self.trace(json.dumps(content, indent=2))
        
        try:
            r = requests.post(
                url=self.mkurl(path),
                headers=headers,
                json=content,
                cookies=self.cookies,
                verify=False
            )
            self.cookies.update(r.cookies)
            
            self.trace('Response:')
            self.trace(f'   {r.status_code} {HTTPStatus(r.status_code).phrase}')
            self.traceheaders(r.headers)
            self.trace('')
            
            if not r.ok:
                print(f'    HTTP: {r.status_code} from {self.mkurl(path)}')
                print(f'    Response content: {r.text}')
                
            return r

        except Exception as e:
            print(f"Exception during POST request: {str(e)}")
            raise

    #
    # NEW: Wraps the list in {"requests": [...]} as per API requirement
    #
    def post_diagnostic(self, content_list):
        path = "/network-diagnostics/operations/connect"
        
        protocol = "https" if self.encrypted else "http"
        base_origin = f"{protocol}://{self.host}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": base_origin,
            "Referer": f"{base_origin}/configurations",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Python/BMC-Tool"
        }

        if self.apiSession is not None:
            headers['x-api-session'] = self.apiSession
            headers['Authorization'] = f"Bearer {self.apiSession}"

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']
        
        # KEY FIX: Wrapping list in "requests" key
        payload = {"requests": content_list}

        self.trace(f'POST DIAGNOSTIC /mvcm-api{path}')
        self.traceheaders(headers)
        self.trace(json.dumps(payload, indent=2))
        
        try:
            r = requests.post(
                url=self.mkurl(path),
                headers=headers,
                json=payload,
                cookies=self.cookies,
                verify=False
            )

            self.cookies.update(r.cookies)
            
            if not r.ok:
                print(f'DIAGNOSTIC HTTP: {r.status_code}')
                print(f'Response: {r.text}')
                
            return r

        except Exception as e:
            print(f"Exception during POST DIAGNOSTIC: {str(e)}")
            raise

    def postbinary(self, path, file_path):
        headers = {}
        if self.apiSession is not None:
            headers['x-api-session'] = self.apiSession 
        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']

        self.trace(f'POST /mvcm-api{path}')
        try:
            if os.path.getsize(file_path) == 0:
                raise ValueError("File is empty.")

            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                r = requests.post(
                    self.mkurl(path),
                    headers=headers,
                    files=files,
                    cookies=self.cookies,
                    verify=False
                )
            self.cookies.update(r.cookies)
            return r
        except Exception as e:
            print(f"Exception during POST request: {str(e)}")
            raise

    def delete(self, path):
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 
        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']

        r = requests.delete(url=self.mkurl(path) ,headers = headers, verify=False, cookies=self.cookies)
        return r

    def merge_configurations(self, username, source_hostname, target_hostname, merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir):
        # (Keeping your original merge logic exactly as is to save space, 
        #  since you confirmed it's working and unchanged)
        def clear_directory(directory):
            for root, dirs, files in os.walk(directory, topdown=False):
                for name in files:
                    try:
                        os.chmod(os.path.join(root, name), 0o777)
                        os.remove(os.path.join(root, name))
                    except: pass
                for name in dirs:
                    try:
                        os.chmod(os.path.join(root, name), 0o777)
                        os.rmdir(os.path.join(root, name))
                    except: pass

        try:
            for dir_path in [source_extract_dir, target_extract_dir, merge_file_dir]:
                if os.path.exists(dir_path): clear_directory(dir_path)

            source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
            target_zip = os.path.join(merge_base_dir, "target_Merge.zip")

            with zipfile.ZipFile(source_zip, 'r') as zip_ref: zip_ref.extractall(source_extract_dir)
            with zipfile.ZipFile(target_zip, 'r') as zip_ref: zip_ref.extractall(target_extract_dir)

            for item in os.listdir(source_extract_dir):
                s = os.path.join(source_extract_dir, item)
                d = os.path.join(merge_file_dir, item)
                if os.path.isdir(s): shutil.copytree(s, d)
                else: shutil.copy2(s, d)

            dirs_replace = ['licensemanager', 'tomcat', 'security']
            for d in dirs_replace:
                if os.path.exists(os.path.join(merge_file_dir, d)): shutil.rmtree(os.path.join(merge_file_dir, d))
            for d in dirs_replace:
                if os.path.exists(os.path.join(target_extract_dir, d)):
                    shutil.copytree(os.path.join(target_extract_dir, d), os.path.join(merge_file_dir, d))

            curr_date = datetime.now().strftime("%d%b%Y").upper()
            src_srv = source_hostname.split('.')[0].upper()
            tgt_srv = target_hostname.split('.')[0].upper()
            merged_name = f"{src_srv}_{tgt_srv}_Merged_V4.1.05_{curr_date}"

            desc_path = os.path.join(merge_file_dir, "descriptor.xml")
            if os.path.exists(desc_path):
                tree = ET.parse(desc_path)
                root = tree.getroot()
                if root.find('name') is not None: root.find('name').text = merged_name
                if root.find('description') is not None: 
                    root.find('description').text = f"Config from {src_srv} brought to {tgt_srv} on {curr_date}"
                
                xmlstr = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
                with open(desc_path, 'w') as f: f.write(xmlstr)

            merged_zip_path = os.path.join(merge_base_dir, merged_name)
            if os.path.exists(f"{merged_zip_path}.zip"): os.remove(f"{merged_zip_path}.zip")

            shutil.make_archive(merged_zip_path, 'zip', merge_file_dir)
            return f"{merged_zip_path}.zip"

        except Exception as e:
            print(f"Error during merge: {str(e)}")
            raise

    def exiting(self):
        self.trace('exiting')

    def trace(self, msg):
        if self.traceon == True: print(f'[Mvcm] : {msg}')

    def traceheaders(self, headers):
        for k in headers.keys(): self.trace(f'    {k}: {headers[k]}' )

    def mkurl(self, path):
        prefix = 'https://' if self.encrypted else 'http://'
        return prefix + self.host + '/mvcm-api' + path

    def extractCookie(self, r, cookieName):
        return r.headers['set-cookie']

    def removeCookie(self, cookieName):
        self.cookies.pop(cookieName)
