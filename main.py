#!/usr/bin/env python
import logging

import webapp2
import os
import jinja2
import json

from kitsunemap_entities import Pin
from create_pin import CreatePinHandler

import cloudstorage as gcs
from google.appengine.api import app_identity

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        show_modal_onload = False
        activate_pin_uuid = self.request.GET.get('activatePin')
        if activate_pin_uuid != None:
            pin = Pin.query(Pin.access_uuid == activate_pin_uuid).get()
            if pin != None:
                pin.is_activated = True
                pin.access_uuid = ""
                pin.put()
                show_modal_onload = True
                template_values["show_pin_activated_message"] = True
        template_values["show_modal_onload"] = show_modal_onload
        template = JINJA_ENVIRONMENT.get_template('templates/map.html')
        self.response.write(template.render(template_values))

class PinsHandler(webapp2.RequestHandler):
    def get(self):
        pins_dict = []
        for pin in Pin.query(Pin.is_activated == True).fetch():
            pin_dict = {}
            pin_dict["id"] = pin.key.id()
            pin_dict["icon"] = pin.pin_icon
            pin_dict["lat"] = pin.point.lat
            pin_dict["lng"] = pin.point.lon
            pins_dict.append(pin_dict)
        self.response.out.write(json.dumps(pins_dict))

class PinHandler(webapp2.RequestHandler):
    def get(self, pin_id):
        pin = Pin.get_by_id(int(pin_id))
        if pin == None:
            self.response.set_status(404)
            self.response.out.write("")
            return
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        with gcs.open('/' + bucket_name + '/data.json') as cloudstorage_file:
            data = cloudstorage_file.read()
            data = json.loads(data)
        members = {
            '1': 'SU-METAL',
            '2': 'MOAMETAL',
            '3': 'YUIMETAL',
            '0': 'They are all my favorite',
        }
        template_values = {
            'pin': pin,
            'fav_song': members[str(pin.favorite_song)],
            'fav_member': data['songs'][str(pin.favorite_song)],
            'communities': [data['communities'][str(community)] for community in pin.communities],
        }
        template = JINJA_ENVIRONMENT.get_template('templates/pin_info_window.html')
        self.response.write(template.render(template_values))

class NewPinFormHandler(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        with gcs.open('/' + bucket_name + '/data.json') as cloudstorage_file:
            data = cloudstorage_file.read()
            data = json.loads(data)
            template_values = {
                'songs': data['songs'],
                'communities': data['communities'],
            }
            template = JINJA_ENVIRONMENT.get_template('templates/new_pin_form.html')
            self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', CreatePinHandler),
    ('/pin/(.*)', PinHandler),
    ('/pins', PinsHandler),
    ('/new_pin_form.html', NewPinFormHandler),
], debug=True)
