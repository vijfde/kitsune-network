#!/usr/bin/env python
import logging

import webapp2
import os
import jinja2
import json
import base64
import uuid
import httplib2
import urllib
import re
import cgi

from google.appengine.ext import ndb
from kitsunemapEntities import Pin
import credentials

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
        pin_dict = pin.to_dict(include=["name","favorite_song","communities","about_you","favorite_member"])
        self.response.out.write(cgi.escape(json.dumps(pin_dict)))

class CreatePinHandler(webapp2.RequestHandler):
    def post(self):
        is_form_valid = True
        try:
            name = self.request.POST.get('name').strip()
            about_you = self.request.POST.get('about_you').strip()
            email = self.request.POST.get('email').strip()
            pin_icon = int(self.request.POST.get('pin_icon'))
            favorite_member = int(self.request.POST.get('favorite_member'))
            favorite_song = int(self.request.POST.get('favorite_song'))
            communities = self.request.POST.get('communities')
            communities_list = ([int(x.strip()) for x in communities.split(',')])
            latitude = self.request.POST.get('latitude')
            longitude = self.request.POST.get('longitude')
            geo_point = ndb.GeoPt(latitude, longitude)
        except:
            is_form_valid = False

        if not name or not about_you or not is_valid_email(email):
            is_form_valid = False

        # TODO: Check for email already in db (save in lowercase)

        if not is_form_valid:
            self.response.set_status(400)
            self.response.out.write("")
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
            communities = communities_list,
            point = geo_point,
            access_uuid = access_uuid,
            user_ip_address = user_ip_address,
        )
        new_pin.put()
        send_activate_email(email, access_uuid)

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

def send_activate_email(recipient, access_uuid):
    return

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


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', CreatePinHandler),
    ('/pin/(.*)', PinHandler),
    ('/pins', PinsHandler),
], debug=True)
