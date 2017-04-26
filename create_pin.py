import webapp2
import os
import jinja2
import base64
import uuid
import httplib2
import urllib
import re
import json

from google.appengine.ext import ndb
from kitsunemap_entities import Pin
import credentials

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class CreatePinHandler(webapp2.RequestHandler):
    def post(self):
        form_error_message = None
        try:
            name = self.request.POST.get('name').strip()
            about_you = self.request.POST.get('about_you').strip()
            email = self.request.POST.get('email').strip()
            pin_icon = int(self.request.POST.get('pin_icon'))
            favorite_member = int(self.request.POST.get('favorite_member'))
            favorite_song = int(self.request.POST.get('favorite_song'))
            latitude = self.request.POST.get('latitude')
            longitude = self.request.POST.get('longitude')
            geo_point = ndb.GeoPt(latitude, longitude)
            communities = self.request.POST.get('communities')
             # this will raise an error if the communities string is invalid
            [int(x) for x in communities.split(',')]

            if not name or not about_you or not email:
                form_error_message = "All fields are required."
            elif not is_valid_email(email) or not is_real_email(email):
                form_error_message = "A valid email address is required."
            elif Pin.query(Pin.email == email).get():
                form_error_message = "A pin already exists for this email address."
        except:
            form_error_message = "All fields are required."

        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        access_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
        user_ip_address = self.request.remote_addr
        new_pin = Pin(
            name = name,
            about_you = about_you,
            email = email,
            pin_icon = pin_icon,
            favorite_member = favorite_member,
            favorite_song = favorite_song,
            communities = communities,
            point = geo_point,
            access_uuid = access_uuid,
            user_ip_address = user_ip_address,
        )
        new_pin.put()
        send_activate_email(email, access_uuid)

        template = JINJA_ENVIRONMENT.get_template('templates/email_sent.html')
        self.response.write(template.render())

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

def send_activate_email(recipient, access_uuid):
    http = httplib2.Http()
    http.add_credentials('api', credentials.MAILGUN_API_KEY)

    activation_url = "https://kitsune.network/?activatePin=%s" % access_uuid
    html_message = """
        <a href="%s">Click here to activiate your pin.</a>
        <p />
        Or copy and paste this URL into your browser:
        <br />
        %s
    """ % (activation_url, activation_url)

    domain = 'kitsune.network'
    url = 'https://api.mailgun.net/v3/%s/messages' % domain
    data = {
        'from': 'Kitsune Network <no-reply@%s>' % domain,
        'to': recipient,
        'subject': 'Activate your pin',
        'text': 'Activate your pin by going to the following url: %s' % activation_url,
        'html': html_message
    }

    resp, content = http.request(
        url, 'POST', urllib.urlencode(data),
        headers={"Content-Type": "application/x-www-form-urlencoded"})

    if resp.status != 200:
        raise RuntimeError(
            'Mailgun API error: {} {}'.format(resp.status, content))
