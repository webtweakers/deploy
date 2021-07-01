import io
import configparser

from ._util import create_app, get_app_id, find_executable
from ._constants import *

# APP_NAME = 'supervisor'


def install_bin(c):
    """
    Install supervisor in ~/bin through account-wide pip (outside virtual env!)
    """
    if not c.config.project.get('supervisor'):
        # nothing to do
        return True

    # check install of supervisor
    # result = c.run(f'[ -f $HOME/bin/supervisorctl ] && echo 1 || echo 0', hide=True)
    # if int(result.stdout):
    #
    #     # nothing to install
    #     print(f'{GREEN}Supervisor found, skipping install.{COL_END}')
    #     return True

    if find_executable(c, 'supervisord'):

        # nothing to install
        print(f'{GREEN}Supervisor found, skipping install.{COL_END}')
        return True

    print(f'{CYAN}Installing supervisor...{COL_END}')
    c.run(f'{c.config.pip_app} install -U supervisor', echo=True)

    raw_version = str(c.config.project.dependencies.get('python'))
    install_path = f'$HOME/opt/python-{raw_version}'

    # create symlinks
    name = f'supervisorctl'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')
    name = f'supervisord'
    c.run(f'ln -sf {install_path}/bin/{name} ~/bin/{name}')

    print(f'{GREEN}Successfully installed Supervisor!{COL_END}')
    return True


def get_id(c):
    """
    Find app-id by project name. Add id to config.
    """
    if not c.config.project.get('supervisor'):
        # nothing to do
        return True

    app_name = f'{c.config.project.user}_supervisor'
    app_id = get_app_id(c, app_name)
    if not isinstance(app_id, str):
        return app_id

    c.config.data.supervisor_app_id = app_id
    print(f'{GREEN}Found supervisor-app-id: {app_id} for {app_name}{COL_END}')
    return True


def create(c):
    """
    Create main project app by name. Add id to config.
    """
    if not c.config.project.get('supervisor'):
        # nothing to do
        return True

    app_name = f'{c.config.project.user}_supervisor'
    app_id = c.config.data.get('supervisor_app_id')
    c.config.data.supervisor_app_id = create_app(c, app_name, app_id)
    return True


def _build_args(args_dict, dl=' '):
    return " ".join([f'--{k}{dl}{v}' for k, v in args_dict.items()])


def _build_main_config(config):
    """
    Build supervisord.conf
    """
    user = config.project.user
    ini = configparser.ConfigParser()
    ini['unix_http_server'] = {
        'file': f'/home/{user}/tmp/supervisor.sock',
    }
    # ini['inet_http_server'] = {
    #     'port': '127.0.0.1:9001',
    # }

    sv = config.project.get('supervisor').copy()
    _ = sv.pop('programs', None)
    env = sv.pop('environment', None)
    if isinstance(env, list):
        env = ', '.join(env)

    supervisord = {}
    supervisord.update(sv)

    supervisord.setdefault('logfile', f'/home/{user}/logs/apps/{user}_supervisor/supervisord.log')
    supervisord.setdefault('loglevel', sv.get('loglevel', 'info'))
    supervisord.setdefault('pidfile', f'/home/{user}/tmp/supervisord.pid')
    if env:
        supervisord.setdefault('environment', env)

    ini['supervisord'] = supervisord

    ini['rpcinterface:supervisor'] = {
        'supervisor.rpcinterface_factory': 'supervisor.rpcinterface:make_main_rpcinterface',
    }
    ini['supervisorctl'] = {
        'serverurl': f'unix:///home/{user}/tmp/supervisor.sock',
    }
    ini['include'] = {
        'files': f'/home/{user}/etc/supervisor.d/*.conf',
    }

    remote_path = f'/home/{user}/etc/supervisord.conf'

    # return as text
    with io.StringIO() as f:
        ini.write(f)
        return f.getvalue(), remote_path


