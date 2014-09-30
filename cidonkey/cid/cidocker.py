from cidonkey.cid.common import KnownError
from django.conf import settings
import docker
import io
import json
import dateutil.parser


def _get_con():
    return docker.Client(base_url='unix://var/run/docker.sock', version='1.12', timeout=10)


def build_image(docker_file, image_name='cidonkey'):
    df = io.BytesIO(docker_file)
    b = _get_con().build(fileobj=df, tag=image_name)
    results = json.loads('[' + ','.join(b) + ']')
    return ''.join([str(r.values()[0]) for r in results])


def start_ci(image_name, src_dir):
    c = _get_con()
    binds = {
        settings.PERSISTENCE_DIR: {'bind': '/persistence/', 'ro': False},
        src_dir: {'bind': '/src/', 'ro': True}
    }
    volumes = [b['bind'] for b in binds.values()]
    con = c.create_container(image=image_name, volumes=volumes)
    if con['Warnings']:
        print 'Warning:', con['Warnings']
    c.start(con, binds=binds)
    return con['Id']


def check_progress(con_id):
    c = _get_con()
    con = c.inspect_container(con_id)
    state = con['State']
    if state['Running']:
        return
    exit_code = state['ExitCode']
    finish_str = state['FinishedAt']
    finished = dateutil.parser.parse(finish_str)
    logs = c.logs(con_id)
    return exit_code, finished, logs, con


def delete_old_containers(del_con_ids):
    c = _get_con()
    all_con_ids = [con['Id'] for con in c.containers(all=True)]
    deleted_cons = []
    for del_con_id in del_con_ids:
        if del_con_id in all_con_ids:
            c.remove_container(del_con_id)
            deleted_cons.append(del_con_id)
    return deleted_cons
