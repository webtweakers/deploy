from distutils.version import StrictVersion

from ._constants import *
from ._util import find_executable, pre_install_executable, download_executable

DEFAULT_PYTHON = '3.6'


def install_bin(c):
    """
    Verify if requested python is installed on server, either in system or custom.
    If not found, install requested python version and create symlinks in ~/bin.
    :return: False on error, True on success
    """
    raw_version = str(c.config.project.dependencies.get('python', DEFAULT_PYTHON))
    requested_version = StrictVersion(raw_version)

    # search python
    maj_version = requested_version.version[0]
    min_version = requested_version.version[1]
    app_name = f'python{maj_version}.{min_version}'
    cont = pre_install_executable(c, app_name, requested_version)
    if not cont:
        # stop install, continue on to next task
        return True

    # download python
    base_name = f'Python-{raw_version}'
    file_name = f'{base_name}.tgz'
    file_url = f'https://www.python.org/ftp/python/{raw_version}/{file_name}'
    cont = download_executable(c, file_name, file_url)
    if not cont:
        # bad download, quit
        return False

    # install python
    install_path = f'$HOME/opt/python-{raw_version}'
    print(f'{CYAN}Installing: {file_name} to {install_path}...{COL_END}')
    c.run('&&'.join([
        f'cd $HOME/src',
        f'tar zxf {file_name}']))
    c.run('&&'.join([
        f'export TMPDIR=$HOME/tmp',
        f'cd $HOME/src/{base_name}',
        f'./configure --prefix={install_path}',
        f'make && make install']))
    c.run(f'rm $HOME/src/{file_name}')

    # create symlinks
    name = f'python{maj_version}.{min_version}'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')
    name = f'python{maj_version}'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')

    name = f'pip{maj_version}.{min_version}'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')
    name = f'pip{maj_version}'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')

    print(f'{GREEN}Successfully installed Python {requested_version}!')
    return True


def find_bin(c):
    """
    Find requested python & pip executables and save in config.
    :return: False on error, True on success
    """
    requested_version = StrictVersion(str(c.config.project.dependencies.get('python', DEFAULT_PYTHON)))
    maj_version = requested_version.version[0]
    min_version = requested_version.version[1]

    print(f'{CYAN}Retrieving paths of python and pip...{COL_END}')

    python_app = find_executable(c, f'python{maj_version}.{min_version}')
    if not python_app:
        return False

    pip_app = find_executable(c, f'pip{maj_version}.{min_version}')
    if not pip_app:
        return False

    # save in config
    c.config.python_app = python_app
    c.config.pip_app = pip_app
    return True
