import webapp2
import os
import jinja2
import json
import base64
import uuid

from entities import Pin
from utilities import send_email
import constants

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        show_modal_onload = False
        activate_pin_uuid = self.request.GET.get('activatePin')
        if activate_pin_uuid != None and Pin.activate_pin(activate_pin_uuid):
            show_modal_onload = True
            template_values["show_pin_activated_message"] = True
        edit_pin_uuid = self.request.GET.get('editPin')
        if edit_pin_uuid != None:
            edit_pin = Pin.query(Pin.access_uuid == edit_pin_uuid).get()
            if edit_pin != None:
                show_modal_onload = True
                template_values["edit_pin_uuid"] = edit_pin_uuid
                template_values["pin"] = edit_pin
                template_values["pin_communities"] = [int(x) for x in edit_pin.communities.split(',')]
                add_constants(template_values)
                template_values["show_pin_edit_form"] = True
        template_values["show_modal_onload"] = show_modal_onload
        template = JINJA_ENVIRONMENT.get_template('templates/map.html')
        self.response.write(template.render(template_values))

def add_constants(template_values):
    template_values["songs_dict"] = constants.songs
    template_values["songs_display_sort"] = constants.songs_display_sort
    template_values["members_dict"] = constants.members
    template_values["members_display_sort"] = constants.members_display_sort
    template_values["communities_dict"] = constants.communities
    template_values["communities_display_sort"] = constants.communities_display_sort

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

class NewPinFormHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        add_constants(template_values)
        template = JINJA_ENVIRONMENT.get_template('templates/pin/new_pin_form.html')
        self.response.write(template.render(template_values))

class PinInfoHandler(webapp2.RequestHandler):
    def get(self, pin_id):
        pin = Pin.get_by_id(int(pin_id))
        if pin == None:
            self.response.set_status(404)
            self.response.out.write("")
            return
        communities = pin.communities.split(',')
        if len(communities) > 1:
            communities.remove('0')
        template_values = {
            'pin': pin,
            'fav_song': constants.songs[str(pin.favorite_song)],
            'fav_member': constants.members[str(pin.favorite_member)],
            'communities': [constants.communities[community] for community in communities],
        }
        template = JINJA_ENVIRONMENT.get_template('templates/pin_info_window.html')
        self.response.write(template.render(template_values))

class PinEditRequestHandler(webapp2.RequestHandler):
    def post(self):
        email = self.request.POST.get('email')
        edit_pin = Pin.query(Pin.email == email).get()
        if edit_pin and edit_pin.is_activated:
            edit_pin.access_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
            edit_pin.put()
            send_email(edit_pin.email, edit_pin.access_uuid, True)
        template_values = { 'action': 'edit' }
        template = JINJA_ENVIRONMENT.get_template('templates/email_sent.html')
        self.response.write(template.render(template_values))

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

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', ManagePinHandler),
    ('/pin/editRequest', PinEditRequestHandler),
    ('/pin/(.*)', PinInfoHandler),
    ('/pins', PinsHandler),
    ('/new_pin_form.html', NewPinFormHandler),
], debug=True)
