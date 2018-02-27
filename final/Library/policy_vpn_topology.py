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
            "choices": ["hubandspoke", "mesh", "control"],
            "type": "str"
        },
        "description": {
            "default": "Created by Ansible",
            "required": False, "type": "str"},
        "vpn": {"required": True, "type": "str"},
        "hubs": {"required": True, "type": "list"},
        "prefixes": {"required": False, "type": "list"},
        "spokes": {"required": True, "type": "list"},
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

    def not_supported():
        module.exit_json(failed=True, msg="module does not yet support type: {}".format(module.params["type"]))

    # hammer time
    if module.params["type"] == "hubandspoke":
        hns = obj.hubAndSpoke_subDefinition(
            name="{}-{}".format(module.params["name"], module.params["type"]),
            spokes=module.params["spokes"],
            hubs=module.params["hubs"],
            state=module.params["state"])

        if hns.get("failed") or hns.get("changed"):
            module.exit_json(**hns)

        resp = obj.create_topology(
            name=module.params["name"],
            vpnList=module.params["vpn"],
            topology_type="hubAndSpoke",
            subDefinitions=[hns])
        module.exit_json(**resp)

    if module.params["type"] == "mesh":
        not_supported()
    if module.params["type"] == "control":
        not_supported()
    else:
        module.exit_json(failed=True, msg="could not find a suitable module for type: {}".format(module.params["type"]))

    module.exit_json(**resp)

if __name__ == '__main__':
    main()
