from distutils.version import StrictVersion

from ._util import (get_app_id, create_app, get_app_info,
                    pre_install_executable, download_executable, find_executable)
from ._constants import *


def get_id(c):
    """
    Find redis-app-id by project name. Add id to config.
    """
    if not c.config.project.dependencies.get('redis'):
        # nothing to do
        return True

    app_name = f'{c.config.project.name}_redis'
    app_id = get_app_id(c, app_name)
    if not isinstance(app_id, str):
        return app_id

    c.config.data.redis_app_id = app_id
    print(f'{GREEN}Found redis-app-id: {c.config.data.redis_app_id} for {app_name}{COL_END}')
    return True


def create(c):
    """
    Create redis app. Add id to config.
    """
    if not c.config.project.dependencies.get('redis'):
        # nothing to do
        return True

    app_name = f'{c.config.project.name}_redis'
    app_id = c.config.data.get('redis_app_id')
    c.config.data.redis_app_id = create_app(c, app_name, app_id)
    return True


def get_info(c):
    """
    Find redis app-info by redis-app-id. Add info to config.
    """
    if not c.config.project.dependencies.get('redis'):
        # nothing to do
        return True

    app_id = c.config.data.get('redis_app_id')
    c.config.data.redis_app_info = get_app_info(c, app_id)
    return True


def install_bin(c):
    raw_version = c.config.project.dependencies.get('redis')
    if not raw_version:
        # nothing to do
        return True

    requested_version = StrictVersion(str(raw_version))

    # check redis version (assuming cli has same version as server, easier to parse)
    app_name = f'redis-cli'
    cont = pre_install_executable(c, app_name, requested_version)
    if not cont:
        # stop install, continue on to next task
        return True

    base_name = f'redis-{raw_version}'
    file_name = f'{base_name}.tar.gz'
    file_url = f'http://download.redis.io/releases/{file_name}'
    cont = download_executable(c, file_name, file_url)
    if not cont:
        # bad install, quit
        return False

    # install redis
    install_path = f'$HOME/opt/redis-{raw_version}'
    print(f'{CYAN}Installing: {file_name} to {install_path}...{COL_END}')
    c.run('&&'.join([
        f'cd $HOME/src',
        f'tar zxf {file_name}']))
    c.run('&&'.join([
        f'export TMPDIR=$HOME/tmp',
        f'cd $HOME/src/{base_name}',
        f'make']))
    c.run(f'rm $HOME/src/{file_name}')

    # copy config (defaults are overridden on commandline)
    c.run(f'cp $HOME/src/{base_name}/redis.conf $HOME/etc/redis.conf')

    # create symlinks
    name = f'redis-cli'
    c.run(f'ln -sf $HOME/src/{base_name}/src/{name} ~/bin/{name}')
    name = f'redis-server'
    c.run(f'ln -sf $HOME/src/{base_name}/src/{name} ~/bin/{name}')

    print(f'{GREEN}Successfully installed Redis {requested_version}!')
    return True


def find_bin(c):
    """
    Find redis executables and save in config.
    :return: False on error, True on success
    """
    if not c.config.project.dependencies.get('redis'):
        # nothing to do
        return True

    print(f'{CYAN}Retrieving paths of redis-server and redis-cli...{COL_END}')

    redis_cli = find_executable(c, 'redis-cli')
    if not redis_cli:
        return False

    redis_server = find_executable(c, 'redis-server')
    if not redis_server:
        return False

    # save in config
    c.config.redis_cli = redis_cli
    c.config.redis_server = redis_server
    return True
