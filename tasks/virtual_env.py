from tasks._constants import *


def create(c):
    """
    Create a python virtual env in path of config.
    """
    result = c.run(f'stat {c.config.data.env_path}', hide=True, warn=True)
    if result.ok:
        print(f'Virtualenv exists, skipping create.')
        return True

    print(f'{CYAN}Creating virtualenv...{COL_END}')
    c.run(f'{c.config.python_app} -m venv {c.config.data.env_path}')
    print(f'{GREEN}Created virtualenv at {c.config.data.env_path}{COL_END}')
    return True


def run(c, command, **kwargs):
    """
    Run a command in the virtual env.
    """
    kwargs.setdefault('echo', True)
    c.run(f'source {c.config.data.env_path}/bin/activate && {command}', **kwargs)


def pip(c, packages, **kwargs):
    """
    Install packages with pip in virtual env.
    """
    run(c, f'pip install {packages}', **kwargs)


def manage(c, command, **kwargs):
    """
    Run a Django management command in virtual env.
    """
    run(c, f'cd {c.config.data.src_path} && ./manage.py {command}', **kwargs)