def _build_project_config(config):
    """
    Build the project conf file for supervisor.
    Requires info from redis and application tasks (ports and whatnot).
    """
    sv = config.project.supervisor
    ini = configparser.ConfigParser()

    config.project.supervisor.get('loglevel', 'info')

    loglevel = sv.get('loglevel', 'info')

    # group
    programs = sv.get('programs').copy()
    group = programs.pop('group', None)
    if group:
        if isinstance(group, list):
            group = ', '.join(group)
        ini[f'group:{config.project.name}'] = {
            'programs': group,
        }

    # programs
    for name in programs:

        # build command
        section = programs.get(name)
        args = section.pop('args', {})
        cmd = section.pop('command', None)

        # celery worker -------------------------
        if cmd == 'celery-worker':
            # loglevel is command arg
            if 'loglevel' not in args:
                args['loglevel'] = loglevel.upper()

            args = _build_args(args, '=')
            command = f'{config.data.env_path}/bin/celery -A {config.project.name} worker {args}'

        # celery beat ---------------------------
        elif cmd == 'celery-beat':
            # loglevel is command arg
            if 'loglevel' not in args:
                args['loglevel'] = loglevel.upper()
            args.setdefault('pidfile', f'{config.data.app_path}/tmp/celerybeat.pid')

            args = _build_args(args, '=')
            command = f'{config.data.env_path}/bin/celery -A {config.project.name} beat {args}'

        # redis-server --------------------------
        elif cmd == 'redis-server':
            args.setdefault('port', config.data.redis_app_info.port)
            args.setdefault('dir', f'/home/{config.project.user}/tmp')
            args.setdefault('logfile', f'/home/{config.project.user}/logs/apps/{config.data.redis_app_info.name}/redis.log')
            args.setdefault('pidfile', f'/home/{config.project.user}/tmp/redis.pid')
            if 'loglevel' not in args:
                args['loglevel'] = loglevel.upper()

            args = _build_args(args)
            command = f'{config.redis_server} /home/{config.project.user}/etc/redis.conf {args}'

            section.setdefault('directory', f'/home/{config.project.user}/apps/{config.data.redis_app_info.name}')

        # gunicorn ------------------------------
        elif cmd == 'gunicorn':
            args.setdefault('pid', f'{config.data.app_path}/tmp/gunicorn.pid')
            args.setdefault('bind', f'127.0.0.1:{config.data.app_info.port}')
            args.setdefault('access-logfile', '-')  # log to stdout, let supervisor handle this
            args.setdefault('error-logfile', '-')  # log to stderr, pass to supervisor
            if 'loglevel' in args:
                args['log-level'] = args.pop('loglevel')

            args = _build_args(args)
            command = f'{config.data.env_path}/bin/gunicorn {args} {config.project.name}.wsgi:application'

        # uwsgi ---------------------------------
        elif cmd == 'uwsgi':
            continue

        else:
            print(f'{RED}Unknown supervisor command: {cmd}.{COL_END}')
            continue

        section_params = {
            'command': command,
        }

        section_params.update(section.copy())

        section_params.setdefault('user', config.project.user)
        section_params.setdefault('directory', config.data.src_path)
        section_params.setdefault('autostart', True)
        section_params.setdefault('autorestart', True)

        # as suggested: https://github.com/Supervisor/supervisor/issues/600#issuecomment-287054424
        section_params.setdefault('stopasgroup', True)
        section_params.setdefault('stopsignal', 'QUIT')

        section_params.setdefault('stdout_logfile', f'{config.data.log_path}/{name}.log')
        if 'stderr_logfile' not in section_params:
            section_params.setdefault('redirect_stderr', True)

        ini[f'program:{name}'] = section_params

    remote_path = f'/home/{config.project.user}/etc/supervisor.d/{config.project.name}.conf'

    # return as text
    with io.StringIO() as f:
        ini.write(f)
        return f.getvalue(), remote_path


def _upload_config(c, local_config, remote_path, force_upload=False):
    """
    Upload config to remote path.

    :param c:
    :param local_config: Generated config
    :param remote_path: Path to remote file
    :param force_upload: When True, don't check with remote and compare, default: False
    :return:
    """
    remote_config = None
    if not force_upload:
        # retrieve remote version of config file
        result = c.run(f'cat {remote_path}', warn=True, hide=True)
        remote_config = result.stdout

    if force_upload or local_config != remote_config:
        # upload local config to remote location
        print(f'Updating {remote_path}...')
        c.put(io.StringIO(local_config), remote_path)


def create_configs(c):
    if not c.config.project.get('supervisor'):
        # nothing to do
        return True

    # create config dirs
    c.run('mkdir -p ~/etc && mkdir -p ~/etc/supervisor.d')

    # create main supervisor config
    cfg_main, remote_path = _build_main_config(c.config)
    _upload_config(c, cfg_main, remote_path, force_upload=True)

    # create project supervisor config
    cfg_project, remote_path = _build_project_config(c.config)
    _upload_config(c, cfg_project, remote_path, force_upload=True)
    return True


def update_configs(c):
    if not c.config.project.get('supervisor'):
        # nothing to do
        return True

    # create main supervisor config
    cfg_main, remote_path = _build_main_config(c.config)
    _upload_config(c, cfg_main, remote_path, force_upload=False)

    # create project supervisor config
    cfg_project, remote_path = _build_project_config(c.config)
    _upload_config(c, cfg_project, remote_path, force_upload=False)
    return True


def start(c):
    # start supervisord
    print(f'{CYAN}Starting supervisord...{COL_END}')
    result = c.run(f'~/bin/supervisord -c ~/etc/supervisord.conf', warn=True, hide=True)
    if not result.ok:
        print('Supervisord is already running. Attempting config update...')
        c.run('supervisorctl update')
    return True


def restart(c):
    # restart project
    print(f'{CYAN}Restarting {c.config.project.name}...{COL_END}')
    c.run(f'supervisorctl reread', echo=True)
    c.run(f'supervisorctl update', echo=True)
    c.run(f'supervisorctl restart all', echo=True)
    return True
