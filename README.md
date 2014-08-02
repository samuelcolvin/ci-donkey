FlaskCI
=======

Simple Continuous Integration System based on Flask


## Basic Setup

Run the following:

    cd /var/www/
    git clone git@github.com:samuelcolvin/FlaskCI.git
    cd FlaskCI/
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

We're going to run FlaskCI as the `www-data` user, make them the group for your project directory:

    sudo chown -R samuel:www-data /var/www/FlaskCI

Edit the `conf` file to set your server, template in `deploy-setup/flaskci.conf`

Copy it to `available-sites` and enable it

    sudo cp deploy-setup/flaskci.conf /etc/nginx/sites-available/
    sudo ln -s /etc/nginx/sites-available/flaskci.conf /etc/nginx/sites-enabled/

We've also enabled `auth_basic` in the conf file, so setup a password file, for this you need `apache-utils` installed:

    sudo apt-get install apache2-utils
    htpasswd -c flaskci.htpasswd <username>

Check the user id for `www-data`

    id -u www-data

set `uid` and `gid` to that value in `deploy-setup/uwsgi.ini`

Start `uwsgi`:

    sudo /var/www/FlaskCI/env/bin/uwsgi --ini /var/www/FlaskCI/deploy-setup/uwsgi.ini

You can check the log to see if it's started ok:

    sudo tail -n 100 /var/log/flaskci-uwsgi.log

If everything has gone ok you can restart nginx:

    sudo service nginx restart