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
        "type": {
            "required": True,
            "choices": ["site", "prefix", "vpn", "app"],
            "type": "str"
        },
        "description": {
            "default": "Created by Ansible",
            "required": False, "type": "str"},
        "entries": {"required": True, "type": "list"},
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
    if module.params["type"] == "prefix":
        resp = obj.policy_prefix(**module.params)
    elif module.params["type"] == "site":
        resp = obj.policy_site(**module.params)
    elif module.params["type"] == "vpn":
        resp = obj.policy_vpn(**module.params)
    elif module.params["type"] == "app":
        resp = obj.policy_app(**module.params)
    else:
        module.exit_json(failed=True, msg="could not find a suitable module for type: {}".format(module.params["type"]))

    module.exit_json(**resp)

if __name__ == '__main__':
    main()
