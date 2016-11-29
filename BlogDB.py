from google.appengine.ext import ndb

class Posts(ndb.Model):
    content = ndb.TextProperty(indexed=False, required=True)
    createdTime = ndb.DateTimeProperty(auto_now=True)
    username = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True,indexed=False)


#p1 = Posts(content='This is my first blog', username='x', email='xyz@abc.com')
#p1.put()

class Users(ndb.Model):
	name = ndb.StringProperty(required=True)
	password = ndb.StringProperty(required=True, indexed=False)
	email = ndb.StringProperty(required=True,indexed=True)
	createdTime = ndb.DateTimeProperty(auto_now=True)

	# @classmethos
	# def makeSalt():
	# 	return ''.join(random.choice(string.letters) for x in range(5))

	# def makePwHash(name,pw,salt=None):
	# 	if not salt:
	# 		salt=make_salt()
	# 	h = hashlib.sha256(name+pw+salt).hexdigest()
	# 	return '%s,%s' % (h,salt)

	# #check at the time of login
	# def validPw(name, pw, h):
	# 	salt = h.split(',')[1]
	# 	return h == makePwHash(name,pw,salt)
