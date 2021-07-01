import dotenv

from . import virtual_env


def env(c, action='list', key=None, value=None):
    """
    Manage project configuration via .env

    e.g: fab config:set,<key>,<value>
         fab config:get,<key>
         fab config:unset,<key>
         fab config:list

    Unfortunately this notation does not work in Fabric 2.
    See: https://github.com/theskumar/python-dotenv

    For now, only list command works (hardcoded).
    """
    dotenv_path = f'{c.config.data.src_path}/.env'
    c.run(f'touch {dotenv_path}')
    command = dotenv.get_cli_string(dotenv_path, action, key, value)
    virtual_env.run(c, command)
