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
        "activate": {"default": False, "type": "bool"},
    }

    # Instantiate Ansible module object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Load all the Ansible parameters into local variables\
    vmanage_ip = module.params['vmanage_ip']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    activate = module.params['activate']


    # Instantiate vmanage requests session
    obj = rest_api_lib(vmanage_ip, username, password)

    # Create requests playload for Post and Put methods
    payload = {}

    policyId, current_topologyId, isactivated = obj.get_vsmart_policyId_by_name(name)

    # If the Policy  does not exist, create it via post
    if not policyId:
        module.fail_json(msg="Policy Does Not Exist")
    # If the VPN list does exist, compare the VPN entries, and if necessary, update via post      
    if policyId:
        if activate == isactivated:
            module.exit_json(changed=False, msg="No changes needed")
        else:
            if module.check_mode:
                module.exit_json(changed=True)
            if activate:
                response = obj.post_request('template/policy/vsmart/activate/' + policyId, payload=payload)
                module.exit_json(changed=True, msg="Updating Vsmart Policy")
            else:
                response = obj.post_request('template/policy/vsmart/deactivate/' + policyId, payload=payload)
                module.exit_json(changed=True, msg="Updating Vsmart Policy")
if __name__ == '__main__':
    main()
