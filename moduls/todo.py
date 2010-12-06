import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from datetime import datetime

# print stack traces, etc
_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):
	"""Supplies a common template generation function.

	When you call generate(), we augment the template variables supplied with
	the current user in the 'user' variable and the current webapp request
	in the 'request' variable.
	"""
	def generate(self, template_name, template_values={}):
		values = {
			'request': self.request,
			'user': users.get_current_user(),
			'login_url': users.create_login_url(self.request.uri),
			'logout_url': users.create_logout_url('http://%s/' % (
				self.request.host,)),
			'debug': self.request.get('deb'),
			'application_name': 'Time - Management',}
		values.update(template_values)
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, os.path.join('../templates', template_name))
		self.response.out.write(template.render(path, values, debug=_DEBUG))

class List(db.Model):
	author = db.UserProperty()
	name = db.StringProperty(multiline=False)

class ListItem(db.Model):
	list = db.ReferenceProperty(List)
	text = db.StringProperty(multiline=False)
	done = db.BooleanProperty()
	date = db.DateTimeProperty(auto_now_add=True)

class MainPage(BaseRequestHandler):
	def get(self):
		user = users.get_current_user()
		lists = db.GqlQuery("SELECT * FROM List WHERE author = :1 ORDER BY name", user)
		
		self.generate('todo/todo_main.html', {
			'lists': lists,
		})

class ToDoList(webapp.RequestHandler):
	def post(self):
		list = List(author= users.get_current_user(),
								name= self.request.get('name'))
		list.put()
		self.redirect('/todo')

class ListPage(BaseRequestHandler):
	def get(self):
		
		list = db.get(self.request.get('key'))
		open_items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = false", list)
		done_items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = true", list)
		
		template_values = {
					'list': list,
					'open_items': open_items,
					'done_items': done_items,
					}
		
		self.generate('todo/todo_list.html',template_values)

	def post(self):
		item = ListItem(text = self.request.get('text'),
										list = db.get(self.request.get('list_key')),
										done = False)
		item.put()
		self.redirect('/todo/list?key=%s' % self.request.get('list_key'))

class CheckItem(webapp.RequestHandler):
	def post(self):
		item = db.get(self.request.get('key'))
		if (self.request.get('done') == 'true'):
			item.done = True
		else:
			item.done = False
		item.date = datetime.now()
		item.put()
		
		if item.done:
			items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = true", item.list)
		else:
			items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = false", item.list)
		
		template_values = {
					'items': items,
					'done': item.done,
					}

		path = os.path.join(os.path.dirname(__file__), '../templates/todo/todo_item_list.html')
		self.response.out.write(template.render(path, template_values))

class DeleteItem(webapp.RequestHandler):
	def get(self):
		item = db.get(self.request.get('key'))
		list = item.list
		item.delete()
		
		self.redirect('/todo/list?key=%s' % list.key())
		

class DeleteList(webapp.RequestHandler):
	def get(self):
		
		list = db.get(self.request.get('key'))
		items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1", list)
		list.delete()
		db.delete(items)
		self.redirect('/todo')

application = webapp.WSGIApplication(
									 [('/todo', MainPage),
										('/todo/list', ListPage),
										('/todo/checkitem', CheckItem),
										('/todo/deleteitem', DeleteItem),
										('/todo/deletelist', DeleteList),
										('/todo/newlist', ToDoList)],
									 debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()