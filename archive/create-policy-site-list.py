from viptilapyclient import rest_api_lib
from yaml import load


try:
    settings = load(open('settings.yml', 'r').read())
except IOError as er:
    raise Exception(er)

try:
    username = settings["username"]
    password = settings["password"]
    vmanage_ip = settings["vmanage_ip"]
except KeyError as er:
    raise Exception(er)

rc = rest_api_lib(vmanage_ip, username, password)

rsp = rc.create_policy_site_list(name="TEST-Site-1", entries=["20", "30"])


print(rsp)








