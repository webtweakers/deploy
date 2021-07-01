"""
Install and deploy projects on Opalstack (and others). Uses Fabric 2+.
See https://github.com/fabric/fabric
"""
from invoke import Collection
from fabric import task, Connection

from tasks._constants import *
from tasks import (control, server, user, application, python, supervisor,
                   virtual_env, project, database, redis, config)

DEFAULT_CONFIG = {
    'inline_ssh_env': True,
    'run': {
        'env': {
            'PATH': '$HOME/bin:$PATH',
        }
    },
    'project': {
        'name': 'project',
        'local': '.',
    },
    'data': {},
    'archive_excludes': ['__pycache__', '.DS_Store'],
}


def execute_tasks(c, tasks):
    # note: this seems silly, fabric has a tasks executor, but what about 'c'?
    # also: instead of 'return' (exit on error) use 'continue' (on error)? use command-arg?
    for t in tasks:
        try:
            print(f'\n------------------------------------------------------')
            print(f'{YELLOW}Executing {t.__module__}.{t.__name__}{COL_END}\n')
            result = t(c)
        except Exception as e:
            print(f'{RED}{e}{COL_END}')
            return
        else:
            if not result:
                return
            elif isinstance(result, Connection):
                c = result
    return c


def pretty_print(c):
    import json
    print(f'{GREEN}Successfully installed {c.config.project.name}!{COL_END}')
    print(f'--------------------------------------------')
    print(json.dumps(c.config.data._config, sort_keys=True, indent=4))
    print(f'--------------------------------------------')


@task
def env(c):
    # TODO: figure out how to pass arguments to this task
    #  to make it possible to get/set/del env vars on remote
    # list remote env vars
    c = user.update_ssh(c)
    application.get_info(c)
    config.env(c, 'list')


@task
def rollback(c):
    tasks = [
        # get fresh api token
        control.login,

        # plug into ssh config
        user.update_ssh,

        # gather redis info
        redis.find_bin,
        redis.get_id,
        redis.get_info,

        # gather main app info
        application.get_id,
        application.get_info,

        # restore project
        project.restore_db,
        project.restore_project,

        # update app config & restart
        supervisor.update_configs,
        supervisor.restart,
    ]

    execute_tasks(c, tasks)


@task
def deploy(c):
    tasks = [
        # get fresh api token
        control.login,

        # plug into ssh config
        user.update_ssh,

        # gather redis info
        redis.find_bin,
        redis.get_id,
        redis.get_info,

        # gather main app info
        application.get_id,
        application.get_info,

        # backup
        project.backup_db,
        project.backup_project,

        # update code / requirements / statics / db
        project.upload,
        project.install_requirements,
        project.update_static_files,
        project.migrate_db,

        # update app config & restart
        supervisor.update_configs,
        supervisor.restart,
    ]

    execute_tasks(c, tasks)


@task
def install(c):
    tasks = [
        # get fresh api token
        control.login,

        # info needed for creates
        server.get_id,

        # create user in control panel and new ssh config
        user.get_id,
        user.create,
        user.get_info,
        user.update_ssh,

        # install python
        python.install_bin,
        python.find_bin,

        # install redis and create redis app in control panel
        redis.install_bin,
        redis.find_bin,
        redis.get_id,
        redis.create,
        redis.get_info,

        # create main app in control panel
        application.get_id,
        application.create,
        application.get_info,

        # install env, project, requirements, files and db
        virtual_env.create,
        project.upload,
        project.install_requirements,
        project.update_static_files,

        # create database
        database.get_id,
        database.create,

        # skipping upload/restore of db - do this manually

        # install & start superuser
        supervisor.install_bin,
        supervisor.get_id,
        supervisor.create,
        supervisor.create_configs,
        supervisor.start,

        # TODO: create domain and site-routes
        # ...

        # print all retrieved info (db pass, etc)
        pretty_print,
    ]

    execute_tasks(c, tasks)


@task
def test(c):
    tasks = [
        control.login,
        user.update_ssh,
        application.get_id,
        application.get_info,
        virtual_env.create,
    ]

    execute_tasks(c, tasks)


# set default config (will be picked up by fabric/invoke)
ns = Collection(install, deploy, rollback, env, test)
ns.configure(DEFAULT_CONFIG)
