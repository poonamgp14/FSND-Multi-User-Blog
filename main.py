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
import time
import ast

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

	def setCookie(self, username):
		securedUserName = self.make_secure_val(username)
		print(securedUserName)
		self.response.headers.add_header('Set-Cookie','user=%s' % str(securedUserName))


#implement if user cookie is available then land on welcome page
class HomePage(handler):
	def get(self):
		self.render("home.html")

class SignUp(handler):
	def get(self):
		self.render("signup.html")

	def post(self):
		self.name = self.request.get("usernamesignup")
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
					self.setCookie(self.name)
					self.redirect('/welcome')
				else:
					self.render("signup.html",error='Both of the passwords should be same')

class LogIn(handler):
	def get(self):
		self.render("login.html")

	def post(self):
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
					self.setCookie(self.loginName)
					self.redirect('/welcome')
			else:
				self.render("login.html",error='Invalid Username')

class Logout(handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'user=')
		self.redirect('/')

class WelcomePage(handler):
	def get(self):
		self.checkUser = self.evaluateCookie('user')
		if not self.checkUser:
			self.render("home.html")
		else:
			self.render("welcome.html",user=self.request.cookies.get('user').split('|')[0])

class BlogPage(handler):
	def get(self):
		blogsList = []
		name = self.request.cookies.get('user').split('|')[0]
		self.posts = BlogDB.Posts.query().order(-BlogDB.Posts.createdTime)
		if self.posts:
			for self.post in self.posts:
				self.eachPost = {
				'user':self.post.username,
				'content': self.post.content,
				'subject': self.post.subject,
				'date': self.post.createdTime,
				'likes':self.post.totalLikes,
				'unlikes': self.post.totalUnlikes,
				'id': self.post.key.id(),
				'isLikable': self.post.isLikable if self.post.username == name or name in self.post.likedBy else True,
				'isUnlikable': self.post.isUnlikable if self.post.username == name or name in self.post.unlikedBy else True,
				'isEditable' : self.post.isEditable if self.post.username == name else False,
				'isDeletable' : self.post.isDeletable if self.post.username == name else False
				}
				blogsList.append(self.eachPost)
			self.render("blogPost.html",blogsList=blogsList, user={'name':name})


class NewBlogForm(handler):
	def get(self):
		self.render("newblogForm.html")

	def post(self):
		self.userName = self.request.cookies.get('user').split('|')[0]
		self.subject = self.request.get("subject")
		self.content = self.request.get("Content")
		if self.userName and self.subject and self.content:
			self.post = BlogDB.Posts(username=self.userName,
								subject=self.subject,
								content=self.content)
			self.post.likedBy = {'hello': 1}
			self.postKey = self.post.put()
			postId = self.postKey.id()
			self.redirect("/blog/%d" % postId)

class NewBlog(handler):
	def get(self):
		url = urlparse(self.request.path)
		newBlog = BlogDB.Posts.get_by_id(int(url[2][6:]))
		name = self.request.cookies.get('user').split('|')[0]
		self.render("blogPostComment.html", blogsList=[
			{
			'user':newBlog.username,
			'content': newBlog.content,
			'subject': newBlog.subject,
			'date': newBlog.createdTime,
			'likes':newBlog.totalLikes,
			'unlikes': newBlog.totalUnlikes,
			'id': newBlog.key.id(),
			'isLikable': newBlog.isLikable if newBlog.username == name or name in newBlog.likedBy else True,
			'isUnlikable': newBlog.isUnlikable if newBlog.username == name or name in newBlog.unlikedBy else True,
			'isEditable' : newBlog.isEditable if newBlog.username == name else False,
			'isDeletable' : newBlog.isDeletable if newBlog.username == name else False
			}],user={'name':name})

	def post(self):
		newContent = self.request.get('newPostContent')
		# print(newContent)
		url = urlparse(self.request.path)
		blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:]))
		blogToUpdate.content = newContent
		blogToUpdate.put()
		time.sleep(.1)
		self.redirect('/blog')

class LikedPost(handler):
	def post(self):
		# query the post with id from url and save the new number of likes
		#rerender the blog url to refresh the whole page
		url = urlparse(self.request.path)
		blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-5]))
		blogToUpdate.totalLikes = blogToUpdate.totalLikes + 1
		blogToUpdate.likedBy[self.request.cookies.get('user').split('|')[0]] = 1
		blogToUpdate.put()
		time.sleep(.1)
		self.redirect('/blog')

class UnlikedPost(handler):
	def post(self):
		url = urlparse(self.request.path)
		blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-7]))
		blogToUpdate.totalUnlikes = blogToUpdate.totalUnlikes + 1
		blogToUpdate.unlikedBy[self.request.cookies.get('user').split('|')[0]] = 1
		blogToUpdate.put()
		time.sleep(.1)
		self.redirect('/blog')

class DeletePost(handler):
	def post(self):
		url = urlparse(self.request.path)
		blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-7]))
		print(blogToUpdate)
		blogToUpdate.key.delete()
		time.sleep(.1)
		self.redirect('/blog')



app = webapp2.WSGIApplication([
	('/welcome', WelcomePage),
	('/', HomePage),
	('/signup',SignUp),('/login', LogIn),
	('/blog/newpost', NewBlogForm),
	('/blog/[0-9]+',NewBlog),('/logout', Logout),('/blog',BlogPage),
	('/blog/[0-9]+/like',LikedPost),('/blog/[0-9]+/unlike',UnlikedPost),
	('/blog/[0-9]+/delete',DeletePost)
], debug=True)
