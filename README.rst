Sense grouping survey
=====================

Install::

    pip install -r requirements.txt

Run migrations and load initial data::

    ./manage.py migrate
    ./manage.py loaddata survey/fixtures/initial_data.yaml

Load dummy contexts for testing::

    ./manage.py loaddata survey/fixtures/contexts.yaml

Or load real contexts::

    ./manage.py load_contexts "Words - Sheet1.csv"

Create superuser::

    ./manage.py createsuperuser

Start development server::

    ./manage.py runserver

