def is_valid_email(email):
    if not email:
        return False
    # purposely removed "+" from regex to ignore alias addresses
    if re.match(r"^[a-z0-9_.-]+@[a-z0-9-]+\.[a-z0-9-.]+$", email) == None:
        return False
    # valid email address, now check if the domain is blacklisted
    blacklist = open('disposable-email-domains/disposable_email_blacklist.conf')
    blacklist_content = [line.rstrip() for line in blacklist.readlines()]
    return not email.split('@')[1] in blacklist_content

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

def send_email(recipient, access_uuid, is_edit):
    http = httplib2.Http()
    http.add_credentials('api', credentials.MAILGUN_API_KEY)

    action = "edit" if is_edit else "activate"
    url = "https://kitsune.network/?%sPin=%s" % (action, access_uuid)
    html_message = """
        <a href="%s">Click here to %s your pin.</a>
        <p />
        Or copy and paste this URL into your browser:
        <br />
        %s
    """ % (url, action, url)

    domain = 'kitsune.network'
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
