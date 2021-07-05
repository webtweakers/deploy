import os
import time
from textwrap import dedent

from invoke import Context
from fabric import Connection

from ._constants import *


def get_id(c):
    """
    Find user-id by name. Add id to config.
    """
    user_name = c.config.project.get('user')
    if not user_name:
        # nothing to do
        return True

    print(f'{CYAN}Retrieving user-id for {user_name}...{COL_END}')
    response = c.config.control.api.get_users()
    
    try:
        rec = next(x for x in response if x['name'] == user_name)
    except StopIteration:
        print(f'{YELLOW}No user-id found: user does not exist.{COL_END}')
        # this is a valid response:
        return True

    c.config.data.user_id = rec.get('id')
    print(f'{GREEN}Found user-id: {c.config.data.user_id}{COL_END}')
    return True


def create(c):
    """
    Create user. Requires server_id. Add id and password to config.
    On the server, this will create the root dir: /home/<user_name>
    """
    user_name = c.config.project.get('user')
    if not user_name:
        # nothing to do
        return True

    password = c.config.project.get('pass')

    if c.config.data.get('user_id'):
        print(f'User {user_name} exists, skipping create.')
        return True

    if not isinstance(c, Context):
        print(f'Was expecting invoke.Context, got something else.')
        return False

    print(f'{CYAN}Creating user {user_name}...{COL_END}')
    server_id = c.config.data.get('server_id')
    response = c.config.control.api.add_user(user_name, password, server_id)

    print(f'{GREEN}User {user_name} created!{COL_END}')
    c.config.data.user_id = response.get('id')
    c.config.data.user_password = response.get('default_password')
    return True


def get_info(c):
    """
    Find user-info by user-id. Add info to config.
    """
    user_name = c.config.project.get('user')
    if not user_name:
        # nothing to do
        return True

    user_id = c.config.data.get('user_id')

    # wait for user to be created
    response = None
    attempts = 5
    while attempts > 0:
        response = c.config.control.api.get_user_info(user_id)
        if response.get('ready'):
            break

        print(f'Waiting 5 seconds for user to be created...')
        time.sleep(5)
        attempts -= 1

    if not response.get('ready'):
        print(f'{RED}User {user_name} was not created ok: check control panel!{COL_END}')
        return False

    c.config.data.user_info = response
    return True


def update_ssh(c):
    """
    Update SSH config, if needed, and start using it!
    """
    env = {'PATH': '/usr/bin:/bin'}
    user_name = c.config.project.user

    # NOTE: no connection set yet, so the c.run statements below are executed on LOCAL!!!

    result = c.run(f'grep -ic {user_name} ~/.ssh/config', env=env, hide=True, warn=True)
    if int(result.stdout) == 0:

        # no ssh config found for user
        print(f'{CYAN}Creating ssh keys for {user_name}...{COL_END}')
        print('You will be asked for a passphrase')
        c.run(f'ssh-keygen -q -t rsa -b 4096 -f ~/.ssh/{user_name}', env=env)

        server = c.config.project.server
        password = c.config.data.get('user_password')
        msg = f'Copying public key to server.'
        if password:
            msg += f' When asked for a password, enter: {GREEN}{password}{COL_END}'
        else:
            # Opalstack control panel: https://my.opalstack.com/notices/
            msg += f' Find password for {user_name} in control panel'
        print(msg)
        c.run(f'ssh-copy-id -i ~/.ssh/{user_name} {user_name}@{server}', env=env)

        print('Updating ssh_config')
        cfg = dedent(f"""
            Host {user_name}
              IdentityFile ~/.ssh/{user_name}
              User {user_name}
              Hostname {server}
        """)

        with open(os.path.expanduser('~/.ssh/config'), 'a+') as f:
            f.write(cfg)

        # TODO: make ssh aware of new config (next runs work, with fresh ssh)
        # TODO: also, if you get weird errors, maybe try chmod 640 ~/.ssh/authorized_keys on server

    # re-create connection with user (after this c.run will be executed on REMOTE!)
    print(f'{GREEN}Updating connection with {user_name}!{COL_END}')
    c = Connection(user_name, config=c.config)
    return c
