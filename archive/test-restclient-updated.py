from viptilapyclient import rest_api_lib
from yaml import load
from random import randint


settings = load(open('settings.yml', 'r').read())

username = settings["username"]
password = settings["password"]
vmanage_ip = settings["vmanage_ip"]

rc = rest_api_lib(vmanage_ip, username, password)

vpn = "HM-vpn"
hub = "HM-hub"
spoke = "HM-spoke"


vpn_list_id = rc.create_vpn(name=vpn, entries=[str(randint(600, 700)) for _ in range(2)])
hub_list_id = rc.create_site(name=hub, entries=[str(randint(600, 700)) for _ in range(2)])
spoke_list_id = rc.create_site(name=spoke, entries=[str(randint(600, 700)) for _ in range(2)])


hns = rc.hubAndSpoke_subDefinition(
    name="test hns topo2",
    spokes=[spoke_list_id],
    hubs=[hub_list_id]
)


resp = rc.create_topology(
    name="Topology-test-hm2",
    vpnList=vpn_list_id,
    topology_type="hubAndSpoke",
    subDefinitions=[hns])


print(resp)
