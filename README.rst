Sense grouping survey
=====================

Install::

    pip install -r requirements.txt

Run migrations and load initial data::

    ./manage.py migrate
    ./manage.py loaddata survey/fixtures/initial_data.yaml
    ./manage.py loaddata survey/fixtures/contexts.yaml

Create superuser::

    ./manage.py createsuperuser

Start development server::

    ./manage.py runserver

