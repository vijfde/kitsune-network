import httplib2
import urllib

import webapp2

import credentials
from utilities import send_email

class SendDiscordWebHookHandler(webapp2.RequestHandler):
    def post(self):
        content = self.request.get('message')
        content = content.encode('utf-8', 'ignore')
        data = { 'content': content }
        http = httplib2.Http()
        url = credentials.DISCORD_WEB_HOOK_URL
        resp, content = http.request(url, 'POST', urllib.urlencode(data))
        self.response.set_status(resp.status)

class SendEditEmailHandler(webapp2.RequestHandler):
    def post(self):
        email = self.request.get('email')
        access_uuid = self.request.get('access_uuid')
        send_email(email, access_uuid, True)
        self.response.set_status(200)

app = webapp2.WSGIApplication([
    ('/tasks/send_discord_web_hook', SendDiscordWebHookHandler),
    ('/tasks/send_edit_email', SendEditEmailHandler),
], debug=True)
