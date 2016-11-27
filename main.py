import webapp2
import jinja2
import os
from google.appengine.api import users
import BlogDB
from urlparse import urlparse
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir)
									,autoescape= True)

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

class UserRegister(handler):
    def get(self):
        self.render("login.html")


class MainPage(handler):
    def get(self):
        blogsList = []
        self.posts = BlogDB.Posts.query().order(-BlogDB.Posts.createdTime)
        if self.posts:
            for self.post in self.posts:
                self.eachPost = {'user':self.post.username,'content': self.post.content,
                                'date': self.post.createdTime
                                }
                blogsList.append(self.eachPost)
            self.render("welcome.html",blogsList=blogsList)
        else:
			self.render("welcome.html", noBlogs='There are no blogs posted yet!')

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
        #self.response.write(sandy.content)
        self.render("blogPost.html", blogsList=[{'user':newBlog.username,'content': newBlog.content,
                                'date': newBlog.createdTime
                                }])


app = webapp2.WSGIApplication([
    ('/welcome', MainPage),
    ('/', UserRegister),
    ('/newBlogForm', NewBlogForm),
    ('/[0-9]+',NewBlog)
], debug=True)
