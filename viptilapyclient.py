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
        """
        name:
            Expect a string, the name for this VPN

        entries:
            Expect a list of strings, each string should be the vpn_id

            To do: Get vpn list and site list first, check
        """

        if not name and not entries:
            raise Exception("Check params")
        if not isinstance(entries, list):
            raise Exception("Check params")

        req_payload = {
            "name": name,
            "description": "Desc Not Required",
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



    def create_policy_site_list(self, name=None, entries=None):

        req_payload = {
            "listId": None,
            "entries": [],
            "type": "site",
            "name": name,
            "description": "Created by Postman"
        }

        for site_list in entries:
            req_payload["entries"].append(
                {
                    "siteId": site_list
                }
            )

        response = self.post_request('template/policy/list/site', req_payload)
        return response


    def create_policy_topology_hub_and_spoke(self, vpnList=None, hubs=None, spokes=None):
        resp = self.get_request('template/policy/list/site')
        site_lists = loads(resp)["data"]
        site_list_names = {}
        for site_list in site_lists:
            name = site_list["name"]
            listId = site_list["listId"]
            site_list_names.setdefault(name, listId)
        for hub in hubs:
            if not site_list_names.get(hub):
                raise Exception("hub not found:", hub)
        for spoke in spokes:
            if not site_list_names.get(spoke):
                raise Exception("spoke not found:", spoke)

        resp = self.get_request('template/policy/list/vpn')
        vpn_lists = loads(resp)["data"]
        vpn_list_names = {}
        for vpn_list in vpn_lists:
            name = vpn_list["name"]
            listId = vpn_list["listId"]
            vpn_list_names.setdefault(name, listId)
        if not vpn_list_names.get(vpnList):
                raise Exception("vpn not found:", vpnList)

        return site_list_names, vpn_list_names



        '''
        req_payload = {
            "listId": None,
            "entries": [],
            "type": "hubAndSpoke",
            "name": name,
            "description": "Created by Postman"
        }

        for site_list in entries:
            req_payload["entries"].append(
                {
                    "siteId": site_list
                }
            )

        response = self.post_request('template/policy/definition/hubandspoke', req_payload)
        return response
        '''
