#!/usr/bin/python

from connectinfo import ConnectInfo
import atexit
import requests
import json
import sys
import zipfile
import io
from http import HTTPStatus
from http.cookiejar import CookieJar

from urllib3.exceptions import InsecureRequestWarning

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

        self.trace('connect 1')
        self.host = host
        self.user = user
        self.password = password

        self.apiSession = ''
        self.cookies = requests.cookies.RequestsCookieJar()

        # 
        # GET of the product info. This gets the CSRF token 
        # in a cookie
        r = self.get('/productinfo')
        self.trace(f'seed status = {r.status_code}')

        self.logon()

        atexit.register(self.exiting)


    #
    # Performs a logon with the credentials provided in the connect call
    #
    def logon(self):
        self.trace("logon================================================")
        j = {'userid' : self.user, 'password' :  self.password}
        r = self.post('/viewerlogon', j)
        if r.status_code == 200:
            print("Logon Successful")
        if r.status_code != 200:
            print('Logon error: ' + str(r.status_code))
            self.trace(str(r.content))
            sys.exit(1)
        self.trace('Content: ' + str(r.content))
        self.trace('Content: ')
        self.trace(json.dumps(r.json(), indent=2))    
        self.apiSession = r.json()["token"]
        self.trace('logon api session = ' + self.apiSession)
        self.cookies = { 'x-api-session' : self.apiSession }
        self.trace("saving cookies " + str(self.cookies))
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
            self.print(f'HTTP: {r.status_code} from {self.mkurl(path)}')
        return r

    #
    # Performs an HTTP POST, which creates an entity
    #
    def post(self, path, content):
        headers = {}
        if self.apiSession != None:
            headers['x-api-session'] = self.apiSession 

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']
        
        self.trace(f'POST /mvcm-api{path}' )
        self.trace('Headers')
        self.traceheaders(headers)
        self.trace('Cookies')
        self.traceheaders(self.cookies)
        self.trace('')
        self.trace('Content: ' + str(content))
        self.trace(json.dumps(content, indent=2))
        
        r = requests.post(url=self.mkurl(path) ,headers = headers, json=content, verify=False, cookies=self.cookies)

        self.cookies.update(r.cookies)
        self.trace('Response:')
        self.trace(f'   {r.status_code} {HTTPStatus(r.status_code).phrase}')
        self.traceheaders(r.headers)
        self.trace('')
        self.trace(f'    status: {r.status_code} from {self.mkurl(path)}')
        if not r.ok:
            self.print(f'    HTTP: {r.status_code} from {self.mkurl(path)}')
        return r


    def postbinary(self, path, content):
        headers = {}
        if self.apiSession is not None:
            headers['x-api-session'] = self.apiSession 

        if 'XSRF-TOKEN' in self.cookies:
            headers['X-XSRF-TOKEN'] = self.cookies['XSRF-TOKEN']
    
        headers['Content-Type'] = 'application/octetstream'
    
        self.trace(f'POST /mvcm-api{path}')
        self.trace('Headers')
        self.traceheaders(headers)
        self.trace('Cookies')
        self.traceheaders(self.cookies)
        self.trace('')
        self.trace('Content: (binary data)')
    
        r = requests.post(url=self.mkurl(path), headers=headers, data=content, verify=False, cookies=self.cookies)

        self.cookies.update(r.cookies)
        self.trace('Response:')
        self.trace(f'   {r.status_code} {HTTPStatus(r.status_code).phrase}')
        self.traceheaders(r.headers)
        self.trace('')
        self.trace(f'    status: {r.status_code} from {self.mkurl(path)}')
        if not r.ok:
            print(f'    HTTP: {r.status_code} from {self.mkurl(path)}')
        return r
    
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