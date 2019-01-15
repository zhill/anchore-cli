import json
import re
import requests
import hashlib
import logging
import urllib3
import uuid
import requests.packages.urllib3
try:
    from urllib.parse import urlparse, urlunparse, urlencode
except:
    from urllib import urlencode
    from urlparse import urlparse,urlunparse

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import anchorecli.clients.common

_logger = logging.getLogger(__name__)

def _get_hub_index(base_url=None, auth=(None, None)):
    index = {}
    url = "{}/index.json".format(base_url)
    try:
        r = requests.get(url, auth=auth)
        if r.status_code not in range(200, 299):
            raise Exception("Could not fetch index from {} - server responded with {}".format(url, r))
        else:
            index = r.json()
    except Exception as err:
        raise err
    return(index)

def get_policies(config):
    ret = {
        'success': False,
        'payload': {},
        'httpcode': 500,
    }

    hub_base_url = config['hub-url']

    try:
        index = _get_hub_index(base_url=hub_base_url)
        ret['success'] = True
        ret['payload'] = index
        ret['httpcode'] = 200
    except Exception as err:
        ret['success'] = False
        ret['error'] = str(err)

    return(ret)

def install_policy(config, bundlename, target_id=None, force=False, auth=(None, None)):
    ret = {
        'success': False,
        'payload': {},
        'httpcode': 500,
    }

    try:
        ret = anchorecli.clients.hub.get_policies(config)
        if ret['success']:
            index = ret['payload']
        else:
            raise Exception(ret['error'])

        url = None
        for record in index['content']:
            if record['type'] == 'bundle' and record['name'] == bundlename:
                url = record['location']

        if not url:
            raise Exception("Bundle name {} not found in index".format(bundlename))

        bundle = None
        r = requests.get(url, auth=auth)
        if r.status_code not in range(200, 299):
            raise Exception("Could not fetch index from {} - server responded with {}".format(url, r))
        else:
            bundle = r.json()
            if target_id:
                bundleid = target_id
            else:
                bundleid = bundle['name']
            bundle['id'] = bundleid

        if not force:
            ret = anchorecli.clients.apiexternal.get_policies(config)
            if ret['success']:
                for installed_policy in ret['payload']:
                    if installed_policy['policyId'] == bundleid:
                        raise Exception("Policy with ID ({}) already installed - use force to override or specify target unique ID".format(bundleid))

        ret = anchorecli.clients.apiexternal.add_policy(config, policybundle=bundle, detail=True)

    except Exception as err:
        ret['success'] = False
        ret['error'] = str(err)

    return(ret)