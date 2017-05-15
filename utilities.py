import httplib2
import urllib
import json
import re

from google.appengine.api import app_identity

import credentials

def is_production_env():
    return app_identity.get_application_id() == 'kitsunemap'

def is_valid_email(email):
    if not email:
        return False
    # purposely removed "+" from regex to ignore alias addresses
    if re.match(r"^[a-z0-9_.-]+@[a-z0-9-]+\.[a-z0-9-.]+$", email) == None:
        return False
    return True

def is_real_email(email):
    http = httplib2.Http()
    http.add_credentials('api', credentials.MAILGUN_PUB_API_KEY)

    data = { 'address': email }
    url = 'https://api.mailgun.net/v3/address/validate?' + urllib.urlencode(data)
    resp, content = http.request(url, 'GET')

    if resp.status != 200:
        raise RuntimeError(
            'Mailgun API error: {} {}'.format(resp.status, content))

    response_json = json.loads(content)
    return response_json["is_valid"]

def is_spam_email(email):
    http = httplib2.Http()
    url = "http://api.antideo.com/email/" + email
    resp, content = http.request(url, 'GET')
    response_json = json.loads(content)
    if not response_json["free_provider"]:
        return True
    if response_json["spam"]:
        return True
    if response_json["scam"]:
        return True
    if response_json["disposable"]:
        return True
    return False

def send_email(recipient, access_uuid, is_edit):
    http = httplib2.Http()
    http.add_credentials('api', credentials.MAILGUN_API_KEY)

    action = "edit" if is_edit else "activate"
    protocol = 'https' if is_production_env() else 'http'
    hostname = 'kitsune.network' if is_production_env() else app_identity.get_default_version_hostname()
    host = protocol +  '://' + hostname
    url = "%s/?%sPin=%s" % (host, action, access_uuid)
    html_message = """
        <a href="%s">Click here to %s your pin.</a>
        <p />
        Or copy and paste this URL into your browser:
        <br />
        %s
    """ % (url, action, url)

    domain = 'kitsune.network' if is_production_env() else 'sandbox7b1ee101c872433f8911490bb3a9ba3b.mailgun.org'
    url = 'https://api.mailgun.net/v3/%s/messages' % domain
    header_action = "Edit" if is_edit else "Activate"
    data = {
        'from': 'Kitsune Network <no-reply@%s>' % domain,
        'to': recipient,
        'subject': '%s your pin' % header_action,
        'text': '%s your pin by going to the following url: %s' % (header_action, url),
        'html': html_message
    }

    resp, content = http.request(
        url, 'POST', urllib.urlencode(data),
        headers={"Content-Type": "application/x-www-form-urlencoded"})

    if resp.status != 200:
        raise RuntimeError(
            'Mailgun API error: {} {}'.format(resp.status, content))
