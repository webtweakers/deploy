from importlib import import_module

from ._constants import *


def login(c):
    """
    Login to Control Panel API, as defined in config.control.service.
    Assumes either a token or username and password to be defined in
    config.control. Store api ref in config.
    """
    service_name = c.config.control.service
    service = import_module(service_name)

    token = c.config.control.get('token')
    username = c.config.control.get('username')
    password = c.config.control.get('password')

    if token and not username and not password:
        print(f'{CYAN}Using provided API token.{COL_END}')
    else:
        print(f'{CYAN}Performing login with provided username and password...{COL_END}')

    try:
        api = service.API(token=token, username=username, password=password)
    except service.ApiException as e:
        print(f'{RED}{e}{COL_END}')
        return False

    c.config.control.api = api
    return True
