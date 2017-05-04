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
from utilities import is_valid_email
from utilities import is_real_email
from utilities import send_email

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

        pin.set_pin_values(self.request.POST, self.request.remote_addr, False)

        template = JINJA_ENVIRONMENT.get_template('templates/pin_updated.html')
        self.response.write(template.render())

    def post(self):
        form_error_message = get_form_error_message(self, self.request.POST, True)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        new_pin = Pin()
        new_pin.set_pin_values(self.request.POST, self.request.remote_addr, True)

        send_email(new_pin.email, new_pin.access_uuid, False)

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
