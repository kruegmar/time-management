import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

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
		path = os.path.join(directory, os.path.join('templates', template_name))
		self.response.out.write(template.render(path, values, debug=_DEBUG))

class MainPage(BaseRequestHandler):
	def get(self):
		self.generate('index.htm', {})
		
class ContactPage(BaseRequestHandler):
	def get(self):
		self.generate('contact.htm', {})
		
class ImprintPage(BaseRequestHandler):
	def get(self):
		self.generate('imprint.htm', {})


application = webapp.WSGIApplication(
										[('/', MainPage),
										('/contact', ContactPage),
										('/imprint', ImprintPage)],
										debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
