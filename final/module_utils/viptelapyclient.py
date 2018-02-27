"""
Class with REST Api GET and POST libraries

Example: python rest_api_lib.py vmanage_hostname username password

PARAMETERS:
    vmanage_hostname : Ip address of the vmanage or the dns name of the vmanage
    username : Username to login the vmanage
    password : Password to login the vmanage

Note: All the three arguments are manadatory
"""
import requests
import sys
from json import dumps, loads
from copy import deepcopy

requests.packages.urllib3.disable_warnings()


class rest_api_lib:
    def __repr__(self):
        return "Connected to vManage at {} as {}".format(self.vmanage_ip, self.username)

    def __init__(self, vmanage_ip, username, password):
        self.vmanage_ip = vmanage_ip
        self.username = username
        self.session = {}
        self.login(self.vmanage_ip, username, password)

    def login(self, vmanage_ip, username, password):
        """Login to vmanage"""
        base_url_str = "https://{}/".format(vmanage_ip)

        login_action = '/j_security_check'

        # Format data for loginForm
        login_data = {'j_username': username, 'j_password': password}

        # Url for posting login data
        login_url = base_url_str + login_action

        url = base_url_str + login_url

        sess = requests.session()

        # If the vmanage has a certificate signed by a trusted authority change verify to True
        resp = sess.post(url=login_url, data=login_data, verify=False)

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        if len(resp.text) > 0:
            raise Exception("Check login credentials")

        self.session[vmanage_ip] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = "https://{}:8443/dataservice/{}".format(self.vmanage_ip, mount_point)
        print(url)

        response = self.session[self.vmanage_ip].get(url, verify=False)
        data = response.text
        return data

    def post_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):
        """POST request"""
        url = "https://{}:8443/dataservice/{}".format(self.vmanage_ip, mount_point)
        payload = dumps(payload)
        response = self.session[self.vmanage_ip].post(url=url, data=payload, headers=headers, verify=False)
        return response.text

    def put_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):
        """POST request"""
        url = "https://%s:8443/dataservice/%s" % (self.vmanage_ip, mount_point)
        payload = dumps(payload)
        response = self.session[self.vmanage_ip].put(url=url, data=payload, headers=headers, verify=False)
        return response

    def delete_request(self, mount_point, payload={}, headers={'Content-Type': 'application/json'}):
        """POST request"""
        url = "https://%s:8443/dataservice/%s" % (self.vmanage_ip, mount_point)
        payload = dumps(payload)
        response = self.session[self.vmanage_ip].delete(url=url, data=payload, headers=headers, verify=False)
        return response

    def __policy_interface(
            self, name=None, entries=None, description=None, action=None, uri_path=None, policy_key=None,
            state=None, policy_type=None, **kwargs):
        if not name and not entries:  # ensure both name and entries are provided
            raise Exception("Check params")
        if not isinstance(name, str):  # ensure that the name variable is a type of string
            raise Exception("name: must be a string")
        if not isinstance(description, str):  # ensure that the description variable is a type of string
            raise Exception("description: must be a string")
        if not isinstance(action, str):  # ensure that the action variable is a type of string
            raise Exception("action: must be a string [create, force, delete]")
        if not isinstance(entries, list):  # ensore that the entries variable is a type of list
            raise Exception("entries: must be a list ids as strings")
        for index in range(len(entries)):  # check entries values are strings, check each item in entries
            if not isinstance(entries[index], str):
                try:
                    entries[index] = str(entries[index])
                except:
                    return_msg = {
                        "failed": True,
                        "msg": "Check your entries list"
                    }
                    return return_msg

        resp = self.get_request(uri_path)  # get the JSON from the API
        results = loads(resp)  # convert the JSON to a dictionary
        # ensure the name hasn't already been used
        used_names = {item["name"]: item for item in results["data"]}

        # TODO: check "referenceCount" and warn before changing a used resource

        if state == "absent":
            listId = used_names.get(name, {}).get("listId")
            if listId:
                resp = self.delete_request(uri_path + "/" + listId)
                return_msg = {
                    "changed": True,
                    "msg": resp.text
                }
                return return_msg
            else:
                return_msg = {
                    "changed": False,
                    "msg": "{} object with name {} not found".format(policy_key, name)
                }
                return return_msg

        elif action == "create" or action == "update":
            do_change = True
            listId = False
            if used_names.get(name):
                do_change = False
                existing_dict = used_names.get(name)
                listId = existing_dict["listId"]
                existing_set = {entry[policy_key] for entry in existing_dict["entries"]}
                existing_set = list(existing_set)
                #existing_set = sorted(existing_set, key=lambda x: int(x))
                for new_id in entries:
                    if new_id not in existing_set:
                        do_change = True

            if not do_change:
                return_msg = {
                    "changed": False,
                    "msg": "No changes required, {} already exists".format(policy_key)
                }
                return return_msg
            elif do_change and listId and action != "update":
                return_msg = {
                    "changed": False,
                    "failed": True,
                    "msg": 'The {} object {} already exists with different ids, use action: "update" to change.'.format(policy_key, name)
                }
                return return_msg

            # ensure the  ids haven't already been used
            used_ids = {entry[policy_key].replace(" ", ""): result for result in results["data"] for entry in result["entries"]}  # extract the unique values
            for entry in entries:
                if used_ids.get(entry) and used_ids.get(entry)["listId"] != listId:
                    return_msg = {
                        "changed": False,
                        "failed": True,
                        "msg": "The id {} is already in use by {} List {}".format(entry, policy_key, used_ids[entry]["name"])
                    }
                    return return_msg

            # construct the payload for the POST
            req_payload = {
                "name": name,
                "type": policy_type,
                "entries": []
            }

            if description:
                req_payload["description"] = description

            for entry in entries:
                req_payload["entries"].append(
                    {
                        policy_key: str(entry)
                    }
                )

            if listId:
                req_payload["listId"] = listId
                _ = self.put_request(uri_path + "/" + listId, req_payload)
                old_ids = list(existing_set)
                return_msg = {
                    "changed": True,
                    "msg": "The {} list has been updated. Previous values: {}".format(policy_key, old_ids)
                }
                return return_msg
            else:
                _ = self.post_request(uri_path, req_payload)
                return_msg = {
                    "changed": True,
                    "msg": "The {} list has been created.".format(policy_key)
                }
                return return_msg

    def policy_vpn(self, **kwargs):
        kwargs["uri_path"] ='template/policy/list/vpn'
        kwargs["policy_type"] = "vpn"
        kwargs["policy_key"] = "vpn"
        return self.__policy_interface(**kwargs)

    def policy_site(self, **kwargs):
        kwargs["uri_path"] = 'template/policy/list/site'
        kwargs["policy_type"] = "site"
        kwargs["policy_key"] = "siteId"
        return self.__policy_interface(**kwargs)

    def policy_prefix(self, **kwargs):
        kwargs["uri_path"] = 'template/policy/list/prefix'
        kwargs["policy_type"] = "prefix"
        kwargs["policy_key"] = "ipPrefix"
        return self.__policy_interface(**kwargs)

    def hubAndSpoke_subDefinition(
            self,
            equalPreference=True,  # All hubs are equal (All Spokes Sites connect to all Hubs)
            advertiseTloc=False,  # Advertise Hub TLOCs
            name=None,  # used for definition and subDefinition names
            spokes=None,  # an unordered list of spokes
            hubs=None,  # an ordered list of hubs
            prefixLists=None,  # optional > an ordered list of lists containing prefixes for each hub
            uri_path="template/policy/definition/hubandspoke",
            state=None
    ):

        assert isinstance(equalPreference, bool)
        assert isinstance(advertiseTloc, bool)
        assert isinstance(name, str)
        assert isinstance(spokes, list)
        assert isinstance(hubs, list)
        if prefixLists:
            assert isinstance(prefixLists, list)

        resp = self.get_request(uri_path)
        short_topologies = loads(resp)["data"]
        long_topologies = {}
        for topology in short_topologies:
            definitionId = topology["definitionId"]
            resp = self.get_request("{}/{}".format(uri_path, definitionId))
            topology_detail = loads(resp)
            long_topologies[definitionId] = topology_detail


        def_used_names = {}
        subdef_used_names = {}
        subdef_used_vpns = {}
        subdef_used_spokes = {}
        subdef_used_hubs = {}
        subdef_used_prefixLists = {}

        for topology in long_topologies:
            topology = long_topologies[topology]
            def_name = topology["name"]
            def_used_names[def_name] = topology
            vpnList = topology["definition"]["vpnList"]
            subdef_used_vpns[vpnList] = topology
            for subdef in topology["definition"]["subDefinitions"]:
                subdef_name = subdef["name"]
                subdef_used_names[subdef_name] = topology
                for spoke in subdef["spokes"]:
                    spoke_siteList = spoke["siteList"]
                    subdef_used_spokes[spoke_siteList] = topology
                    for hub in spoke["hubs"]:
                        hub_siteList = hub["siteList"]
                        subdef_used_hubs[hub_siteList] = topology
                        for prefixList in hub.get("prefixLists", []):  # not all topologies have the prefixLists key
                            subdef_used_prefixLists[prefixList] = topology

        if subdef_used_names.get(name):
            if state == "absent":
                definitionId = subdef_used_names.get(name)["definitionId"]
                resp = self.delete_request("{}/{}".format(uri_path, definitionId))
                return_msg = {
                    "changed": True,
                    "failed": False,
                    "msg": "The topology has been deleted"
                }
                return return_msg
            return_msg = {
                "changed": False,
                "failed": True,
                "msg": "A topology with the subDefinition name {} has already been \
                created by {} for {} {}/{}".format(
                    name,
                    subdef_used_names[name]["owner"], subdef_used_names[name]["name"], uri_path,
                    subdef_used_names[name]["definitionId"])
            }
            return return_msg

        # TODO: check used VPN, hub, spoke, prefix

        # ensure the hub and spokes are already present
        resp = self.get_request('template/policy/list/site')
        site_lists = loads(resp)["data"]
        site_list_names = {}
        for site_list in site_lists:
            site_list_name = site_list["name"]
            listId = site_list["listId"]
            site_list_names.setdefault(site_list_name, listId)
        for hub in hubs:
            if not site_list_names.get(hub):
                return_msg = {
                    "changed": False,
                    "failed": True,
                    "msg": "hub not found: {}".format(hub)
                }
                return return_msg

        for spoke in spokes:
            if not site_list_names.get(spoke):
                return_msg = {
                    "changed": False,
                    "failed": True,
                    "msg": "spoke not found: {}".format(spoke)
                }
                return return_msg

        # TODO: check the prefixes

        subDefinition = {
            "equalPreference": equalPreference,
            "advertiseTloc": advertiseTloc,
            "name": name,
            "spokes": []
        }

        spoke_structure = {
            "siteList": "",
            "hubs": []
        }

        hub_structure = {
            "siteList": "",
            "prefixLists": []
        }

        for spoke in spokes:
            this_spoke = deepcopy(spoke_structure)
            this_spoke["siteList"] = site_list_names[spoke]
            for hub in hubs:
                this_hub = deepcopy(hub_structure)
                this_hub["siteList"] = site_list_names[hub]
                # TODO: add prefix logic
                this_spoke["hubs"].append(this_hub)
            subDefinition["spokes"].append(this_spoke)
        return subDefinition

    def create_topology(
            self,
            name=None,  # used for definition and subDefinition names
            vpnList=None,  # a string with the vpn list name
            topology_type=None,  # a string of the topology type being created
            subDefinitions=None,
            description="Created by Ansible"):  # optional description


        assert isinstance(topology_type, str)
        valid_topology_types = {
            "hubAndSpoke": {
                "uri_path": "template/policy/definition/hubandspoke",
                "supported": True
            },
            "mesh": {
                "uri_path": "template/policy/definition/mesh",
                "supported": False
            },
            "control": {
                "uri_path": "template/policy/definition/control",
                "supported": False
            }
        }
        if valid_topology_types.get(topology_type):
            if not valid_topology_types[topology_type]["supported"]:
                return_msg = {
                    "changed": False,
                    "failed": True,
                    "msg": "This topology type isn't supported yet, call harrison"
                }
                return return_msg
            uri_path = valid_topology_types[topology_type]["uri_path"]
        else:
            return_msg = {
                "changed": False,
                "failed": True,
                "msg": "Valid topology_type values are {}".format([key for key in valid_topology_types])
            }
            return return_msg

        assert isinstance(vpnList, str)
        assert isinstance(description, str)
        assert isinstance(subDefinitions, list)

        # ensure the vpn list is already present
        resp = self.get_request('template/policy/list/vpn')
        vpn_lists = loads(resp)["data"]
        vpn_list_names = {}
        for vpn_list in vpn_lists:
            vpn_list_name = vpn_list["name"]
            listId = vpn_list["listId"]
            vpn_list_names.setdefault(vpn_list_name, listId)
        if not vpn_list_names.get(vpnList):
            return_msg = {
                "changed": False,
                "failed": True,
                "msg": "vpn not found: {}".format(vpnList)
            }
            return return_msg



        req_payload = {
            "name": name,
            "type": topology_type,
            "description": description,
            "definition": {
                "vpnList": vpn_list_names[vpnList],
                "subDefinitions": subDefinitions
            }
        }

        resp = self.post_request(uri_path, req_payload)
        return_msg = {
            "changed": True,
            "failed": False,
            "msg": resp
        }
        return return_msg

    def apply_policy(
            self,
            isPolicyActivated=False,
            description="Created by Ansible",
            name=None,
            policyType="feature",
            topologies=None,
            action=None,
            state=None,

    ):

        #uri_path = 'template/policy/vsmart/'
        uri_path = 'template/policy/vsmart'

        req_payload = {
          "isPolicyActivated": isPolicyActivated,
          "policyDefinition": {"assembly": []},
          "policyDescription": description,
          "policyName": name,
          "policyType": policyType
        }

        assembly_struct = {"definitionId": None, "type": None}


        # is the name already in use?
        resp = self.get_request(uri_path)
        data = loads(resp)["data"]

        used_policyNames = {}
        for policy in data:
            policyDefinition = loads(policy["policyDefinition"])
            policy["policyDefinition"] = policyDefinition
            policyName = policy["policyName"]
            used_policyNames[policyName] = policy

        if used_policyNames.get(name):
            if state == "absent":
                policyId = used_policyNames.get(name)["policyId"]
                this_uri_path = "{}/{}".format(uri_path, policyId)
                resp = self.delete_request(this_uri_path)
                return_msg = {
                    "changed": True,
                    "failed": False,
                    "msg": "The policy {} has been deleted".format(name)
                }
                return return_msg
            return_msg = {
                "changed": False,
                "failed": True,
                "msg": "A policy with the name {} is has already been created by {}".format(
                    name, used_policyNames[name]["createdBy"])
            }
            return return_msg

        # to the topologies exist already?
        hubandspokes = loads(self.get_request('template/policy/definition/hubandspoke'))["data"]
        hubandspokes = {hns["name"]: hns for hns in hubandspokes}
        #mesh = self.get_request('template/policy/definition/mesh')
        #control = self.get_request('template/policy/definition/control')

        topology_keys = ["hubandspoke", "mesh", "control"]

        for topology in topologies:
            for topology_type in topology:
                topology_name = topology[topology_type]
                if topology_type not in topology_keys:
                    return_msg = {
                        "changed": False,
                        "failed": True,
                        "msg": "The topology type {} is not recognized".format(topology_type)
                    }
                    return return_msg
                if topology_type == "hubandspoke":
                    if not hubandspokes.get(topology_name):
                        return_msg = {
                            "changed": False,
                            "failed": True,
                            "msg": "The hubandspoke topology {} does not exist".format(topology_name)
                        }
                        return return_msg
                    # all is well, add this topology to the payload
                    this_definitionId = hubandspokes.get(topology_name, {}).get("definitionId")
                    if this_definitionId:
                        this_assembly_struct = deepcopy(assembly_struct)
                        this_assembly_struct["definitionId"] = this_definitionId
                        this_assembly_struct["type"] = "hubAndSpoke"
                        req_payload["policyDefinition"]["assembly"].append(this_assembly_struct)
                    else:
                        return_msg = {
                            "changed": False,
                            "failed": True,
                            "msg": "Couldn't find the definitionId for {}".format(topology_name)
                        }
                        return return_msg
                else:
                    return_msg = {
                        "changed": False,
                        "failed": True,
                        "msg": "The topology type {} is not yet supported".format(topology_type)
                    }
                    return return_msg

        resp = self.post_request(uri_path, req_payload)
        return_msg = {
            "changed": True,
            "failed": False,
            "msg": resp
        }
        return return_msg



