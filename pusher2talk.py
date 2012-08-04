import re
import cherrypy
import urllib
import random
import simplejson
from django.template import Template, Context, loader
from django.conf import settings
from twilio import twiml
from twilio.rest import TwilioRestClient
import time
import json
import urllib2
from twilio.util import TwilioCapability
import creds
import pusher
import hmac
import hashlib



settings.configure(TEMPLATE_DIRS = ( "/server/pusher2talk/static",))

#Twilio Details
account = creds.twilio_account
token = creds.twilio_token
application_sid = creds.twilio_application_sid

#Pusher Details
pusher.app_id = creds.pusher_app_id
pusher.key = creds.pusher_key
pusher.secret = creds.pusher_secret

					
class start(object):
	def index(self):
		template_values = {}
		t = loader.get_template('index.html')
		c = Context(template_values)
		return t.render(c)
	def clienttoken(self, var=None, **params):
		clientid = urllib.unquote(cherrypy.request.params['clientid'])
		room = clientid.split(".")[0]
		user = clientid.split(".")[1]
		capability = TwilioCapability(account, token)
		capability.allow_client_outgoing(application_sid)
		return capability.generate()
	def pusherauth(self, var=None, **params):
		socket_id = urllib.unquote(cherrypy.request.params['socket_id'])
		channel_name = urllib.unquote(cherrypy.request.params['channel_name'])
		string_to_sign = socket_id + ":" + channel_name
		sig = hmac.new(pusher.secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
		data = {}
		data['auth'] = pusher.key + ":" + sig
		cherrypy.response.headers['content-type'] = "application/json"
		return json.dumps(data)
	def twilio(self, var=None, **params):
		clientid = urllib.unquote(cherrypy.request.params['id'])
		room = clientid.split(".")[0]
		user = clientid.split(".")[1]
		capability = TwilioCapability(account, token)
		capability.allow_client_outgoing(application_sid)
		template_values = {"token": capability.generate(), "room" : room, "user": user}
		t = loader.get_template('twilioclient.html')
		c = Context(template_values)
		return t.render(c)
	def pusher(self, var=None, **params):
		clientid = urllib.unquote(cherrypy.request.params['id'])
		room = clientid.split(".")[0]
		user = clientid.split(".")[1]
		template_values = {"room": room, "user" : user}
		t = loader.get_template('pushertest.html')
		c = Context(template_values)
		return t.render(c)
	def joinroom(self, var=None, **params):
		room = urllib.unquote(cherrypy.request.params['room'])
		user = urllib.unquote(cherrypy.request.params['user'])
		print user + " entered " + room
		leaveurl= "http://ec2.sammachin.com/pusher2talk/leaveroom?room={0}&user={1}".format(room, user)
		c = twiml.Conference(room)
		r = twiml.Response()
		d = twiml.Dial(action=leaveurl)
		d.append(c)
		r.append(d)
#		p = pusher.Pusher()
#		p[room].trigger('join', {'user' : user})
		return str(r)
	def leaveroom(self, var=None, **params):
		room = urllib.unquote(cherrypy.request.params['room'])
		user = urllib.unquote(cherrypy.request.params['user'])
#		p = pusher.Pusher()
#		p[room].trigger('leave', {'user' : user})
		return "ok"
	index.exposed = True
	twilio.exposed = True
	pusher.exposed = True			
	clienttoken.exposed = True
	pusherauth.exposed = True
	joinroom.exposed = True
	leaveroom.exposed = True



cherrypy.config.update('app.cfg')
app = cherrypy.tree.mount(start(), '/', 'app.cfg')
cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 9041})

if hasattr(cherrypy.engine, "signal_handler"):
    cherrypy.engine.signal_handler.subscribe()
if hasattr(cherrypy.engine, "console_control_handler"):
    cherrypy.engine.console_control_handler.subscribe()
cherrypy.engine.start()
cherrypy.engine.block()

