from ._util import get_app_id, create_app, get_app_info
from ._constants import *


def get_id(c):
    """
    Find app-id by project name. Add id to config.
    """
    app_name = c.config.project.name
    app_id = get_app_id(c, app_name)
    if not isinstance(app_id, str):
        return app_id

    c.config.data.app_id = app_id
    print(f'{GREEN}Found app-id: {c.config.data.app_id} for {app_name}{COL_END}')
    return True


def create(c):
    """
    Create main project app by name. Add id to config.
    """
    app_name = c.config.project.name
    app_id = c.config.data.get('app_id')
    c.config.data.app_id = create_app(c, app_name, app_id)
    # TODO: create 'tmp' dir in app dir
    return True


def get_info(c):
    """
    Find main project app-info by app-id. Add info + project paths to config.
    """
    app_id = c.config.data.get('app_id')
    if app_id:
        c.config.data.app_info = get_app_info(c, app_id)

    c.config.data.app_path = f'/home/{c.config.project.user}/apps/{c.config.project.name}'.lower()
    c.config.data.log_path = f'/home/{c.config.project.user}/logs/apps/{c.config.project.name}'.lower()
    c.config.data.src_path = f'{c.config.data.app_path}/app'  # must be sub of app_path
    c.config.data.env_path = f'{c.config.data.app_path}/env'
    c.config.data.backup_path = f'{c.config.data.app_path}/backup'
    return True
