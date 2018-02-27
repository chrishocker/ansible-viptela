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

    def create_vpn(self, name=None, entries=None):
        if not name and not entries:  # ensure both name and entries are provided
            raise Exception("Check params")
        if not isinstance(name, str):  # ensure that the name variable is a type of string
            raise Exception("name: must be a string")
        if not isinstance(entries, list):  # ensore that the entries variable is a type of list
            raise Exception("entries: must be a list of vpn ids as strings")
        for item in entries:  # check entries values are strings, check each item in entries
            if not isinstance(item, str):
                raise Exception(
                    "entries list must contain strings or integers, found {} as type {}".format(item, type(item))
                )

        resp = self.get_request('template/policy/list/vpn')  # get the JSON from the API
        results = loads(resp)  # convert the JSON to a dictionary

        # ensure the name hasn't already been used
        used_vpn_names = {vpn["name"]: {} for vpn in results["data"]}
        if used_vpn_names.get(name):
            raise Exception("The name {} has already been used by another VPN List".format(name))

        # ensure the VPN ids haven't already been used
        used_vpn_ids = {entry["vpn"].replace(" ", ""): vpn["name"] for vpn in results["data"] for entry in
                        vpn["entries"]}  # extract the unique VPN values
        for entry in entries:
            if used_vpn_ids.get(entry):
                raise Exception("The VPN id {} is already in use by VPN List {}".format(entry, used_vpn_ids[entry]))

        # construct the payload for the POST
        req_payload = {
            "name": name,
            "description": "Created by viptilapyclient",
            "type": "vpn",
            "listId": None,
            "entries": []
        }

        for vpn_id in entries:
            req_payload["entries"].append(
                {
                    "vpn": vpn_id
                }
            )
        response = self.post_request('template/policy/list/vpn', req_payload)
        return response

    def create_site(self, name=None, entries=None):
        if not name and not entries:  # ensure both name and entries are provided
            raise Exception("Check params")
        if not isinstance(name, str):  # ensure that the name variable is a type of string
            raise Exception("name: must be a string")
        if not isinstance(entries, list):  # ensore that the entries variable is a type of list
            raise Exception("entries: must be a list of vpn ids as strings")
        for item in entries:  # check entries values are strings, check each item in entries
            if not isinstance(item, str):
                raise Exception(
                    "entries list must contain strings or integers, found {} as type {}".format(item, type(item))
                )

        resp = self.get_request('template/policy/list/site')
        results = loads(resp)  # convert the JSON to a dictionary

        # ensure the name hasn't already been used
        used_site_names = {site["name"]: {} for site in results["data"]}
        if used_site_names.get(name):
            raise Exception("The name {} has already been used by another VPN List".format(name))

        # ensure the Site ids haven't already been used
        used_site_ids = {entry["siteId"].replace(" ", ""): site["name"] for site in results["data"] for entry in
                         site["entries"]}  # extract the unique Site ids values
        for entry in entries:
            if used_site_ids.get(entry):
                raise Exception("The Site id {} is already in use by Site List {}".format(entry, used_site_ids[entry]))

        # construct the payload for the POST
        req_payload = {
            "listId": None,
            "entries": [],
            "type": "site",
            "name": name,
            "description": "Created by viptilapyclient"
        }

        for site_list in entries:
            req_payload["entries"].append(
                {
                    "siteId": site_list
                }
            )

        response = self.post_request('template/policy/list/site', req_payload)
        return response

    # TODO: create create prefix function
    '''
    template/policy/list/prefix
    {
      "name": "test",
      "description": "Desc Not Required",
      "type": "prefix",
      "entries": [
        {
          "ipPrefix": "172.24.1.0/26"
        }
      ]
    }
    '''

    def hubAndSpoke_subDefinition(
            self,
            equalPreference=True,  # All hubs are equal (All Spokes Sites connect to all Hubs)
            advertiseTloc=False,  # Advertise Hub TLOCs
            name=None,  # used for definition and subDefinition names
            spokes=None,  # an unordered list of spokes
            hubs=None,  # an ordered list of hubs
            prefixLists=None,  # optional > an ordered list of lists containing prefixes for each hub
            uri_path="template/policy/definition/hubandspoke"
    ):

        assert isinstance(equalPreference, bool)
        assert isinstance(advertiseTloc, bool)
        assert isinstance(name, str)
        assert isinstance(spokes, list)
        assert isinstance(hubs, list)
        if prefixLists:
            assert isinstance(prefixLists, list)

        resp = self.get_request(uri_path)
        topologies = loads(resp)["data"]
        used_names = {topology["name"]: topology["owner"] for topology in topologies}
        if used_names.get(name):
            raise Exception("A topology with the name {} has already been created by {}".format(name, used_names[name]))

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
                raise Exception("hub not found:", hub)
        for spoke in spokes:
            if not site_list_names.get(spoke):
                raise Exception("spoke not found:", spoke)

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
            description="Created by viptilapyclient"  # optional description
    ):

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
                raise Exception("This topology type isn't supported yet, call harrison")
            uri_path = valid_topology_types[topology_type]["uri_path"]
        else:
            raise Exception("Valid topology_type values are {}".format([key for key in valid_topology_types]))

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
            raise Exception("vpn not found:", vpnList)

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
        return resp