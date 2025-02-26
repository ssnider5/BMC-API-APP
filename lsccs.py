#!/usr/bin/python

import requests
import json

import mvcm
import connectinfo


print('==================================================')

m = mvcm.Mvcm()

connectInfo = connectinfo.ConnectInfo()

m.connect(connectInfo.host, connectInfo.user, connectInfo.password)

m.traceon = False

print('Get CCS=================================================')
r = m.get('/ccs/servers')

j = r.json()

serverName = "Server name"
upstreamHost = "Upstream Host"
upstreamPort = "Port"
sessionName = "Console Name"
luName  = "LU Name"

serverNameWidth = 14
hostWidth = 30
portWidth = 6
sessNameWidth = 14
luNameWidth = 14

print(f'{serverName:<{serverNameWidth}} {upstreamHost:<{hostWidth}} {upstreamPort:<{portWidth}} {sessionName:<{sessNameWidth}} {luName:<{luNameWidth}}')
print(f'{"-"*serverNameWidth} {"-"*hostWidth} {"-"*portWidth} {"-"*sessNameWidth} {"-"*luNameWidth}')



for s in j['servers']:
    r2 = m.get(f'/ccs/servers/{s["name"]}/sessions')
    j2 = r2.json()
    for sess in j2['sessions']:
        print(f'{s["name"]:<{serverNameWidth}} {s["upstreamHost"]:<{hostWidth}} {sess["upstreamPort"]:>{portWidth}} {sess["name"]:<{sessNameWidth}} {sess['luName']:<{luNameWidth}}')
