import json
import logging
from http.client import responses as http_responses
from typing import Dict, Union
from urllib.parse import urlencode

import requests
import urllib3
from packaging import version
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AFA:

    """API Connection object used to interact with AlgoSec Firewall Analyzer REST API"""

    def __init__(self, hostname: str, username: str, password: str, protocol='https', verify_cert=False, timeout=120):
        """Initialize connection object. It is highly recommended to use a
        dedicated user for api operations

        :param hostname: ip address or fqdn of algosec firewall analyzer
        :type hostname: str
        :param username: username used for api authentication
        :type username: str
        :param password: password used for api authentication
        :type password: str
        :param protocol: protocol used to access fmc rest api. Defaults to `https`
        :type protocol: str, optional
        :param verify_cert: check https certificate for validity. Defaults to `False`
        :type verify_cert: bool, optional
        :param timeout: timeout value for http requests. Defaults to `120` seconds
        :type timeout: int, optional
        """
        if not verify_cert:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.headers = {'User-Agent': 'AlgoREST'}
        self.hostname = hostname
        self.protocol = protocol
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.timeout = timeout
        self.verify_cert = verify_cert
        self.login()

    def _request(self, method: str, url: str, params=None, auth=None, data=None):
        """Base operation used for all http api calls

        :param method: http operation (post, get, put, delete)
        :type method: str
        :param url: url to api resource
        :type url: str
        :param params: additional http params that should be passed to the request
        :type params: dict, optional
        :param auth: credentials in base64 format
        :type auth: HTTPBasicAuth, optional
        :param data: request body (api payload)
        :type data: dict, optional
        :return: api response
        :rtype: requests.Response
        """
        if not params:
            params = {}
        if self.token:
            params['session'] = self.token

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=json.dumps(data),
            auth=auth,
            headers=self.headers,
            timeout=self.timeout,
            verify=self.verify_cert,
        )
        msg = {
            'method': method.upper(),
            'url': url,
            'params': urlencode(params) if params else '',
            'data': data if data else '',
            'status': f'{http_responses[response.status_code]} ({response.status_code})',
        }
        if response.status_code >= 400:
            logger.error('\n%s', json.dumps(msg, indent=4))
        else:
            logger.info('\n%s', json.dumps(msg, indent=4))
            try:
                logger.debug('\n"response": %s', json.dumps(response.json(), sort_keys=True, indent=4))
            except json.JSONDecodeError:
                pass

        return response

    def get(self, url: str, params=None, _items=None):
        """GET operation

        :param url: path to resource that will be queried
        :type url: str
        :param params: dict of parameters for http request. Defaults to `None`
        :type params: dict, optional
        :param _items: list of items if response includes multiple pages. Used internally for recursion
        :type _items: list, optional
        :return: dictionary or list of returned api objects
        :rtype: Union[dict, list]
        """

        response = self._request('get', url, params=params)
        return response.json()

    def delete(self, url: str, params=None):
        """DELETE specified api resource

        :param url: path to resource that will be deleted
        :type url: str
        :param params: dict of parameters for http request
        :type params: dict, optional
        :return: api response
        :rtype: requests.Response
        """
        return self._request('delete', url, params=params)

    def post(self, url: str, data: Dict, params=None, ignore_fields=None):
        """POST operation that is mostly used to create new resources or trigger tasks

        :param url: path to resource on which POST operation will be performed
        :type url: str
        :param data: data that will be sent to the api endpoint
        :type data: Union[list, dict], optional
        :param params: dict of parameters for http request
        :type params: dict, optional
        :param ignore_fields: list of fields that should be stripped from payload before performing operation
        :type ignore_fields: list, optional
        :return: requests.response object
        """
        return self._request('post', url, params=params, data=data)

    def put(self, url: str, data: Dict, params=None, ignore_fields=None):
        """PUT operation that updates existing resources according to the payload provided

        :param url: path to resource on which POST operation will be performed
        :type url: str
        :param data: data that will be sent to the api endpoint
        :type data: Union[list, dict], optional
        :param params: dict of parameters for http request
        :type params: dict, optional
        :param ignore_fields: list of fields that should be stripped from payload before performing operation
        :type ignore_fields: list, optional
        :return: api response
        :rtype: requests.Response
        """
        return self._request('put', url, data=data, params=params)

    def login(self):
        """Basic authentication to algosec rest api
        """
        logger.info('Attempting authentication with AlgoSec Appliance (%s)', self.hostname)
        url = f'{self.protocol}://{self.hostname}/fa/server/connection/login'
        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'username': self.username, 'password': self.password}
        self.token = self.session.request(
            method='post', url=url, data=data, headers=headers, timeout=self.timeout, verify=self.verify_cert
        ).json()['SessionID']

    def get_risky_rules(self, device: str):
        """Get risky rules of latest risk report in json format
        """
        url = f'https://{self.hostname}/fa/server/risks/riskyRules'
        params = {'entity': device, 'entityType': 'device', 'responseType': 'json'}
        return self.get(url=url, params=params)
