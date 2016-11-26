from google.appengine.ext import ndb

class Posts(ndb.Model):
    content = ndb.TextProperty(indexed=False, required=True)
    createdTime = ndb.DateTimeProperty(auto_now=True)
    username = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True,indexed=False)
    

#p1 = Posts(content='This is my first blog', username='x', email='xyz@abc.com')
#p1.put()