#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.viptela import rest_api_lib
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main():
    # Define Ansible module argument spec
    module_args = {
        "vmanage_ip": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "name": {"required": True, "type": "str"},
        "description": {"required": False, "type": "str"},
        "vpn_list": {"required": True, "type": "str"},
        "hub_site_list": {"required": True, "type": "str"},
        "spoke_site_list": {"required": True, "type": "str"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": 'str'
        }
    }

    # Instantiate Ansible module object
    module = AnsibleModule(argument_spec=module_args)

    # Load all the Ansible parameters into local variables\
    vmanage_ip = module.params['vmanage_ip']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    description = module.params['description']
    vpn_list_name = module.params['vpn_list']
    hub_site_list_name = module.params['hub_site_list']
    spoke_site_list_name = module.params['spoke_site_list']

    # Instantiate vmanage requests session
    obj = rest_api_lib(vmanage_ip, username, password)
    # Check if VPN list already exists and get VPN list entries
    vpn_listId, vpn_entries = obj.get_vpn_list_by_name(vpn_list_name)
    hub_listId, hub_entries = obj.get_site_list_by_name(hub_site_list_name)
    spoke_listId, spoke_entries = obj.get_site_list_by_name(spoke_site_list_name)

    # Create requests playload for Post and Put methods
    payload = {
        "name": name,
        "type": "hubAndSpoke",
        "description": description,
        "definition": {
            "vpnList": vpn_listId,
            "subDefinitions": [
                {
                    "name": "My Hub and Spoke",
                    # "equalPreference": "true",
                    # "advertiseTloc": "false",
                    "spokes": [
                        {
                            "siteList": spoke_listId,
                            "hubs": [
                                {
                                    "siteList": hub_listId
                                    # "prefixLists": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    definitionId = obj.get_topology_by_name(name)
    
    if not definitionId:
        response = obj.post_request('template/policy/definition/hubandspoke', payload=payload)
        if response.status_code == 200:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="Error", definitionId=definitionId, payload=payload)

    current_vpnId, current_spokeId, current_hubId = obj.get_topology_details(definitionId)
    if current_vpnId == vpn_listId and current_spokeId == spoke_listId and current_hubId == hub_listId:
        module.exit_json(changed=False, msg="No changes needed")
    else:
        obj.put_request('template/policy/definition/hubandspoke/' + definitionId, payload=payload)
        module.exit_json(changed=True, msg="Updating Topology", definitionId=definitionId)

if __name__ == '__main__':
    main()
