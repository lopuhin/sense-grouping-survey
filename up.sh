set -e
git pull
cp db.sqlite3 db.sqlite3.backup
. ./venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py collectstatic --noinput
sudo supervisorctl restart sgs
