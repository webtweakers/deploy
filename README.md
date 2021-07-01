
Deploy
===

*Deploy* is a set of [Fabric](http://www.fabfile.org/) tasks to install and deploy projects to a server. 
It was written specifically to deploy a [Python](https://www.python.org/) / [Django](https://www.djangoproject.com/) project to [Opalstack](https://opalstack.com/), 
but in theory, could be used to install and deploy any type of project to
any hosting provider. A requirement is that the hosting provider has an API.
A simple client for Opalstack's v1 API is provided.

Note: At this time the API for Opalstack is not completely implemented. Feel free to help out!

Installation
===

Create virtual env
---

Using python 3:

```
python -m venv /path/to/env
```

Or when using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/):

```
mkvirtualenv deploy
workon deploy
```


Checkout *Deploy* project
---

```
git clone https://github.com/webtweakers/deploy.git
```


Install requirements
---

```
pip install -r requirements.txt
```


Configure your project
===

Keep the configuration of your project in its root directory. For example: `/path/to/project/fabric.yml`.

An example `fabric.yml` configuration file, showing all current features:

```yaml
control:
  service: opalstack  # currently only Opalstack is supported
  username: myuser  # your username and password for the control panel
  password: mypass
  token: 123abc  # OR alternatively create a token in the control panel and use it here

project:
  server: opal1.opalstack.com  # server to install project
  name: myproject  # name of your project, this will create /home/myuser/apps/myproject
  user: myuser  # user for your project, this will create /home/myuser
  pass:
  source: src  # path within /path/to/project where your project code is located
  database: postgres  # or: mariadb
  dependencies:  # dependencies you'd like to be installed on Opalstack
    python: 3.9.0
    redis: 6.2.2

  supervisor:
    loglevel: info  # default: info
    environment:
      - DJANGO_SETTINGS_MODULE="myproject.settings"
      - LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8", LC_LANG="en_US.UTF-8"
    strip_ansi: true

    programs:
      group: celery_worker, celery_beat, gunicorn  # this will create a [group:myproject] in supervisor

      celery_worker:  # name of [program:...] in supervisor config
        command: celery-worker  # deploy supervisor command
        args:
          concurrency: 3
          hostname: celery@myhost.com
          queues: celery

      celery_beat:
        command: celery-beat  # deploy supervisor command

      gunicorn:
        command: gunicorn  # deploy supervisor command
        args:
          workers: 2
          threads: 1
          max-requests: 100
          loglevel: error

      redis:
        command: redis-server  # deploy supervisor command
```

This is basic YAML, so you could also write this, for instance:

```yaml

    programs:
      group:
        - celery_worker
        - celery_beat
        - gunicorn
```

*Deploy* currently supports [supervisor](http://supervisord.org/) to manage services and will create
and update its configuration files based on the settings provided in your `fabric.yml`.

*Deploy* currently recognises a set of supervisor commands and will create basic configurations for those.
You can fine-tune by specifying args, as shown above. The commands currently supported:
- celery-worker
- celery-beat
- gunicorn
- redis-server

The idea behind *Deploy* is to keep the `fabric.yml` file as short, minimal and simple as possible and
perform a little bit of magic behind the screens to install all requirements correctly. *Deploy* uses
basic defaults that can be overridden using the configuration.


Running tasks
---

To get a list of available tasks, type:

```
fab -f /path/to/project/fabric.yml -l
```


For the initial installation of your project, type:

```
fab -f /path/to/project/fabric.yml install
```

This command will create an SSH config on your system, to be used when connecting with the hosting
provider. Project dependencies as configured in your project configuration, if any, will be installed 
and also a virtualenv and supervisor will be installed on the server. Additionally, your complete 
project will be installed. This process is incremental: should anything go wrong, you can run install 
again and any steps that were performed successfully will be skipped.


To run subsequent deployment updates, use:

```
fab -f /path/to/project/fabric.yml deploy
```

While deploying, a backup of your current live project files and database will be made.


To perform a rollback in case of problems with your new release, type:

```
fab -f /path/to/project/fabric.yml rollback
```


Remote environment variables
---

*Deploy* makes use of [python-dotenv](https://github.com/theskumar/python-dotenv) and will also
install it on the remote server, along with the virtual environment. In theory, it can be used to 
edit the remote environment, if you have an `.env` file located in your src path. (In practice,
however, editing remote environment variables using *Deploy* is not working well at the moment. You'll need
to update your `.env` and re-deploy or manually update on the server.)

To list all remote environment variables:
```
fab -f $HOME/dev/chaturfier/fabric.yml env
```


TODO
===
- Add support for more APIs: domains, sites, etc.
- Use command-line argument to set verbosity level for output logging.
- Improve output logging code, eg. use python logger instead of print statements.
- Add support for more apps and services, eg.:
    - [circus](https://circus.readthedocs.io/en/latest/)
    - [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/)
- Provide more customization options to make *Deploy* also work with PHP, for instance.
