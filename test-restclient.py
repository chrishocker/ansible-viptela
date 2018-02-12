from viptilapyclient import rest_api_lib
from yaml import load
from json import loads

settings = loads(open('settings.json', 'r').read())


username = "admin"
password = "3FVT6nKPKAH2NdG"
vmanage_ip = "199.66.188.81"


rc = rest_api_lib(vmanage_ip, username, password)

resp = rc.create_vpn(name="Test4", entries=["521", "531"])

print(resp)



