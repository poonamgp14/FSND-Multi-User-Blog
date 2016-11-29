import random
import string
import hashlib


def makeSalt():
	return ''.join(random.choice(string.letters) for x in range(5))
