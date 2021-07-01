import time

from ._constants import *


def get_id(c):
    """
    Retrieve id of configured database. Store in config.
    """
    db_type = c.config.project.get('database')
    if not db_type or db_type.lower() == 'none' or db_type.lower() == 'sqlite':
        # nothing to do
        return True

    db_name = c.config.project.name
    print(f'{CYAN}Retrieving db-id for {db_name}...{COL_END}')

    if db_type == 'postgres':
        key = 'psqldbs'
        response = c.config.control.api.get_psqls()

    elif db_type == 'mariadb':
        key = 'mariadbs'
        response = c.config.control.api.get_mariadbs()

    else:
        print(f'{RED}Unknown database type: {db_type}.{COL_END}')
        return False

    try:
        rec = next(x for x in response[key] if x['name'] == db_name)
    except StopIteration:
        print(f'{YELLOW}No db-id found: {db_type} db {db_name} does not exist.{COL_END}')
        # this is a valid response:
        return True

    db_id = rec['id']
    if not isinstance(db_id, str):
        return db_id

    c.config.data.db_id = db_id
    print(f'{GREEN}Found db-id: {c.config.data.db_id} for {db_name}{COL_END}')
    return True


def create(c):
    """
    Create database in control panel. DB user of same name will be created automatically.
    """
    # get db type
    db_type = c.config.project.get('database')
    if not db_type or db_type.lower() == 'none':
        return True

    # verify db type
    if db_type in ['sqlite']:
        print(f'{GREEN}Skipping database install for {db_type}.{COL_END}')
        return True

    if db_type not in ['postgres', 'mariadb']:
        print(f'{RED}Unknown database type: {db_type}.{COL_END}')
        return False

    # quick check existence
    db_name = c.config.project.name
    db_id = c.config.data.get('db_id')
    if db_id:
        print(f'Database {db_name} exists, skipping create.')
        return db_id

    # create database
    print(f'{CYAN}Creating {db_type} database {db_name}...{COL_END}')
    charset = 'utf8'  # hardcoded for simplicity
    server_id = c.config.data.get('server_id')
    if db_type == 'postgres':
        response = c.config.control.api.add_postgres(db_name, server_id, charset)
    else:
        response = c.config.control.api.add_mariadb(db_name, server_id, charset)

    db_id = response.get('id')
    db_user_name = response.get('dbuser')
    db_user_id = response.get('dbuserid')
    c.config.data.db_info = response

    # wait for db to be created
    response = None
    attempts = 5
    while attempts > 0:
        if db_type == 'postgres':
            response = c.config.control.api.get_psql_info(db_id)
        else:
            response = c.config.control.api.get_mariadb_info(db_id)

        if response.get('ready'):
            break

        print(f'Waiting 5 seconds for db to be created...')
        time.sleep(5)
        attempts -= 1

    if not response.get('ready'):
        print(f'{RED}{db_type} database {db_name} is not installed ok: check control panel!{COL_END}')
        return False

    # wait for db-user to be created
    response = None
    attempts = 5
    while attempts > 0:
        if db_type == 'postgres':
            response = c.config.control.api.get_psql_userinfo(db_user_id)
        else:
            response = c.config.control.api.get_mariadb_userinfo(db_user_id)

        if response.get('ready'):
            break

        print(f'Waiting 5 seconds for db user to be created...')
        time.sleep(5)
        attempts -= 1

    if not response.get('ready'):
        print(f'{RED}database user {db_user_name} is not installed ok: check control panel!{COL_END}')
        return False

    print(f'{GREEN}{db_type} database {db_name} and user {db_user_name} created!{COL_END}')
    return True
