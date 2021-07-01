import requests

API_HOST = 'my.opalstack.com'
API_BASE_URI = '/api/v1'

__all__ = ['API', 'ApiException']


class API:

    def __init__(self, token=None, username=None, password=None):
        if token is None and username is None:
            raise ApiException('Provide one of token or username/password.')

        if not token and username and password:
            result = self.login(username, password, headers={'Content-type': 'application/json'})
            if not result.get('token'):
                raise ApiException('Invalid username and password provided.')
            token = result['token']

        self.headers = {
            'Content-type': 'application/json',
            'Authorization': f'Token {token}'
        }

    def request(self, method_name, method='get', json=None, headers=None):
        """
        Makes a request to the Opalstack API.
        :param method_name: Name of the API method to be called. (E.g. '/app/add/')
        :param method: HTTP method to be used. Defaults to 'get'.
        :param json: (optional) A JSON serializable object to send in the body of the request.
        :param headers: (optional) Custom headers for this request
        :return: The result parsed to a JSON dictionary.
        """
        url = f'https://{API_HOST}{API_BASE_URI}{method_name}'
        headers = headers or self.headers
        response = requests.request(method, url, json=json, headers=headers)
        return self._check_response(method_name, response)

    def _check_response(self, method_name, response):
        """
        Checks whether `result` is a valid API response.
        A result is considered invalid if:
            - The server returned an HTTP response code other than 200
            - The content of the result is invalid JSON.
            - The method call was unsuccessful (The JSON 'ok' field equals False)

        :raises ApiException: if one of the above listed cases is applicable
        :param method_name: The name of the method called
        :param response: The returned response of the method request
        :return: The result parsed to a JSON dictionary.
        """
        if response.status_code and not 200 <= response.status_code < 300:
            msg = 'The server returned HTTP {0}: {1}.\nResponse body: {2}' \
                .format(response.status_code, response.reason, response.text.encode('utf8'))
            raise ApiException(msg, method_name, response)

        try:
            result_json = response.json()
        except Exception:
            msg = 'The server returned an invalid JSON response.\nResponse body: {0}' \
                .format(response.text.encode('utf8'))
            raise ApiException(msg, method_name, response)

        # Opalstack does not return a status in the json, yet...
        # if not result_json['ok']:
        #     msg = 'Error code: {0} Description: {1}' \
        #         .format(result_json['error_code'], result_json['description'])
        #     raise ApiException(msg, method_name, result)
        return result_json

    def login(self, username, password, headers=None):
        method_url = '/login/'
        payload = {'username': username, 'password': password}
        return self.request(method_url, json=payload, method='post', headers=headers)

    def get_users(self):
        """
        Get list of users.
        :return: API Response:
            {
                "users": [
                    {
                        "id": "01234567-89ab-cdef-0123-456789abcdef",
                        "name": "username1",
                        "server": "01234567-89ab-cdef-0123-456789abcdef",
                        "state": "READY",
                        "ready": true,
                    },
                    ...
                ]
            }
        """
        method_url = '/osuser/list/'
        return self.request(method_url)

    def get_user_info(self, user_id):
        """
        Get info for a user.
        :param user_id: The UUID of the user
        :return: API Response:
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "name": "username1",
                "server": "01234567-89ab-cdef-0123-456789abcdef",
                "state": "READY",
                "ready": true
            }
        """
        method_url = f'/osuser/read/{user_id}'
        return self.request(method_url)

    def add_user(self, user_name, password, server_id):
        """
        Add a user.
        :param user_name: Name of user
        :param password: Password for user
        :param server_id: UUID of server to create user
        :return: API Response:
            {
                'name': 'test_user1',
                'server': '01234567-89ab-cdef-0123-456789abcdef',
                'id': '01234567-89ab-cdef-0123-456789abcdef',
                'default_password': 'password1'
            }
        """
        method_url = '/osuser/create/'
        payload = [{'json': {}, 'name': user_name, 'password': password, 'server': server_id}]
        return self.request(method_url, json=payload, method='post')

    def get_servers(self):
        """
        Get list of servers.
        :return: API Response:
            {
                "web_servers": [
                    {
                        "id": "01234567-89ab-cdef-0123-456789abcdef",
                        "hostname": "opal1.opalstack.com"
                    }
                ],
                "imap_servers": [
                    ...
                ],
                "smtp_servers": [
                    ...
                ]
            }
        """

        method_url = '/server/list/'
        return self.request(method_url)

    def get_apps(self):
        """
        Retrieve list of apps.
        :return: API Response:
            [
                {
                    "id": "01234567-89ab-cdef-0123-456789abcdef",
                    "name": "application1"
                    "state": "READY",
                    "ready": true,
                    "server": "01234567-89ab-cdef-0123-456789abcdef",
                    "osuser": "01234567-89ab-cdef-0123-456789abcdef",
                    "type": "CUS",
                    "port": 12345,
                    "installer_url": null,
                    "json": {},
                    "osuser_name": "example"
                },
                ...
            ]

        """
        method_url = '/app/list/'
        return self.request(method_url)

    def get_app_info(self, app_id):
        """
        Get info of an app.
        :param app_id: UUID of the app
        :return: API Response:
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "state": "READY",
                "ready": true,
                "name": "application1",
                "server": "01234567-89ab-cdef-0123-456789abcdef",
                "osuser": "01234567-89ab-cdef-0123-456789abcdef",
                "type": "CUS",
                "port": 12345,
                "installer_url": null,
                "json": {},
                "osuser_name": "example"
            }
        """
        method_url = f'/app/read/{app_id}'
        return self.request(method_url)

    def add_app(self, app_type, app_name, user_id):
        """
        Create a new app.
        :param app_type: Type of app, use "CUS" for custom app.
            Possible values: STA, NPF, APA, CUS, SLS, SLP, SVN, DAV.
        :param app_name: Name of app
        :param user_id: UUID of app user
        :return: API Response:
            {
                'id': '01234567-89ab-cdef-0123-456789abcdef',
                'name': 'application1',
                'server': '01234567-89ab-cdef-0123-456789abcdef',
                'json': {},
                'type': 'CUS',
                'installer_url': None
            }
        """
        method_url = '/app/create/'
        payload = [{'json': {}, 'type': app_type, 'name': app_name,
                   'osuser': user_id}]
        return self.request(method_url, json=payload, method='post')

    def get_psqls(self):
        """
        Get list of postgres databases.
        :return: API Response:
            [
                {
                    "id": "01234567-89ab-cdef-0123-456789abcdef",
                    "name": "dbname1"
                    "state": "READY",
                    "ready": true,
                    "server": "01234567-89ab-cdef-0123-456789abcdef",
                    "charset": "utf8",
                    "dbusers_readwrite": [
                      "01234567-89ab-cdef-0123-456789abcdef"
                    ],
                    "dbusers_readonly": []
                },
                ...
            ]
        """
        method_url = '/psqldb/list/'
        return self.request(method_url)

    def get_psql_info(self, db_id):
        """
        Get info for a postgres database.
        :param db_id: UUID of the database
        :return: API Response:
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "name": "example",
                "state": "READY",
                "ready": true,
                "server": "01234567-89ab-cdef-0123-456789abcdef",
                "charset": "utf8",
                "dbusers_readwrite": [
                    "01234567-89ab-cdef-0123-456789abcdef"
                ],
                "dbusers_readonly": []
            }
        """
        method_url = f'/psqldb/read/{db_id}'
        return self.request(method_url)

    def get_psql_userinfo(self, db_user_id):
        """
        Get info for a postgres user.
        :param db_user_id:
        :return: API Response:
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "state": "READY",
                "ready": true,
                "name": "example",
                "server": "01234567-89ab-cdef-0123-456789abcdef",
                "external": false
            }
        """
        method_url = f'/psqluser/read/{db_user_id}'
        return self.request(method_url)

    def get_mariadbs(self):
        """
        Get list of maria databases.
        :return: API Response:
            {
                "mariadbs": [
                    {
                        "id": "01234567-89ab-cdef-0123-456789abcdef",
                        "name": "dbname1",
                        ...
                    },
                    ...
                ]
            }
        """
        method_url = '/mariadb/list/'
        return self.request(method_url)

    def get_mariadb_info(self, db_id):
        method_url = f'/mariadb/read/{db_id}'
        return self.request(method_url)

    def get_mariadb_userinfo(self, db_user_id):
        method_url = f'/mariauser/read/{db_user_id}'
        return self.request(method_url)

    def add_postgres(self, name, server_id, charset='utf8'):
        """
        Create a postgres database.
        :param name: Name of the database
        :param server_id: UUID of server to create db
        :param charset: Default: utf8, possible values: utf8, latin1, etc...
        :return: API Response:
            ...
        """
        method_url = '/psqldb/create/'
        payload = [{'name': name, 'server': server_id, 'charset': charset}]
        return self.request(method_url, json=payload, method='post')

    def add_mariadb(self, name, server_id, charset):
        """
        Create a maria database.
        :param name: Name of the database
        :param server_id: UUID of server to create db
        :param charset: Charset
        :return: API Response:
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "name": "database1",
                "server": "opal1.opalstack.com",
                "installed_ok": true,
                "charset": "utf8",
                "owner": "dbuser1"
            }
        """
        method_url = '/mariadb/create/'
        # untested payload...
        payload = [{'name': name, 'server': server_id, 'charset': charset}]
        return self.request(method_url, json=payload, method='post')


class ApiException(Exception):
    """
    This class represents an Exception thrown when a call to the Opalstack API fails.
    In addition to an informative message, it has a `function_name` and a `response`
    attribute, which respectively contain the name of the failed function and the
    returned response that made the function to be considered as failed.
    """
    def __init__(self, msg, function_name=None, response=None):
        msg = "A request to the Opalstack API was unsuccessful. {0}".format(msg)
        super(ApiException, self).__init__(msg)
        self.function_name = function_name
        self.response = response
