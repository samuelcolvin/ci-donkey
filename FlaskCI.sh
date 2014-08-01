# this is an example test script
# <PRE SCRIPT>:
virtualenv env
env/bin/pip install -r requirements.txt
grablib grablib.json
echo "this is just an example"

# <MAIN SCRIPT>:
# python manage.py test
python sample_test.py