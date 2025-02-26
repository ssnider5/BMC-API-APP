#!/usr/bin/python

import requests
import json
import sys

import mvcm
import connectinfo


m = mvcm.Mvcm()
connectInfo = connectinfo.ConnectInfo()

m.connect(connectInfo.host, connectInfo.user, connectInfo.password)


print('=========================================')
r = m.get('/ccs/servers')
print(f'Status: {r.status_code}')

if r.status_code == 403:
    print('Login denied')
    sys.exit(1)
print('=========================================')


names = [
    'ABLE',
    'BAKR',
    'CRLY',
    'DLTA',
    'ECHO',
    'FXTR',
    'GRGE',
    'HOTL',
]


for name in names:


    serverPath = f'/ccs/servers/{name}'
    r = m.get(serverPath)
    if r.status_code != 404:
        print(f'Deleting {name}')
        m.delete(serverPath)

    newServer = {}
    newServer['upstreamHost'] = 'clm-aus-006632.bmc.com'
    newServer['startupMode'] = 'manual'
    newServer['controllerType'] = 2

    print(f'Creating server {name}')
    r = m.post(serverPath, newServer)
    if not r.ok:
        print(f'Error creating server {name} : {r.status_code}')
        sys.exit(255)


    sessname = name
    newSession = {}
    newSession['luName'] = sessname
    newSession['desription'] = 'Description for ' + sessname
    newSession['viewerAccess'] = True
    newSession['vtam'] = False

    print(f'Creating session {sessname}')
    r = m.post(f'{serverPath}/sessions/{sessname}', newSession)
    if not r.ok:
        print(f'Error creating session {name}/{sessname} : {r.status_code}')
        sys.exit(255)

