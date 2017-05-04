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

class ManagePinHandler(webapp2.RequestHandler):
    def put(self):
        edit_pin_uuid = self.request.POST.get('editAccessUUID')
        pin = Pin.query(Pin.access_uuid == edit_pin_uuid).get()
        if pin == None:
            self.response.set_status(404)
            self.response.out.write("")
            return

        form_error_message = get_form_error_message(self, self.request.POST, False)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        set_pin_values(self, pin, self.request.POST, False)

        template = JINJA_ENVIRONMENT.get_template('templates/pin_updated.html')
        self.response.write(template.render())

    def post(self):
        form_error_message = get_form_error_message(self, self.request.POST, True)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        new_pin = Pin()
        set_pin_values(self, new_pin, self.request.POST, True)

        send_activate_email(new_pin.email, new_pin.access_uuid)

        template_values = { 'action': 'activate' }
        template = JINJA_ENVIRONMENT.get_template('templates/email_sent.html')
        self.response.write(template.render(template_values))

def get_form_error_message(self, request_values, is_new_pin):
    form_error_message = None
    try:
        name = request_values.get('name').strip()
        about_you = request_values.get('about_you').strip()
        if is_new_pin:
            email = request_values.get('email').strip()
            latitude = request_values.get('latitude')
            longitude = request_values.get('longitude')
            geo_point = ndb.GeoPt(latitude, longitude)
        pin_icon = int(request_values.get('pin_icon'))
        favorite_member = int(request_values.get('favorite_member'))
        favorite_song = int(request_values.get('favorite_song'))
        communities = request_values.get('communities')
         # this will raise an error if the communities string is invalid
        [int(x) for x in communities.split(',')]

        if not name or not about_you or (is_new_pin and not email):
            form_error_message = "All fields are required."
        elif is_new_pin and (not is_valid_email(email) or not is_real_email(email)):
            form_error_message = "A valid email address is required."
        elif is_new_pin and Pin.query(Pin.email == email).get():
            form_error_message = "A pin already exists for this email address."
    except:
        form_error_message = "All fields are required."

    return form_error_message

def set_pin_values(self, pin, request_values, is_new_pin):
    pin.name = request_values.get('name').strip()
    pin.about_you = request_values.get('about_you').strip()
    pin.pin_icon = int(request_values.get('pin_icon'))
    pin.favorite_member = int(request_values.get('favorite_member'))
    pin.favorite_song = int(request_values.get('favorite_song'))
    pin.communities = request_values.get('communities')
    pin.user_ip_address = self.request.remote_addr
    if is_new_pin:
        pin.access_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
        pin.email = request_values.get('email').strip()
        latitude = request_values.get('latitude')
        longitude = request_values.get('longitude')
        pin.point = ndb.GeoPt(latitude, longitude)
    else:
        pin.access_uuid = ""
    pin.put()

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
        <a href="%s">Click here to activate your pin.</a>
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
