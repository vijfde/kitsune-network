import httplib2
import urllib

import webapp2

import credentials
from utilities import send_email

class SendDiscordWebHookHandler(webapp2.RequestHandler):
    def post(self):
        send_discord_web_hook(self, credentials.DISCORD_WEB_HOOK_URL)

class SendDiscordModerationWebHookHandler(webapp2.RequestHandler):
    def post(self):
        send_discord_web_hook(self, credentials.DISCORD_MODERATION_WEB_HOOK_URL)

def send_discord_web_hook(request_handler, web_hook_URL):
    content = request_handler.request.get('message')
    content = content.encode('utf-8', 'ignore')
    data = { 'content': content }
    http = httplib2.Http()
    resp, content = http.request(web_hook_URL, 'POST', urllib.urlencode(data))
    request_handler.response.set_status(resp.status)

class SendEditEmailHandler(webapp2.RequestHandler):
    def post(self):
        email = self.request.get('email')
        access_uuid = self.request.get('access_uuid')
        send_email(email, access_uuid, True)
        self.response.set_status(200)

app = webapp2.WSGIApplication([
    ('/tasks/send_discord_web_hook', SendDiscordWebHookHandler),
    ('/tasks/send_discord_moderation_web_hook', SendDiscordModerationWebHookHandler),
    ('/tasks/send_edit_email', SendEditEmailHandler),
], debug=True)
