import json
import requests
import flask

import logging

from pymessenger.utils import AttrsEncoder

logger = logging.getLogger(__name__)

class Bot(object):
    def __init__(self,
                 api_username,
                 api_password):
        """
            @required:
                api_username
                api_password
        """
        self.api_username = api_username
        self.api_password = api_password
        self.access_token = self.login(api_username, api_password)

        logger.info("__init__ -> access_token:" , self.access_token)


    @property
    def auth_args(self):
        if not hasattr(self, '_auth_args'):
            auth = 'Bearer ' + self.access_token.get('jwt')
            self._auth_args = auth
        return self._auth_args

    def send_raw(self, payload):
        request_endpoint = 'https://api.h3rmes.com/api/v1/messages'
        response = requests.post(
            request_endpoint,
            data=json.dumps(payload, cls=AttrsEncoder),
            headers={'Content-Type': 'application/json',
                     'Authorization': self.auth_args})
        result = flask.jsonify(response.json())

        return result

    def login(self, api_username, api_password):
        payload = json.loads('{}')
        payload.update({"username": api_username,
                        "password": api_password
                        })
        request_endpoint = 'https://api.h3rmes.com/api/v1/users/sign_in'
        response = requests.post(
            request_endpoint,
            data=json.dumps(payload, cls=AttrsEncoder),
            headers={'Content-Type': 'application/json'})
        result = response.json()

        logger.debug("login -> result:", result)

        return result


    def create_hsm(self, hsm_name, hsm_message):
        return hsm_message