from ._constants import *


def get_id(c):
    """
    Find server-id by host name. Add id to config.
    """
    server = c.config.project.server
    print(f'{CYAN}Retrieving server-id for {server}...{COL_END}')
    response = c.config.control.api.get_servers()

    try:
        rec = next(x for x in response['web_servers'] if x['hostname'] == server)
    except StopIteration:
        print(f'{RED}No server-id found: server does not exist.{COL_END}')
        # this is a valid response:
        return True

    c.config.data.server_id = rec.get('id')
    print(f'{GREEN}Found server-id: {c.config.data.server_id} for {server}{COL_END}')
    return True
