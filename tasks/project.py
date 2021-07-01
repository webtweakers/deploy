from os.path import dirname

from . import virtual_env
from ._constants import *

# TODO: also backup/restore static files?


def backup_db(c):
    """
    Create a backup of the remote db.
    """
    db_type = c.config.project.get('database')
    if not db_type or db_type.lower() == 'none' or db_type.lower() == 'sqlite':
        # nothing to do
        return True

    print(f'{CYAN}Creating backup of remote database...{COL_END}')

    # create backup dir
    c.run(f'mkdir -p {c.config.data.backup_path}')

    file_name = f'{c.config.data.backup_path}/{c.config.project.name}.last.db'
    c.run(f'pg_dump -U {c.config.project.user} -Fc {c.config.project.name} > {file_name}', echo=True)
    return True


def restore_db(c):
    """
    Restore last version of remote db.
    """
    db_type = c.config.project.get('database')
    if not db_type or db_type.lower() == 'none' or db_type.lower() == 'sqlite':
        # nothing to do
        return True

    file_name = f'{c.config.data.backup_path}/{c.config.project.name}.last.db'
    result = c.run(f'stat {file_name}', hide=True)
    if not result.ok:
        print(f'{RED}Could not find database backup: {file_name}{COL_END}')
        return False

    c.run(f'pg_restore -U {c.config.project.user} -c --if-exists -d {c.config.project.name} {file_name}', echo=True)
    return True


def migrate_db(c):
    """
    Migrate database changes.
    """
    db_type = c.config.project.get('database')
    if not db_type or db_type.lower() == 'none':
        # nothing to do
        return True

    print(f'{CYAN}Migrating database...{COL_END}')
    virtual_env.manage(c, 'migrate --noinput')
    return True


def backup_project(c):
    """
    Backup remote project files.
    """
    print(f'{CYAN}Creating backup of remote project...{COL_END}')

    # create backup dir
    c.run(f'mkdir -p {c.config.data.backup_path}')

    file_name = f'{c.config.data.backup_path}/{c.config.project.name}.last.tar.gz'
    exclude_args = ' '.join(f"--exclude='{e}'" for e in c.config.archive_excludes)
    src_sub = c.config.data.src_path.split('/')[-1]
    c.run(f'cd {c.config.data.app_path} && tar -czf {file_name} {exclude_args} {src_sub}', echo=True)
    return True


def restore_project(c):
    """
    Restore latest version of project files.
    """
    file_name = f'{c.config.data.backup_path}/{c.config.project.name}.last.tar.gz'
    result = c.run(f'stat {file_name}', hide=True)
    if not result.ok:
        print(f'{RED}Could not find project backup: {file_name}{COL_END}')
        return False

    src_sub = c.config.data.src_path.split('/')[-1]
    c.run(f'cd {c.config.data.app_path} && tar -zxf {file_name} {src_sub}', echo=True)
    return True


def upload(c):
    """
    Upload project source files.
    Creates local tar, scp to remote, unzip on remote, cleanup.
    """
    env = {'PATH': '/usr/bin:/bin'}
    print(f'{CYAN}Uploading project {c.config.project.name}...{COL_END}')

    # local project path (location of fabric.yml file)
    fab_path = dirname(c.config._runtime_path)

    # create archive of source code
    file_name = f'{c.config.project.name}.tar.gz'
    exclude_args = ' '.join(f"--exclude='{e}'" for e in c.config.archive_excludes)
    c.local(f'cd {fab_path} && tar -czf /tmp/{file_name} {exclude_args} {c.config.project.source}', env=env)

    # upload archive to remote server
    c.local(f'scp /tmp/{file_name} {c.config.project.user}:{c.config.data.app_path}', pty=True, echo=True, env=env)
    c.local(f'rm /tmp/{file_name}', env=env)

    # extract archive to fresh source path
    src_dir = c.config.data.src_path.split('/')[-1]
    c.run(f'cd {c.config.data.app_path} && rm -rf {src_dir} && tar -zxf {file_name} && rm {file_name}')
    return True


def install_requirements(c):
    """
    Install project requirements.
    """
    print(f'{CYAN}Installing project requirements...{COL_END}')
    virtual_env.pip(c, f'--upgrade pip')
    # virtual_env.pip(c, f'--upgrade python-dotenv[cli]')
    virtual_env.pip(c, f'-r {c.config.data.src_path}/requirements.txt')
    return True


def update_static_files(c):
    """
    Collects and compresses static files.
    """
    print(f'{CYAN}Processing static files...{COL_END}')
    virtual_env.manage(c, 'collectstatic --noinput --verbosity 0', warn=True)

    # compress is a command from whitenoise, will be ignored if not used
    virtual_env.manage(c, 'compress --force', warn=True)
    return True
