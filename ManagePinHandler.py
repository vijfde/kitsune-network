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

        form_error_message = Pin.validate_pin_values(self.request.POST, False)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        pin.set_pin_values(self.request.POST, self.request.remote_addr, False)

        template = JINJA_ENVIRONMENT.get_template('templates/pin_updated.html')
        self.response.write(template.render())

    def post(self):
        form_error_message = Pin.validate_pin_values(self.request.POST, True)
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
