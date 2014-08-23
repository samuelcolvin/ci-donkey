ci-donkey
=======

Simple Continuous Integration


## Basic Setup

Run the following:

    cd /var/www/
    git clone git@github.com:samuelcolvin/ci-donkey.git
    cd ci-donkey/
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt 
    grablib grablib.json

## To run the dev server

    python runserver.py

## To deploy with Nginx

This assumes you already have Nginx working.

If you haven't run the dev server there will be no initial user to login with, you can create a user with

    python create_user.py

If will prompt you to create a user if none exist.

We're going to run ci-donkey as the `www-data` user, make them the group for your project directory:

    sudo chown -R samuel:www-data /var/www/ci-donkey

Edit one of the `conf` files in `setup/` to set your server

Copy it to `available-sites` and enable it

    sudo cp setup/<conf file>.conf /etc/nginx/sites-available/cid.conf
    sudo ln -s /etc/nginx/sites-available/cid.conf /etc/nginx/sites-enabled/

If you used `basic-auth` in your conf file, you need to setup a password file, for this you need `apache-utils` installed:

    sudo apt-get install apache2-utils
    htpasswd -c cid.htpasswd <username>

Check the user id for `www-data`

    id -u www-data

set `uid` and `gid` to that value in `setup/uwsgi.ini`

Start `uwsgi`:

    sudo /var/www/ci-donkey/env/bin/uwsgi --ini /var/www/ci-donkey/setup/uwsgi.ini

You can check the log to see if it's started ok:

    sudo tail -n 100 /var/log/cid-uwsgi.log

If everything has gone ok you can restart nginx:

    sudo service nginx restart