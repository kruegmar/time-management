import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from datetime import datetime

class List(db.Model):
	author = db.UserProperty()
	name = db.StringProperty(multiline=False)

class ListItem(db.Model):
	list = db.ReferenceProperty(List)
	text = db.StringProperty(multiline=False)
	done = db.BooleanProperty()
	date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
	def get(self):
		greeting = ""
		user = users.get_current_user()
		if user:
			greeting = ("Hallo, %s! (<a href=\"%s\">abmelden</a>)" % (user.nickname(), users.create_logout_url("/")))
		else:
			self.redirect(users.create_login_url(self.request.uri))

		lists = db.GqlQuery("SELECT * FROM List WHERE author = :1 ORDER BY name", user)
			
		template_values = {
					'greeting': greeting,
					'lists': lists,
					}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
		self.response.out.write(template.render(path, template_values))

class ToDoList(webapp.RequestHandler):
	def post(self):
		list = List(author= users.get_current_user(),
								name= self.request.get('name'))
		list.put()
		self.redirect('/')

class ListPage(webapp.RequestHandler):
	def get(self):
		
		list = db.get(self.request.get('key'))
		open_items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = false", list)
		done_items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1 AND done = true", list)
		
		template_values = {
					'list': list,
					'open_items': open_items,
					'done_items': done_items,
					}
		
		path = os.path.join(os.path.dirname(__file__), 'templates/list.html')
		self.response.out.write(template.render(path, template_values))

	def post(self):
		item = ListItem(text = self.request.get('text'),
										list = db.get(self.request.get('list_key')),
										done = False)
		item.put()
		self.redirect('/list?key=%s' % self.request.get('list_key'))

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

		path = os.path.join(os.path.dirname(__file__), 'templates/_item_list.html')
		self.response.out.write(template.render(path, template_values))

class DeleteItem(webapp.RequestHandler):
	def get(self):
		item = db.get(self.request.get('key'))
		list = item.list
		item.delete()
		
		self.redirect('/list?key=%s' % list.key())
		

class DeleteList(webapp.RequestHandler):
	def get(self):
		
		list = db.get(self.request.get('key'))
		items = db.GqlQuery("SELECT * FROM ListItem WHERE list = :1", list)
		list.delete()
		db.delete(items)
		self.redirect('/')

application = webapp.WSGIApplication(
																		 [('/', MainPage),
																			('/list', ListPage),
																			('/checkitem', CheckItem),
																			('/deleteitem', DeleteItem),
																			('/deletelist', DeleteList),
																			('/newlist', ToDoList)],
																		 debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
