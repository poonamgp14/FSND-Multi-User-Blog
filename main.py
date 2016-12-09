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
		# print(self.cookie_val)
		ifUserValid =  self.check_secure_val(self.cookie_val)
		# print(ifUserValid)
		if ifUserValid:
			return self.request.cookies.get('user').split('|')[0]
		else:
			return False

	def setCookie(self, username):
		securedUserName = self.make_secure_val(username)
		self.response.headers.add_header('Set-Cookie','user=%s' % str(securedUserName))

	# def initialize(self, *a, **kw):
	# 	webapp2.RequestHandler.initialize(self, *a, **kw)
	# 	userName = self.evaluateCookie('user')
	# 	if userName:
	# 		self.user = self.request.cookies.get('user').split('|')[0]


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
			if query:
				self.render("signup.html",error='This user already exists')
			else:
				if self.pw == self.pwVerify:
					self.pwHashed = self.makePwHash(self.name,self.pw)
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
			query = BlogDB.Users.query(ndb.AND(
				BlogDB.Users.name == self.loginName)).fetch()
			if query:
				if not self.validPw(self.loginName,self.loginpw,query[0].password):
					self.render("login.html",
						error='Username and/or password doesnot match with our records'
						)
				else:
					self.setCookie(self.loginName)
					self.redirect('/welcome')
			else:
				self.render("login.html",error='Invalid Username')

class Logout(handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'user=')
		self.redirect('/login')

class WelcomePage(handler):
	def get(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			self.render("welcome.html",user=self.user)

class BlogPage(handler):
	def get(self):
		self.checkUser = self.evaluateCookie('user')
		if not self.checkUser:
			self.render("home.html")
		else:
			blogsList = []
			name = self.checkUser
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
					'isLikable': self.post.isLikable if self.post.username == name
								or name in self.post.likedBy else True,
					'isUnlikable': self.post.isUnlikable if self.post.username == name
								or name in self.post.unlikedBy else True,
					'isEditable' : self.post.isEditable if self.post.username == name
								else False,
					'isDeletable' : self.post.isDeletable if self.post.username == name
								else False
					}
					blogsList.append(self.eachPost)
				self.render("blogPost.html",blogsList=blogsList, user={'name':name})


class NewBlogForm(handler):
	def get(self):
		self.user = self.evaluateCookie('user')
		# if this methods return false
		if not self.user:
			self.render("home.html")
		else:
			self.render("newblogForm.html")

	def post(self):
		self.userName = self.evaluateCookie('user')
		if not self.userName:
			self.render("home.html")
		else:
			self.subject = self.request.get("subject")
			self.content = self.request.get("Content")
			if self.userName and self.subject and self.content:
				self.post = BlogDB.Posts(username=self.userName,
									subject=self.subject,
									content=self.content)
				self.postKey = self.post.put()
				postId = self.postKey.id()
				self.redirect("/blog/%d" % postId)

class NewBlog(handler):
	def get(self):
		self.checkUser = self.evaluateCookie('user')
		if not self.checkUser:
			self.render("home.html")
		else:
			url = urlparse(self.request.path)
			newBlog = BlogDB.Posts.get_by_id(int(url[2][6:]))
			name = self.checkUser
			commentResults = BlogDB.Comments.query(ndb.AND(BlogDB.Comments.postId == url[2][6:])).fetch()
			self.render("blogPostComment.html", blogsList=[
				{
				'user':newBlog.username,
				'content': newBlog.content,
				'subject': newBlog.subject,
				'date': newBlog.createdTime,
				'likes':newBlog.totalLikes,
				'unlikes': newBlog.totalUnlikes,
				'id': newBlog.key.id(),
				'isLikable': newBlog.isLikable if newBlog.username == name
							or name in newBlog.likedBy else True,
				'isUnlikable': newBlog.isUnlikable if newBlog.username == name
								or name in newBlog.unlikedBy else True,
				'isEditable' : newBlog.isEditable if newBlog.username == name
								else False,
				'isDeletable' : newBlog.isDeletable if newBlog.username == name
								else False
				}],
				user={'name':name},
				previousComments = [
					{'author': comment.author,
					'content': comment.content,
					'id': comment.key.id(),
					'postId': comment.postId,
					'isEditable': comment.isEditable if comment.author == name
								else False,
					'isDeletable': comment.isDeletable if comment.author == name
									else False
					}
					for comment in commentResults
					]
			)

	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			self.ifContentOrComment = self.request.get('submitEditedText')
			if self.ifContentOrComment:
				newContent = self.request.get('newPostContent')
				url = urlparse(self.request.path)
				blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:]))
				blogToUpdate.content = newContent
				blogToUpdate.put()
				time.sleep(.1)
				self.redirect('/blog')
			else:
				url = urlparse(self.request.path)
				self.postId = url[2][6:]
				self.commentContent= self.request.get('postAComment')
				self.comment = BlogDB.Comments(author=self.user,
									content=self.commentContent,
									postId=self.postId)
				self.commentKey = self.comment.put()
				time.sleep(.1)
				self.redirect('/blog/%d' % int(self.postId))


class LikedPost(handler):
	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			url = urlparse(self.request.path)
			blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-5]))
			blogToUpdate.totalLikes = blogToUpdate.totalLikes + 1
			blogToUpdate.likedBy[self.user] = 1
			blogToUpdate.put()
			time.sleep(.1)
			self.redirect('/blog')

class UnlikedPost(handler):
	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			url = urlparse(self.request.path)
			blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-7]))
			blogToUpdate.totalUnlikes = blogToUpdate.totalUnlikes + 1
			blogToUpdate.unlikedBy[self.user] = 1
			blogToUpdate.put()
			time.sleep(.1)
			self.redirect('/blog')

class DeletePost(handler):
	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			url = urlparse(self.request.path)
			blogToUpdate = BlogDB.Posts.get_by_id(int(url[2][6:-7]))
			blogToUpdate.key.delete()
			time.sleep(.1)
			self.redirect('/blog')

class DeleteComment(handler):
	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			url = urlparse(self.request.path)
			commentToUpdate = BlogDB.Comments.get_by_id(int(url[2][14:-7]))
			commentToUpdate.key.delete()
			time.sleep(.1)
			self.redirect('/blog/%d' % int(commentToUpdate.postId))

class EditComment(handler):
	def post(self):
		self.user = self.evaluateCookie('user')
		if not self.user:
			self.render("home.html")
		else:
			newContent = self.request.get('newCommentContent')
			url = urlparse(self.request.path)
			commentToUpdate = BlogDB.Comments.get_by_id(int(url[2][14:-5]))
			commentToUpdate.content = newContent
			commentToUpdate.put()
			time.sleep(.1)
			self.redirect('/blog/%d' % int(commentToUpdate.postId))



app = webapp2.WSGIApplication([
	('/welcome', WelcomePage),
	('/', HomePage),
	('/signup',SignUp),('/login', LogIn),
	('/blog/newpost', NewBlogForm),
	('/blog/[0-9]+',NewBlog),('/logout', Logout),('/blog',BlogPage),
	('/blog/[0-9]+/like',LikedPost),('/blog/[0-9]+/unlike',UnlikedPost),
	('/blog/[0-9]+/delete',DeletePost),('/blog/comment/[0-9]+/edit',EditComment)
	,('/blog/comment/[0-9]+/delete',DeleteComment)
], debug=True)
