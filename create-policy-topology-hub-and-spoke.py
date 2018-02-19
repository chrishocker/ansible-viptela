from viptilapyclient import rest_api_lib
from yaml import load
from json import dumps


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

print(rc)

resp = rc.create_policy_topology_hub_and_spoke(hubs=["Syed", "Hub"], spokes=["Spokes"], vpnList="Test7")

print(dumps(resp, indent=4))
'''

template/policy/list/site






#print(resp)

url = "https://199.66.188.81/dataservice/template/policy/definition/hubandspoke"

payload = "{\"name\":\"policy-topo-hub-and-spoke-chocker\",\"type\":\"hubAndSpoke\",\"description\":\"Created by Postman\",\"definition\":{\"vpnList\":\"4d598724-c349-4540-a10b-18eb0243fc19\",\"subDefinitions\":[{\"name\":\"My Hub-and-Spoke\",\"equalPreference\":true,\"advertiseTloc\":false,\"spokes\":[{\"siteList\":\"ac52570b-6055-4af2-8ba0-2e5ed969bbda\",\"hubs\":[{\"siteList\":\"565558a4-27b8-4697-bf6a-d33cb00d8c6a\",\"prefixLists\":[]}]}]}]}}"
'''