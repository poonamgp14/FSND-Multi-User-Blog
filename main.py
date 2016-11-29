import webapp2
import jinja2
import os
from google.appengine.api import users
import BlogDB
from urlparse import urlparse
from google.appengine.ext import ndb
import random
import string
import hashlib
import hmac

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir)
									,autoescape= True)

secret = 'Haeligmatin'

class handler(webapp2.RequestHandler):
	"""This is the handler class for handling jinja2 template"""

	def write(self,*a,**kw):
		"""This will write response back to our browser(client)"""
		self.response.out.write(*a,**kw)

	#functions for rendering basic templates
	def render_str(self,template,**params):
		"""This calls jinja template we specify and
		returns template in form of a string.
		"""
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self,template, **kw):
		"""Main method to call from get methods"""
		self.write(self.render_str(template,**kw))

	def makeSalt(self):
		return ''.join(random.choice(string.letters) for x in range(5))

	def makePwHash(self,name,pw,salt=None):
		if not salt:
			salt = self.makeSalt()
		h = hashlib.sha256(name+pw+salt).hexdigest()
		return '%s,%s' % (h,salt)

	#check at the time of login
	def validPw(self,name, pw, h):
		salt = h.split(',')[1]
		#print(h == self.makePwHash(name,pw,salt))
		return h == self.makePwHash(name,pw,salt)

	def make_secure_val(self,val):
		return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

	def check_secure_val(self,secure_val):
		val = secure_val.split('|')[0]
		return secure_val == self.make_secure_val(val)
		#return val

	def evaluateCookie(self, cookieName):
		self.cookie_val = self.request.cookies.get(cookieName)
		#return cookie_val and self.check_secure_val(cookie_val)
		return self.check_secure_val(self.cookie_val)


	def renderAllPosts(self,username):
		blogsList = []
		self.posts = BlogDB.Posts.query().order(-BlogDB.Posts.createdTime)
		if self.posts:
			for self.post in self.posts:
				self.eachPost = {'user':self.post.username,'content': self.post.content,'date': self.post.createdTime}
				blogsList.append(self.eachPost)
			securedUserName = self.make_secure_val(username)
			print(securedUserName)
			self.response.headers.add_header('Set-Cookie','user=%s' % str(securedUserName))
			self.render("blogPost.html",blogsList=blogsList, user=securedUserName.split('|')[0])

	def handlelogin(self):
		self.loginName = self.request.get("username")
		self.loginpw = self.request.get("password")
		if self.loginName and self.loginpw:
			#check if user already exists
			query = BlogDB.Users.query(ndb.AND(BlogDB.Users.name == self.loginName)).fetch()
			#print(query)
			if query:
				if not self.validPw(self.loginName,self.loginpw,query[0].password):
					self.render("login.html",error='Username and/or password doesnot match with our records')
				else:
					self.renderAllPosts(self.loginName)
			else:
				self.render("login.html",error='Invalid Username')


#implement if user cookie is available then land on welcome page
class HomePage(handler):
	def get(self):
		self.render("home.html")

class SignUp(handler):
	def get(self):
		self.render("signup.html")

class LogIn(handler):
	def get(self):
		self.render("login.html")

class WelcomePage(handler):
	def get(self):
		self.checkUser = self.evaluateCookie('user')
		if not self.checkUser:
			self.render("home.html")
		else:
			self.renderAllPosts(self.request.cookies.get('user').split('|')[0])


	def post(self):
		self.name = self.request.get("usernamesignup")
		if self.name:
			self.email = self.request.get("emailsignup")
			self.pw = self.request.get("passwordsignup")
			self.pwVerify = self.request.get("passwordsignup_confirm")

			if self.name and self.email and self.pw:
				#check if username and email id already exists
				query = BlogDB.Users.query(ndb.AND(BlogDB.Users.name == self.name, BlogDB.Users.email ==self.email)).fetch()
				#print(query)
				if query:
					self.render("signup.html",error='This user already exists')
				else:
					if self.pw == self.pwVerify:
						self.pwHashed = self.makePwHash(self.name,self.pw)
						print(self.pwHashed)
						self.user = BlogDB.Users(name=self.name,
										email=self.email,
										password=self.pwHashed)
						self.postKey = self.user.put()
						self.renderAllPosts(self.name)
					else:
						self.render("signup.html",error='Both of the passwords should be same')
		else:
			self.handlelogin()

class NewBlogForm(handler):
	def get(self):
		self.render("newblogForm.html")

	def post(self):
		self.userName = self.request.get("UserName")
		self.emailId = self.request.get("EmailID")
		self.content = self.request.get("Content")
		if self.userName and self.emailId and self.content:
			self.post = BlogDB.Posts(username=self.userName,
								email=self.emailId,
								content=self.content)
			self.postKey = self.post.put()
			postId = self.postKey.id()
			self.redirect("/%d" % postId)

class NewBlog(handler):
	def get(self):
		url = urlparse(self.request.path)
		newBlog = BlogDB.Posts.get_by_id(int(url[2][1:]))
		self.render("blogPost.html", blogsList=[{'user':newBlog.username,'content': newBlog.content,
								'date': newBlog.createdTime
								}])


app = webapp2.WSGIApplication([
	('/welcome', WelcomePage),
	('/', HomePage),
	('/signup',SignUp),('/login', LogIn),
	('/newBlogForm', NewBlogForm),
	('/[0-9]+',NewBlog)
], debug=True)
