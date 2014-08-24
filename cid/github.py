import uuid
from collections import OrderedDict

def process_request(request, allowed_hooks):
    """
    extracts the required data about the event from
    a request object resulting from a webhook request.
    """
    info = OrderedDict([
        ('trigger', 'unknown webhook'),
        ('author', None),
    ])
    try:
        rjson = request.get_json()
        info['trigger'] =  request.headers.get('X-GitHub-Event')
        if info['trigger'] not in allowed_hooks:
            return False, '"%s" is not an allowed webhook.' % info['trigger']
        if info['trigger'] == 'push':
            info['author'] = rjson['pusher']['name']
            info['message'] = rjson['head_commit']['message']
            info['display_url'] = rjson['head_commit']['url']
            info['private'] = rjson['repository']['private']
            info['default_branch'] = rjson['repository']['default_branch']
            info['sha'] = rjson['head_commit']['id']
            info['label'] = rjson['ref']
            info['status_url'] = rjson['repository']['statuses_url']\
                    .replace('{sha}',info['sha'])
        elif info['trigger'] == 'pull_request':
            info['author'] = rjson['sender']['login']
            info['message'] = rjson['pull_request']['title']
            info['display_url'] = rjson['pull_request']['_links']['html']['href']
            info['private'] = rjson['pull_request']['head']['repo']['private']
            info['sha'] = rjson['pull_request']['head']['sha']
            info['action'] = rjson['action']
            if info['action'] == 'closed':
                return False, 'not running ci when pull request is closed'
            info['label'] = rjson['pull_request']['head']['label']
            info['status_url'] = rjson['pull_request']['statuses_url']
            info['fetch'] = 'pull/%(number)d/head:pr_%(number)d' % rjson
            info['fetch_branch'] = 'pr_%(number)d' % rjson
    except Exception, e:
        print 'Exception getting hook details: %r' % e
        try:
            requestinfo = str(request.headers)
            requestinfo += '\n' + str(rjson)
            fn = '/tmp/%s.log' % uuid.uuid4()
            open(fn, 'w').write(requestinfo)
            print 'data saved to %s' % fn
        except Exception:
            pass
        return e
    return True, info

