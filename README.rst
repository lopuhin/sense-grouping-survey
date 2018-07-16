Sense grouping survey
=====================

This is code for running a survey that discovers how different people group
word contexts into senses.

If you are going to use it in your own work, please change text and email in
``./templates/start.html``, and email in ``./templates/group.html``.
Also please site our (submitted) paper :)

Also note that this survey does not work in mobile browsers
due to drag-n-drop issues (should be possible to fix). Desktop IE is supported.

There is an alternative design with jars instead of baskets
in the ``new-variant`` branch.


Usage
-----

Check out user instructions in ``./templates/start.html``.

You can add ``?source=some-value`` argument to experiment link, this will
be tracked in the ``source`` field.

You can download results for respondents who completed all tasks
at ``/export`` URL, and results for all respondents at ``/export?all=``.
Partisipants will be in ``_participants.csv``, and there will be a csv file
for each participant.


Installation
------------

Install (short version)::

    pip install -r requirements.txt

In more detail, assuming Ubuntu 16.04:

    sudo apt install python3.5-venv python3-dev
    git clone git@github.com:lopuhin/sense-grouping-survey.git
    cd sense-grouping-survey
    python3 -m venv venv
    . venv/bin/activate
    pip install pip wheel -U
    pip install -r requirements.txt

Data is stored in an SQLite database in ``./db.sqlite3``.

Run migrations and load initial data::

    ./manage.py migrate
    ./manage.py loaddata survey/fixtures/initial_data.yaml

Next you can load dummy contexts for testing::

    ./manage.py loaddata survey/fixtures/contexts.yaml

or load real contexts from a more convenient format
(see ``example-contexts.csv``)::

    ./manage.py load_contexts "example-contexts.csv"
    # or
    ./manage.py load_contexts_with_fillers "example-contexts.csv"

Create superuser::

    ./manage.py createsuperuser

Start development server::

    ./manage.py runserver


Deployment
----------

Fist, collect static::

    ./manage.py collectstatic

Then there are many options for production deployment, see
https://docs.djangoproject.com/en/1.10/howto/deployment/

One easy but not optimal (it's better to put nginx in front)
way is to use just ``gunicorn`` and ``supervisord``::

    sudo apt install supervisor
    pip install gunicorn
    mkdir conf

Then create ``conf/supervisor.conf`` file along this lines
(again, this is far from ideal in many cases, just an example)::

    [program:sgs]
    environment=SECRET_KEY="generate some secret key, dont share it!"
    command=/root/sense-grouping-survey/venv/bin/gunicorn sgs.wsgi -b 0.0.0.0:80 -w 4 --timeout 60 --access-logfile=/root/sense-grouping-survey/access.log --access-logformat '%%(h)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s" %%(f)s'
    directory=/root/sense-grouping-survey/
    autostart=true
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/root/sense-grouping-survey/error.log

and then do::

    supervisorctl start sgs

