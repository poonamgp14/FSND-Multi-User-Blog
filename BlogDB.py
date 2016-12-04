from google.appengine.ext import ndb

# The form input boxes must have the names 'subject' and
# 'content' in order for the grading script to correctly post to them.
class Posts(ndb.Model):
    content = ndb.TextProperty(indexed=False, required=True)
    createdTime = ndb.DateTimeProperty(auto_now=True)
    username = ndb.StringProperty(required=True)
    subject = ndb.StringProperty(required=True,indexed=False)
    totalLikes = ndb.IntegerProperty(default = 0)
    totalUnlikes = ndb.IntegerProperty(default = 0)
    isLikable = ndb.BooleanProperty(default = False)
    isUnlikable = ndb.BooleanProperty(default = False)
    isCommentable = ndb.BooleanProperty(default = True)
    isEditable = ndb.BooleanProperty(default = True)
    isDeletable = ndb.BooleanProperty(default = True)
    likedBy = ndb.JsonProperty(required=False,default={})
    unlikedBy = ndb.JsonProperty(required=False,default={})

class Users(ndb.Model):
	name = ndb.StringProperty(required=True)
	password = ndb.StringProperty(required=True, indexed=False)
	email = ndb.StringProperty(required=True,indexed=True)
	createdTime = ndb.DateTimeProperty(auto_now=True)



class Comments(ndb.Model):
	author = ndb.StringProperty(required=True)
	content = ndb.TextProperty(indexed=False, required=True)
