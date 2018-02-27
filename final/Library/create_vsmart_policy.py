#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.viptela import rest_api_lib
import requests
import json
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
        "topology_name": {"required": True, "type": "str"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": 'str'
        }
    }

    # Instantiate Ansible module object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Load all the Ansible parameters into local variables\
    vmanage_ip = module.params['vmanage_ip']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    description = module.params['description']
    topology_name = module.params['topology_name']


    # Instantiate vmanage requests session
    obj = rest_api_lib(vmanage_ip, username, password)
    # Check if VPN list already exists and get VPN list entries
    topologyId = obj.get_topology_by_name(topology_name)

    # Create requests playload for Post and Put methods
    payload = {
        "policyName": name,
        "policyDescription": description,
        "policyType": "feature",
        "isPolicyActivated": "false",
        "policyDefinition": {
            "assembly": [
                {
                    "definitionId": topologyId,
                    "type": "hubAndSpoke"
                }
            ]
        }
    }

    policyId, current_topologyId = obj.get_vsmart_policyId_by_name(name)

    # If the Policy  does not exist, create it via post
    if not policyId:
        if module.check_mode:
            module.exit_json(changed=True)
        response = obj.post_request('template/policy/vsmart', payload=payload)
        if response.status_code == 200:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="Error", payload=payload)
    # If the VPN list does exist, compare the VPN entries, and if necessary, update via post      
    if policyId:
        if current_topologyId == topologyId:
            module.exit_json(changed=False, msg="No changes needed")
        else:
            if module.check_mode:
                module.exit_json(changed=True)
            obj.put_request('template/policy/vsmart/' + policyId, payload=payload)
            module.exit_json(changed=True, msg="Updating Vsmart Policy")

if __name__ == '__main__':
    main()
