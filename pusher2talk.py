import os
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
import pusher
import hmac
import hashlib
import memcache
import json
from cherrypy.process import servers


mc = memcache.Client(['127.0.0.1:12111'], debug=0)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
settings.configure(TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT,'static/')))

def fake_wait_for_occupied_port(host, port): 
	return

servers.wait_for_occupied_port = fake_wait_for_occupied_port

#Twilio Details
account = os.environ["twilio_account"]
token = os.environ["twilio_token"]
application_sid = os.environ["twilio_application_sid"]

#Pusher Details
pusher.app_id = os.environ["pusher_app_id"]
pusher.key = os.environ["pusher_key"]
pusher.secret = os.environ["pusher_secret"]


def adduser(room, user):
	mcresp = mc.get(room)
	if mcresp != None:
		data = json.loads(mcresp)
		data['users'].append(user)
		mc.set(room, json.dumps(data))
	else:
		data = {}
		data['users'] = []
		data['users'].append(user)
		mc.set(room, json.dumps(data))

def deluser(room, user):
	data = json.loads(mc.get(room))
	data['users'].remove(user)
	mc.set(room, json.dumps(data))
def getusers(room):
	data = json.loads(mc.get(room))
	return data
	



class twiliotest(object):
	def start(self, var=None, **params):
		r = twiml.Response()
		r.say("Please record a short message after the tone, it will then be played back to you")
		r.record(action="http://voxirc.sammachin.com/twiliotest/recorded", maxLength="6")
		return str(r)
	def recorded(self, var=None, **params):
		r = twiml.Response()
		r.say("Thankyou")
		r.play(url=str(urllib.unquote(cherrypy.request.params['RecordingUrl'])))
		r.say("Goodbye")
		return str(r)
	start.exposed = True
	recorded.exposed = True
		
		
		
class start(object):
	twiliotest = twiliotest()
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
		channel_data = {'user_id': socket_id}
		channel_data['user_info'] = {'user':user}
		p = pusher.Pusher(app_id=creds.pusher_app_id, key=creds.pusher_key, secret=creds.pusher_secret)
		auth = p[channel_name].authenticate(socket_id, channel_data)
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
		if room == "welcome-test" and user == "guest-test":
			r = twiml.Response()
			r.say("Please record a short message after the tone, it will then be played back to you")
			r.record(action="http://voxirc.sammachin.com/twiliotest/recorded", maxLength="6")
		else:
			print user + " entered " + room
			leaveurl= "http://ec2.sammachin.com/pusher2talk/leaveroom?room={0}&user={1}".format(room, user)
			c = twiml.Conference(room, waitUrl="", beep="false")
			r = twiml.Response()
			d = twiml.Dial(action=leaveurl)
			d.append(c)
			r.append(d)
			p = pusher.Pusher()
			p["presence-"+room].trigger('join', {'user' : user})
			adduser(room, user)
		return str(r)
	def leaveroom(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		user = str(urllib.unquote(cherrypy.request.params['user']))
		p = pusher.Pusher()
		p["presence-"+room].trigger('leave', {'user' : user})
		deluser(room, user)
		return "ok"
	def getusers(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		data = getusers(room)
		cherrypy.response.headers['content-type'] = "application/json"
		return json.dumps(data)
	def recorded(self, var=None, **params):
		r = twiml.Response()
		r.say("Thankyou")
		r.play(url=str(urllib.unquote(cherrypy.request.params['RecordingUrl'])))
	def test(self, var=None, **params):
		room = str(urllib.unquote(cherrypy.request.params['room']))
		user = str(urllib.unquote(cherrypy.request.params['user']))
		capability = TwilioCapability(account, token)
		capability.allow_client_outgoing(application_sid)
		template_values = {"token": capability.generate(), "room" : room, "user": user}
		t = loader.get_template('test.html')
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


		
cherrypy.config.update({'server.socket_host': '0.0.0.0',})
cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', '5000')),})
cherrypy.quickstart(HelloWorld())
