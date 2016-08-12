rm survey/migrations/0001_initial.py
rm db.sqlite3
./manage.py makemigrations
./manage.py migrate
./manage.py loaddata survey/fixtures/initial_data.yaml
./manage.py loaddata survey/fixtures/contexts.yaml
