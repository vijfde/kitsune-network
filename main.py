#!/usr/bin/env python
import logging

import webapp2
import os
import jinja2
import json
import cgi

from kitsunemap_entities import Pin
from create_pin import CreatePinHandler

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

class ModalHandler(webapp2.RequestHandler):
    def get(self, template_name):
        template = JINJA_ENVIRONMENT.get_template('templates/%s.html' % template_name)
        self.response.write(template.render())

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
        pin_dict = pin.to_dict(include=["name","favorite_song","communities","about_you","favorite_member"])
        self.response.out.write(cgi.escape(json.dumps(pin_dict)))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', CreatePinHandler),
    ('/pin/(.*)', PinHandler),
    ('/pins', PinsHandler),
    ('/modal/(new_pin_form)', ModalHandler),
], debug=True)
