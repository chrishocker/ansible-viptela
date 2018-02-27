#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.viptelapyclient import rest_api_lib
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
        "description": {
            "default": "Created by Ansible",
            "required": False, "type": "str"},
        "topologies": {"required": True, "type": "list"},
        "action": {
            "default": "create",
            "choices": ["create", "update"],
            "type": "str"
        },
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": 'str'
        }
    }

    # Instantiate Ansible module object
    module = AnsibleModule(argument_spec=module_args)

    # Build API session
    vmanage_ip = module.params['vmanage_ip']
    username = module.params['username']
    password = module.params['password']
    obj = rest_api_lib(vmanage_ip, username, password)

    # hammer time
    resp = obj.apply_policy(
        description=module.params["description"],
        name=module.params["name"],
        topologies=module.params["topologies"],
        action=module.params["action"],
        state=module.params["state"])

    module.exit_json(**resp)

if __name__ == '__main__':
    main()
