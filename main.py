import webapp2
import os
import jinja2
import json
import base64
import uuid

from entities import Pin
from utilities import send_email
import constants

from babel.support import Translations
from google.appengine.api import taskqueue

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        show_modal_onload = False
        activate_pin_uuid = self.request.GET.get('activatePin')
        if activate_pin_uuid != None:
            if Pin.activate_pin(activate_pin_uuid):
                show_modal_onload = True
                template_values["show_pin_activated_message"] = True
                template_values["force_refresh_pins"] = True
            else:
                self.redirect('/')
                return
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
            else:
                self.redirect('/')
                return
        template_values["show_modal_onload"] = show_modal_onload
        template_values["cookie_language"] = self.request.cookies.get('language')
        template_values["languages_dict"] = constants.languages
        template_values["languages_display_sort"] = constants.languages_display_sort
        template = JINJA_ENVIRONMENT.get_template('templates/map.html')
        setup_i18n(self.request)
        self.response.write(template.render(template_values))

def get_translations(request):
    cookie_language = request.cookies.get('language')
    if cookie_language:
        list_of_desired_locales = cookie_language
    else:
        header = request.headers.get('Accept-Language', '')  # e.g. en-gb,en;q=0.8,es-es;q=0.5,eu;q=0.3
        list_of_desired_locales = [locale.split(';')[0] for locale in header.split(',')]
        if "en" in list_of_desired_locales:
            list_of_desired_locales = None
    locale_dir = "locales"
    translations = Translations.load(locale_dir, list_of_desired_locales)
    return translations

def setup_i18n(request):
    translations = get_translations(request)
    JINJA_ENVIRONMENT.install_gettext_translations(translations)

def add_constants(template_values):
    template_values["pin_icons"] = constants.pin_icons
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
        # self.response.headers["cache-control"] = "max-age=600"
        self.response.out.write(json.dumps(pins_dict))

class NewPinFormHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        add_constants(template_values)
        template = JINJA_ENVIRONMENT.get_template('templates/pin/new_pin_form.html')
        setup_i18n(self.request)
        self.response.write(template.render(template_values))

class PinInfoHandler(webapp2.RequestHandler):
    def get(self, pin_id):
        pin = Pin.get_by_id(int(pin_id))
        if pin == None:
            self.response.set_status(404)
            self.response.out.write("")
            return
        communities = pin.communities.split(',')
        if len(communities) > 1 and '0' in communities:
            communities.remove('0')
        template_values = {
            'pin': pin,
            'fav_song': constants.songs[str(pin.favorite_song)],
            'fav_member': constants.members[str(pin.favorite_member)],
            'communities': [constants.communities[community] for community in communities],
        }
        template = JINJA_ENVIRONMENT.get_template('templates/pin_info_window.html')
        setup_i18n(self.request)
        # self.response.headers["cache-control"] = "max-age=600"
        self.response.write(template.render(template_values))

class PinEditRequestHandler(webapp2.RequestHandler):
    def post(self):
        email = self.request.POST.get('email')
        edit_pin = Pin.query(Pin.email == email).get()
        if edit_pin and edit_pin.is_activated:
            edit_pin.access_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
            edit_pin.put()
            task = taskqueue.add(
                url = '/tasks/send_edit_email',
                params = { 'email': edit_pin.email, 'access_uuid': edit_pin.access_uuid })
        template_values = { 'action': 'edit' }
        template = JINJA_ENVIRONMENT.get_template('templates/email_sent.html')
        setup_i18n(self.request)
        self.response.write(template.render(template_values))

class ManagePinHandler(webapp2.RequestHandler):
    def put(self):
        edit_pin_uuid = self.request.POST.get('editAccessUUID')
        pin = Pin.query(Pin.access_uuid == edit_pin_uuid).get()
        if pin == None:
            self.response.set_status(404)
            self.response.out.write("")
            return

        translations = get_translations(self.request)
        form_error_message = Pin.validate_pin_values(self.request.POST, False, translations)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        pin.set_pin_values(self.request.POST, self.request.remote_addr, False, translations)
        pin.send_discord_moderation_web_hook()

        template = JINJA_ENVIRONMENT.get_template('templates/pin_updated.html')
        setup_i18n(self.request)
        self.response.write(template.render())

    def post(self):
        translations = get_translations(self.request)
        form_error_message = Pin.validate_pin_values(self.request.POST, True, translations)
        if form_error_message:
            self.response.set_status(400)
            self.response.out.write(form_error_message)
            return

        new_pin = Pin()
        new_pin.set_pin_values(self.request.POST, self.request.remote_addr, True, translations)

        send_email(new_pin.email, new_pin.access_uuid, False)

        template_values = { 'action': 'activate' }
        template = JINJA_ENVIRONMENT.get_template('templates/email_sent.html')
        setup_i18n(self.request)
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/pin', ManagePinHandler),
    ('/pin/editRequest', PinEditRequestHandler),
    ('/pin/(.*)', PinInfoHandler),
    ('/pins.json', PinsHandler),
    ('/new_pin_form.html', NewPinFormHandler),
], debug=True)
