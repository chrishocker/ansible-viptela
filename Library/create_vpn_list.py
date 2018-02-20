#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.viptela import rest_api_lib
import requests
import sys
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main():
    module_args = {
        "vmanage_ip": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "name": {"required": True, "type": "str"},
        "description": {"required": False, "type": "str"},
        "vpns": {"required": True, "type": "list"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": 'str'
        }
    }

    module = AnsibleModule(argument_spec=module_args)

    vmanage_ip = module.params['vmanage_ip']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    description = module.params['description']
    entries = []
    for vpn in module.params['vpns']:
        entries.append({"vpn": str(vpn)})
    payload = {
        "name": name,
        "description": description,
        "entries": entries
    }

    obj = rest_api_lib(vmanage_ip, username, password)
    listId, current_entries = obj.get_vpn_list_by_name(module.params['name'])

    if not listId:
        response = obj.post_request('template/policy/list/vpn', payload=payload)
    else:
        if obj.compare_vpn_list_entries(current_entries, entries):
            module.exit_json(changed=False, msg="No changes needed", listId=listId)
        else:
            obj.put_request('template/policy/list/vpn/' + listId, payload=payload)
            module.exit_json(changed=True, msg="Updating Entries", listId=listId)

    if response.status_code == 200:
        #listId = response.json()['listId']
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="Error", listId=listId)


if __name__ == '__main__':
    main()
