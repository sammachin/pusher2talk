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
import memcache
import json

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

settings.configure(TEMPLATE_DIRS = ( "/server/pusher2talk/static",))

#Twilio Details
account = creds.twilio_account
token = creds.twilio_token
application_sid = creds.twilio_application_sid

#Pusher Details
pusher.app_id = creds.pusher_app_id
pusher.key = creds.pusher_key
pusher.secret = creds.pusher_secret


def adduser(room, user):
	data = json.loads(mc.get(room))
	data['users'].append(user)
	mc.set(room, json.dumps(data))

def deluser(room, user):
	data = json.loads(mc.get(room))
	data['users'].remove(user)
	mc.set(room, json.dumps(data))
def getusers(room):
	data = json.loads(mc.get(room))
	return data


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
		user = str(urllib.unquote(cherrypy.request.params['user']))
		channel_data = {}
		channel_data['user'] = user
		p = pusher.Pusher(app_id=creds.pusher_app_id, key=creds.pusher_key, secret=creds.psuher_secret)
		auth = p[channel_name].authenticate(socket_id, json.dumps(channel_data))
		json_data = json.dumps(auth)
		cherrypy.response.headers['content-type'] = "application/json"
		return json.dumps(auth)
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
	def main(self, var=None, **params):
		clientid = urllib.unquote(cherrypy.request.params['id'])
		room = clientid.split(".")[0]
		user = clientid.split(".")[1]
		capability = TwilioCapability(account, token)
		capability.allow_client_outgoing(application_sid)
		template_values = {"token": capability.generate(), "room" : room, "user": user}
		t = loader.get_template('mainclient.html')
		c = Context(template_values)
		return t.render(c)
	def joinroom(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		user = str(urllib.unquote(cherrypy.request.params['user']))
		print user + " entered " + room
		leaveurl= "http://ec2.sammachin.com/pusher2talk/leaveroom?room={0}&user={1}".format(room, user)
		c = twiml.Conference(room, waitUrl="", beep="false")
		r = twiml.Response()
		d = twiml.Dial(action=leaveurl)
		d.append(c)
		r.append(d)
		p = pusher.Pusher()
		p["private-"+room].trigger('join', {'user' : user})
		adduser(room, user)
		return str(r)
	def leaveroom(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		user = str(urllib.unquote(cherrypy.request.params['user']))
		p = pusher.Pusher()
		p["private-"+room].trigger('leave', {'user' : user})
		deluser(room, user)
		return "ok"
	def getusers(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		data = getusers(room)
		cherrypy.response.headers['content-type'] = "application/json"
		return json.dumps(data)
	def test(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		user = str(urllib.unquote(cherrypy.request.params['user']))
		template_values = {"room": room, "user" : user}
		t = loader.get_template('listtest.html')
		c = Context(template_values)
		return t.render(c)
	index.exposed = True
	main.exposed = True
	test.exposed = True			
	clienttoken.exposed = True
	pusherauth.exposed = True
	joinroom.exposed = True
	leaveroom.exposed = True
	getusers.exposed = True


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

