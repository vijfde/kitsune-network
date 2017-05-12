import base64
import uuid

from google.appengine.ext import ndb
from google.appengine.api import taskqueue

import constants
from utilities import is_valid_email, is_real_email, is_spam_email

class Pin(ndb.Model):
    created_datetime = ndb.DateTimeProperty(auto_now_add=True,indexed=True,required=True)
    email = ndb.StringProperty(required=True)
    user_ip_address = ndb.StringProperty(required=True)
    access_uuid = ndb.StringProperty(required=True)
    is_activated = ndb.BooleanProperty(required=True,indexed=True,default=False)
    point = ndb.GeoPtProperty(required=True)

    name = ndb.StringProperty(required=True)
    about_you = ndb.TextProperty(required=True)
    pin_icon = ndb.IntegerProperty(required=True)
    favorite_member = ndb.IntegerProperty(required=True)
    favorite_song = ndb.IntegerProperty(required=True)
    communities = ndb.StringProperty(required=True)

    def send_discord_web_hook(self):
        pin_details = 'Title: ' + self.name
        pin_details += '\nFav Song: ' + constants.songs[str(self.favorite_song)]
        pin_details += '\nFav Member: ' + constants.members[str(self.favorite_member)]
        communities = self.communities.split(',')
        if len(communities) > 1 and '0' in communities:
            communities.remove('0')
        pin_details += '\nCommunities: ' + ', '.join([constants.communities[str(community)] for community in communities])
        pin_details += '\nAbout: \n' + self.about_you
        content = """**New Pin Activated!**```%s```""" % pin_details
        task = taskqueue.add(
            url = '/tasks/send_discord_web_hook',
            params = { 'message': content })

    def send_discord_moderation_web_hook(self):
        pin_details = 'ID: ' + str(self.key.id())
        pin_details += '\nIP: ' + self.user_ip_address
        pin_details += '\nEmail: ' + self.email
        pin_details += '\nTitle: ' + self.name
        pin_details += '\nCommunities: ' + self.communities
        pin_details += '\nAbout: \n' + self.about_you
        content = """**Pin Putted**```%s```""" % pin_details
        task = taskqueue.add(
            url = '/tasks/send_discord_moderation_web_hook',
            params = { 'message': content })

    def _post_put_hook(self, future):
        self.send_discord_moderation_web_hook()

    @classmethod
    def validate_pin_values(cls, request_values, is_new_pin, translations):
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
                form_error_message = translations.gettext("All fields are required.")
            elif is_new_pin and (not is_valid_email(email) or not is_real_email(email) or is_spam_email(email)):
                form_error_message = translations.gettext("A valid email address is required.")
            elif is_new_pin and Pin.query(Pin.email == email).get():
                form_error_message = translations.gettext("A pin already exists for this email address.")
        except:
            form_error_message = translations.gettext("All fields are required.")

        return form_error_message

    def set_pin_values(self, request_values, remote_addr, is_new_pin, translations):
        if Pin.validate_pin_values(request_values, is_new_pin, translations):
            return
        self.name = request_values.get('name').strip()
        self.about_you = request_values.get('about_you').strip()
        self.pin_icon = int(request_values.get('pin_icon'))
        self.favorite_member = int(request_values.get('favorite_member'))
        self.favorite_song = int(request_values.get('favorite_song'))
        self.communities = request_values.get('communities')
        self.user_ip_address = remote_addr
        if is_new_pin:
            self.access_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
            self.email = request_values.get('email').strip()
            latitude = request_values.get('latitude')
            longitude = request_values.get('longitude')
            self.point = ndb.GeoPt(latitude, longitude)
        else:
            self.access_uuid = ""
        self.put()

    @classmethod
    def activate_pin(cls, activate_pin_uuid):
        ''' Activate a pin, returns if the activation was a success '''
        pin = Pin.query(Pin.access_uuid == activate_pin_uuid).get()
        if not pin:
            return False
        pin.is_activated = True
        pin.access_uuid = ""
        pin.put()
        pin.send_discord_web_hook()
        return True
