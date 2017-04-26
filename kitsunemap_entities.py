from google.appengine.ext import ndb

class Pin(ndb.Model):
    #use entity key for acticvation
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
