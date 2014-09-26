from django.conf import settings
import docker
import re
import io
import json


def _get_con():
    return docker.Client(base_url='unix://var/run/docker.sock', version='1.12', timeout=10)


def build_image(docker_file, image_name='cidonkey'):
    df = io.BytesIO(docker_file)
    b = _get_con().build(fileobj=df, tag=image_name)
    results = json.loads('[' + ','.join(b) + ']')
    return ''.join([str(r.values()[0]) for r in results])


def start_ci(image_name, src_dir):
    c = _get_con()
    con = c.create_container(image=image_name, volumes=[settings.PERSISTENCE_DIR, src_dir])
    if con['Warnings']:
        print 'Warning:', con['Warnings']
    c.start(con, binds={
        '/persistence/': {'bind': settings.PERSISTENCE_DIR, 'ro': False},
        '/src/': {'bind': src_dir, 'ro': True}
    })
    return con['Id']


def check_progress(con_id):
    c = _get_con()
    if con_id in [con['Id'] for con in c.containers()]:
        return
    if con_id in [con['Id'] for con in c.containers(all=True)]:
        raise Exception('wow, container not found')
    con = next(con for con in c.containers(all=True) if con['Id'] == con_id)
    status = con['Status']
    m = re.search('\((\d+)\)', status)
    if not m:
        raise Exception('wow, no status code found: "%s"' % status)
    return_code = int(m.groups()[0])
    logs = c.logs(con_id)
    return return_code, logs
