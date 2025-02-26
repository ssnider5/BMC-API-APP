#!/usr/bin/python

import requests
import mvcm
import connectinfo

print('==================================================')

m = mvcm.Mvcm()

connectInfo = connectinfo.ConnectInfo()

m.connect(connectInfo.host, connectInfo.user, connectInfo.password)

m.traceon = False

print('Get Saved Configurations=================================================')
r = m.get('/saved-configurations/Q2_Backup_V4-1-05_13Feb25', 'zip')

if r.status_code == 200:
    # Save the ZIP file content
    zip_file_path = r"C:\Users\F7JB1KS\OneDrive - Fiserv Corp\Documents\BMC API\saved_configurations.zip"
    with open(zip_file_path, 'wb') as f:
        f.write(r.content)
    print(f'Successfully downloaded the ZIP file to {zip_file_path}')
else:
    print(f'Failed to retrieve configurations. Status code: {r.status_code}')

print('==================================================')
