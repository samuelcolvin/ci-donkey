import uuid
from collections import OrderedDict

def process_request(request, allowed_hooks):
    """
    extracts the required data about the event from
    a request object resulting from a webhook request.
    """
    info = OrderedDict([
        ('event_type', 'unknown webhook'),
        ('author', None),
        ('message', None),
        ('display_url', None),
        ('private', None),
        ('git_url', None),
        ('sha', None)
    ])
    try:
        rjson = request.get_json()
        info['event_type'] =  request.headers.get('X-GitHub-Event')
        if info['event_type'] not in allowed_hooks:
            return False, '"%s" is not an allowed webhook.'
        if info['event_type'] == 'push':
            info['author'] = rjson['pusher']['name']
            info['message'] = rjson['head_commit']['message']
            info['display_url'] = rjson['head_commit']['url']
            info['private'] = rjson['repository']['private']
            info['git_url'] = rjson['repository']['git_url']
            info['sha'] = rjson['repository']
            info['label'] = rjson['head_commit']['id']
        elif info['event_type'] == 'pull_request':
            info['author'] = rjson['sender']['login']
            info['message'] = rjson['pull_request']['title']
            info['display_url'] = rjson['pull_request']['_links']['html']['href']
            info['private'] = rjson['pull_request']['head']['repo']['private']
            info['git_url'] = rjson['pull_request']['head']['repo']['git_url']
            info['sha'] = rjson['pull_request']['head']['sha']
            info['label'] = rjson['pull_request']['head']['label']
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