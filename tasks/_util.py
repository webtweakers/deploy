import time
from distutils.version import StrictVersion

from ._constants import *


def find_executable(c, executable):
    """
    Find full path of given executable file.
    :return: Path or False when not found
    """
    result = c.run(f'command -v {executable}', hide=True, warn=True)
    if result.stderr:
        print(f'{RED}Could not find {executable}{COL_END}')
        return False

    app = result.stdout.strip()
    if not app:
        print(f'{RED}No path found for {executable}{COL_END}')
        return False

    print(f'{GREEN}Found {app}{COL_END}')
    return app


def pre_install_executable(c, executable, version):
    """
    Perform pre-installation checks for executables.

    :param c:
    :param executable: File name of executable
    :param version: Requested version
    :return: False if installer should stop, True when it should continue installation
    """
    installed_version = None
    result = c.run(f'{executable} --version', warn=True, hide=True)
    if result.stdout:
        _, result_version = result.stdout.strip().split(' ')
        installed_version = StrictVersion(result_version)

        # nothing to install
        if version <= installed_version:
            print(f'{GREEN}{executable} ({version}) install found: {installed_version}{COL_END}')
            return False

    # create build dirs
    c.run('mkdir -p ~/{bin,opt,src,tmp,etc}')

    if installed_version:
        print(f'Server has python version {installed_version}. ')

    # continue installation
    return True


def download_executable(c, file_name, url):
    """
    Download an archive/executable to the ~/src dir.
    :return: False if installer should stop, True when it should continue installation
    """
    print(f'{CYAN}Downloading {url}...{COL_END}')
    c.run(f'wget -O ~/src/{file_name} {url}', pty=True)

    # check download
    result = c.run(f'stat ~/src/{file_name}', hide=True)
    if not result.ok:
        print(f'{RED}Could not find {file_name} on python.org!{COL_END}')
        # stop install
        return False

    # continue installation
    return True


def get_app_id(c, app_name):
    """
    Retrieve app-id for a given app name (in full). Called from get_id, not for use as sub-task.
    :return: False on error, True on not found (continue), or string with app uuid
    """
    print(f'{CYAN}Retrieving app-id for {app_name}...{COL_END}')
    response = c.config.control.api.get_apps()

    try:
        rec = next(x for x in response if x['name'] == app_name)
    except StopIteration:
        print(f'{YELLOW}No app-id found: app does not exist.{COL_END}')
        # this is a valid response:
        return True

    return rec['id']


def create_app(c, app_name, app_id=None):
    """
    Create proxy app in Control Panel. This will also create the project.app_path on the server.
    Requires user_id. Receives app-id on creation, which is returned.
    """
    if app_id:
        print(f'App {app_name} exists, skipping create.')
        return app_id

    app_type = 'CUS'
    user_id = c.config.data.get('user_id')
    if not user_id:
        print(f'{RED}user-id is required to create an app.{COL_END}')
        return False

    print(f'{CYAN}Creating app {app_name}...{COL_END}')
    response = c.config.control.api.add_app(app_type, app_name, user_id)

    print(f'{GREEN}App {app_name} created!{COL_END}')
    return response['id']


def get_app_info(c, app_id):
    """
    Find app-info by app-id (mainly to get the port number).
    """
    if not app_id:
        print(f'{RED}Did not get an app-id to get info for.{COL_END}')
        return False

    print(f'{CYAN}Retrieving app info for id {app_id}...{COL_END}')

    response = None
    attempts = 5
    while attempts > 0:
        response = c.config.control.api.get_app_info(app_id)
        if response.get('ready'):
            break

        print(f'Waiting 5 seconds for app to be created...')
        time.sleep(5)
        attempts -= 1

    app_name = response['name']
    if not response.get('ready'):
        print(f'{RED}App {app_name} is not installed ok: check control panel!{COL_END}')
        return False

    app_type = response['type']
    if app_type != 'CUS':
        print(f'{RED}App {app_name} is of wrong type: {app_type}!{COL_END}')
        return False

    msg = 'Found app {name} for user {osuser} at port {port}.'.format(**response)
    print(f'{GREEN}{msg}{COL_END}')
    return response
