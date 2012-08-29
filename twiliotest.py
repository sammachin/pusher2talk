from twilio import twiml
import cherrypy
import urllib

class start(object):
	def start(self, var=None, **params):
		raise cherrypy.HTTPRedirect("go", 307)
	def go(self, var=None, **params):
		r = twiml.Response()
		r.say("Please record a short message after the tone, it will then be played back to you")
		r.record(action="http://ec2.sammachin.com/twiliotest/recorded", maxLength="6")
		return str(r)
	def recorded(self, var=None, **params):
		r = twiml.Response()
		r.say("Thankyou")
		r.play(url=str(urllib.unquote(cherrypy.request.params['RecordingUrl'])))
		r.say("Goodbye")
		return str(r)
	start.exposed = True
	recorded.exposed = True
	go.exposed = True

cherrypy.config.update('app.cfg')
app = cherrypy.tree.mount(start(), '/', 'app.cfg')
cherrypy.config.update({'server.socket_host': '0.0.0.0',	
                        'server.socket_port': 9043})

if hasattr(cherrypy.engine, "signal_handler"):
	cherrypy.engine.signal_handler.subscribe()
if hasattr(cherrypy.engine, "console_control_handler"):
	cherrypy.engine.console_control_handler.subscribe()
cherrypy.engine.start()
cherrypy.engine.block()
