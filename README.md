ci-donkey
=======

Simple Continuous Integration based on django and docker with excellent github integration.

Supports:
* **Build Badge** showing status (building, passing, failing) for use in readme files.
* **Github webhooks** to kick off builds
* **Github status updates** to mark commits and pull requests as passing/failing.
* **intelligent setup caching** for faster build. A persistent attached volume on the docker image allows you to check the hash of your pre test setup (eg. python's `requirements.txt` file) and copy it into place if it exists instead of rebuilding it.
* **prebuild/build** split, so you can visually and logically split CI setup and actual setup.
* **Coverage** the output can be parsed for the coverage value which which is then listed next to builds.

## Basic Setup

Run the following:

    cd /var/www/
    git clone git@github.com:samuelcolvin/ci-donkey.git
    cd ci-donkey/
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt 
    grablib grablib.json
    ./manage.py syncdb

## To run the dev server

    ./manage.py runserver

## To deploy with Nginx

This assumes you already have Nginx working.

We're going to run ci-donkey as the `www-data` user, make them the group for your project directory:

    sudo chown -R samuel:www-data /var/www/ci-donkey

Edit one of the `conf` files in `setup/` to set your server

Copy it to `available-sites` and enable it

    sudo cp setup/<conf file>.conf /etc/nginx/sites-available/cid.conf
    sudo ln -s /etc/nginx/sites-available/cid.conf /etc/nginx/sites-enabled/

Check the user id for `www-data`

    id -u www-data

set `uid` and `gid` to that value in `setup/uwsgi.ini`

Start `uwsgi`:

    sudo /var/www/ci-donkey/env/bin/uwsgi --ini /var/www/ci-donkey/setup/uwsgi.ini

You can check the log to see if it's started ok:

    sudo tail -n 100 /var/log/cid-uwsgi.log

If everything has gone ok you can restart nginx:

    sudo service nginx restart
