#doubi beta 0.1

import jinja2
import os
import webapp2
import re
import json
import logging

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb

# msgs: Msg entities
def get_msgs_json(msgs):
	tmp = []
	for msg in msgs:
		tmp.append({
			'name': msg.author.nickname(),
			'vote': msg.vote,
			'data': str(msg.date),
			'content': msg.content
			})
	return json.dumps(tmp)


def query_msgs():
	msg_query = Msg.query().order(-Msg.date)
	return msg_query.fetch(10)

def send_json(json):


	qo = ndb.QueryOptions(read_policy=ndb.EVENTUAL_CONSISTENCY)
	channels = Channel.query(default_options=qo)
	
	# currently sending updates to all the channels
	# including the used one to avoid cases where 
	# newly enabled channel is not updated yet in 
	# the datastore when query the avaliable 
	# channels. 
	for ch in channels:
			channel.send_message(ch.token,  json)


class Channel(ndb.Model):
	token = ndb.StringProperty()
	used = ndb.BooleanProperty()


class Player(ndb.Model):
	name = ndb.StringProperty()
	symbols = ndb.StringProperty()
	level = ndb.IntegerProperty()


class Msg(ndb.Model):
	author = ndb.UserProperty()
	vote = ndb.IntegerProperty()
	date = ndb.DateTimeProperty(auto_now_add=True)
	content = ndb.StringProperty(indexed=False)


### TODO 
# try to encrypt this
# tokens need to be kept secret
class OpenChannel(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user:
			ch = Channel.query(Channel.used == False).get()
			if ch:
				token = ch.token
				ch.put()
			else:
				uuid = self.request.get("uid")
				token = channel.create_channel(uuid)

				# Question: some how for the 3rd I 
				# have to set it to true
				# even if it's set to true in 
				# the ChannelConnected handler
				# seems that in ChannelOpened handler
				# a stale value is read
				Channel(key=ndb.Key(Channel,uuid), token=token,used=True).put()

			self.response.content_type="text/plain"
			self.response.write(token)


class MainPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()

		email = "Anonymous"

		# logging.info(self.request.get("channel_token"))

		logged = None

		if user:
			url_linktext = "Logout"
			url = users.create_logout_url(self.request.url)
			email = user.email()
			logged = True

		else:
			url_linktext = "Login"
			url = users.create_login_url(self.request.url)

		template_values = {
			'logged': logged,
			'my_email': email,
			'url_linktext': url_linktext,
			'url': url
		}
		
		template = JINJA_ENVIRONMENT.get_template("index.html")
		self.response.write(template.render(template_values))


class AddMsg(webapp2.RequestHandler):

	def post(self):

		user = users.get_current_user()

		if user:
			msg = Msg()
			if users.get_current_user():
				msg.author = users.get_current_user()

			msg.content = self.request.get('content')

			send_json(get_msgs_json([msg] + query_msgs()))
			msg.put()

		else:
			self.redirect(users.create_login_url())



class ChannelOpened(webapp2.RequestHandler):
	def post(self):
		send_json(get_msgs_json(query_msgs()))

class ChannelDisconnected(webapp2.RequestHandler):

	def post(self):
		client_id = self.request.get('from')
		if client_id:
			ch = ndb.Key(Channel, client_id).get()
			ch.used = False
			ch.put()
			

class ChannelConnected(webapp2.RequestHandler):

	def post(self):

		logging.info("Channel connected!!")

		client_id = self.request.get('from')
		if client_id:
			ch = ndb.Key(Channel, client_id).get()
			ch.used = True
			ch.put()

		

# cron job that deletes the expired channels
# cron job:
# https://cloud.google.com/appengine/docs/python/config/cron
class Clean(webapp2.RequestHandler):
	def get(self):
		Channel.query().map(lambda x: x.delete(), keys_only=True)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/add_msg', AddMsg),
    ('/_ah/channel/disconnected/', ChannelDisconnected),
    ('/_ah/channel/connected/', ChannelConnected),
    ('/tasks/clean', Clean),
    ('/opened', ChannelOpened),
    ('/open', OpenChannel)
    ], debug=True)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)