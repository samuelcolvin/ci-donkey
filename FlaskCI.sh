# this is an example test script
# <PRE SCRIPT>:
virtualenv env
echo "we haven't changed source so remember to manually call the correct python (or other script)"
# env/bin/pip install -r requirements.txt
#./env/bin/grablib grablib.json
# this is should fail:
grablib grablib.json

# <MAIN SCRIPT>:
# python manage.py test
./env/bin/python sample_test.py