#!/usr/bin/env python
import logging

import webapp2
import os
import jinja2
import json
import httplib2
import urllib

from kitsunemap_entities import Pin
from create_pin import CreatePinHandler
import const_data
import credentials

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
                send_discord_web_hook(pin)
                show_modal_onload = True
                template_values["show_pin_activated_message"] = True
        template_values["show_modal_onload"] = show_modal_onload
        template = JINJA_ENVIRONMENT.get_template('templates/map.html')
        self.response.write(template.render(template_values))

def send_discord_web_hook(pin):
    http = httplib2.Http()
    pin_details = ''
    pin_details += '\nTitle: ' + pin.name
    pin_details += '\nFav Song: ' + const_data.songs[str(pin.favorite_song)]
    pin_details += '\nFav Member: ' + const_data.members[str(pin.favorite_member)]
    pin_details += '\nCommunities: ' + ', '.join([const_data.communities[str(community)] for community in pin.communities.split(',')])
    pin_details += '\nAbout: \n' + pin.about_you
    content = """
        **New Pin Activated!**```%s```
    """ % pin_details
    content = content.encode('utf-8', 'ignore')
    data = { 'content': content }
    url = credentials.DISCORD_WEB_HOOK_URL
    resp, content = http.request(url, 'POST', urllib.urlencode(data))

class PinsHandler(webapp2.RequestHandler):
    def get(self):
        # bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        # with gcs.open('/' + bucket_name + '/pins.json') as cloudstorage_file:
        #     pins = cloudstorage_file.read()
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
        template_values = {
            'pin': pin,
            'fav_song': const_data.songs[str(pin.favorite_song)],
            'fav_member': const_data.members[str(pin.favorite_member)],
            'communities': [const_data.communities[str(community)] for community in pin.communities.split(',')],
        }
        template = JINJA_ENVIRONMENT.get_template('templates/pin_info_window.html')
        self.response.write(template.render(template_values))

class NewPinFormHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/new_pin_form.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', CreatePinHandler),
    ('/pin/(.*)', PinHandler),
    ('/pins', PinsHandler),
    ('/new_pin_form.html', NewPinFormHandler),
], debug=True)
