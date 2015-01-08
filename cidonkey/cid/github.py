import hashlib
import hmac
from cidonkey.cid import UPDATE_CONTEXT
import requests
import json
from requests.packages.urllib3.exceptions import ConnectionError


def process_github_webhook(request, build_info):
    """
    extracts the required data about the event from
    a request object resulting from a webhook request.
    """
    headers = request.META
    if not _validate_signature(request.body, headers, build_info.project.webhook_secret):
        return 403, 'permission denied'
    try:
        rjson = json.loads(request.body)
    except ValueError, e:
        return 400, 'Error parsing JSON: %s' % str(e)
    build_info.trigger = headers.get('HTTP_X_GITHUB_EVENT', 'unknown')
    private = None
    if build_info.trigger not in build_info.project.webhooks:
        return False, '"%s" is not an allowed webhook.' % build_info.trigger
    if build_info.trigger == 'push':
        build_info.author = rjson['pusher']['name']
        if rjson['head_commit'] is None:
            return 200, 'head_commit null, not building'
        build_info.commit_message = rjson['head_commit']['message']
        build_info.display_url = rjson['head_commit']['url']
        build_info.sha = rjson['head_commit']['id']
        build_info.label = rjson['ref']
        build_info.status_url = rjson['repository']['statuses_url'].replace('{sha}', build_info.sha)
        default_branch = rjson['repository']['default_branch']
        build_info.on_master = build_info.label.split('/')[-1] == default_branch
        private = rjson['repository']['private']
    elif build_info.trigger == 'pull_request':
        build_info.author = rjson['sender']['login']
        build_info.commit_message = rjson['pull_request']['title']
        build_info.display_url = rjson['pull_request']['_links']['html']['href']
        private = rjson['pull_request']['head']['repo']['private']
        build_info.sha = rjson['pull_request']['head']['sha']
        build_info.action = rjson['action']
        if build_info.action == 'closed':
            return 200, 'not running ci when pull request is closed'
        build_info.label = rjson['pull_request']['head']['label']
        if build_info.label.split(':')[0] == build_info.project.github_user:
            return 200, 'not running ci for local pull request, should be triggered by push'
        build_info.status_url = rjson['pull_request']['statuses_url']
        build_info.fetch_cmd = 'pull/%(number)d/head:pr_%(number)d' % rjson
        build_info.fetch_branch = 'pr_%(number)d' % rjson
        build_info.on_master = False
    if build_info.project.private != private:
        print 'changing project private status to %r' % private
        build_info.project.private = private
        build_info.project.save()
    try:
        statues, _ = github_api(build_info.status_url, build_info.project.github_token)
    except ConnectionError, e:
        return 400, 'error getting status: %r' % e
    statues = [s for s in statues if s.get('context', '') == UPDATE_CONTEXT]
    if len(statues) > 0 and not build_info.project.allow_repeat:
        return 200, 'not running ci, status already exists for this commit'
    build_info.save()
    return 202, build_info


def _validate_signature(data, headers, secret):
    sig_header = 'HTTP_X_HUB_SIGNATURE'
    if sig_header not in headers:
        return False
    sha_name, signature = headers[sig_header].split('=')
    if sha_name != 'sha1':
        return False
    mac = hmac.new(str(secret), msg=str(data), digestmod=hashlib.sha1)
    return mac.hexdigest() == signature


def github_api(url, token, method=requests.get, data=None, extra_headers=None):
    headers = {'Authorization': 'token %s' % token}
    if extra_headers:
        headers.update(extra_headers)
    payload = None
    if data:
        payload = json.dumps(data)
    r = method(url, data=payload, headers=headers)
    try:
        return json.loads(r.text), r
    except ValueError:
        return None, r
