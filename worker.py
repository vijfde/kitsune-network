import httplib2
import urllib

import webapp2

import credentials
from kitsunemap_entities import Pin

class UpdatePinsJsonHandler(webapp2.RequestHandler):
    def post(self):
        self.response.set_status(200)
        return
        # new_pin_id = int(self.request.get('pin_id'))
        #
        # pin_dicts = []
        # has_new_pin = False
        # for pin in Pin.query(Pin.is_activated == True).fetch():
        #     pin_id = pin.key.id()
        #     if pin_id == new_pin_id:
        #         has_new_pin = True
        #     pin_dict = {}
        #     pin_dict["id"] = pin_id
        #     pin_dict["icon"] = pin.pin_icon
        #     pin_dict["lat"] = pin.point.lat
        #     pin_dict["lng"] = pin.point.lon
        #     pin_dicts.append(pin_dict)
        #
        # if not has_new_pin:
        #     # the new pin is missing from the list
        #     self.response.set_status(404)
        #     return
        #
        # data = json.dumps(pins_dict)
        #
        # bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        # with gcs.open('/' + bucket_name + '/pins.json') as cloudstorage_file:
        #     pins = cloudstorage_file.read()

class SendDiscordWebHookHandler(webapp2.RequestHandler):
    def post(self):
        content = self.request.get('message')
        content = content.encode('utf-8', 'ignore')
        data = { 'content': content }
        http = httplib2.Http()
        url = credentials.DISCORD_WEB_HOOK_URL
        resp, content = http.request(url, 'POST', urllib.urlencode(data))
        self.response.set_status(resp.status)

app = webapp2.WSGIApplication([
    ('/update_pins_json', UpdatePinsJsonHandler),
    ('/tasks/send_discord_web_hook', SendDiscordWebHookHandler),
], debug=True)
