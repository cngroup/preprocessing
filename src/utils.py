#define User, UserGroup, Community, Event, Hashtag, Activities

class MyUser(object):
	"""docstring for MyUser"""
	uid = ''
	name = ''
	likelihood = 0
	diversity = 0
	###############
	status = {}
	community = ''
	time = 0
	sentiment = 0

	def __init__(self, uid, name, likelihood, diversity):
		super(MyUser, self).__init__()
		self.uid = uid
		self.name = name
		self.likelihood = likelihood
		self.diversity = diversity
		self.status = {}

	def setStatus(self, st):
		self.status = st

	def setCommunity(self, com):
		self.community = com

	def setTime(self, time):
		self.time = time

	def setSentiment(self, sentiment):
		self.sentiment = sentiment

	def getStatus(self):
		return self.status

	def getTime(self):
		return self.time

	def getCommunity(self):
		return self.community

	def getSentiment(self):
		return self.sentiment

	def getId(self):
		return self.uid

	def getName(self):
		return self.name

	def getLikelihood(self):
		return self.likelihood

	def getDiversity(self):
		return self.diversity


class UserGroup(object):
	"""docstring for UserGroup"""
	uid = ''
	time = 0
	sentiment = [0, 0]
	users = []
	def __init__(self):
		super(UserGroup, self).__init__()
		self.sentiment = [0, 0]
		self.users = []
	
	def setId(self, uid):
		self.uid = uid
	
	def setTime(self, time):
		self.time = time

	def setSentiment(self, i, value):
		self.sentiment[i] = value

	def addUser(self, user):
		self.users.append(user)	

	def addUsers(self, user):
		self.users.extend(user)

	def getId(self):
		return self.uid

	def getTime(self):
		return self.time

	def getSentiment(self, i):
		return self.sentiment[i]

	def getSentiment(self):
		return self.sentiment

	def getNumUser(self):
		return len(self.users)

	def getUser(self, i):
		return self.users[i]


class Community(object):
	"""docstring for Community"""
	cid = ''
	usergroup = []
	def __init__(self):
		super(Community, self).__init__()
		self.usergroup = []
	
	def setId(self, cid):
		self.cid = cid

	def getId(self):
		return self.cid

	def addGroup(self, ugroup):
		self.usergroup.append(ugroup)

	def getNumGroup(self):
		return len(self.usergroup)

	def getUserGroup(self, i):
		return self.usergroup[i]


class Event(object):
	"""docstring for Event"""
	eid = ''
	time = 0
	hashtags = {}
	def __init__(self):
		super(Event, self).__init__()
		self.hashtags = {}
	
	def setId(self, eid):
		self.eid = eid

	def setTime(self, time):
		self.time = time

	def addHashtag(self, key, hashtag):
		self.hashtags[key] = hashtag

	def updateHashtag(self, key, tag):
		if key not in self.hashtags:
			self.hashtags[key] = tag
		else:
			t = self.hashtags[key]
			mention = tag.getMentions()
			t.accMention(0, mention[0])
			t.accMention(1, mention[1])
			t.accSentiment(0, tag.getSentiment(0))
			t.accSentiment(1, tag.getSentiment(1))
			self.hashtags[key] = t 
	
	def getId(self):
		return self.eid

	def getTime(self):
		return self.time

	def getNumHashtag(self):
		return len(self.hashtags)

	def getHashtagKeys(self):
		return self.hashtags.viewkeys()

	def getHashtag(self, key):
		return self.hashtags[key]


class HashTag(object):
	"""docstring for HashTag"""
	tag = ''
	sentiment = [0, 0]
	mention = [0, 0]
	time = []
	def __init__(self):
		super(HashTag, self).__init__()
		self.mention = [0, 0]
		self.sentiment = [0, 0]
		self.time = []
		
	def addTime(self, time):
		self.time.append(time)

	def setTag(self, tag):
		self.tag = tag

	def accSentiment(self, i, value):
		self.sentiment[i] += value

	def accMention(self, i, value):
		self.mention[i] += value

	def increaseMention(self, i):
		self.mention[i] += 1

	def getTime(self):
		return self.time

	def getTag(self):
		return self.tag

	def getSentiment(self, i):
		return self.sentiment[i]

	def getSentiments(self):
		return self.sentiment

	def getMention(self, i):
		return self.mention[i]

	def getMentions(self):
		return self.mention


class Activity(object):
	"""docstring for Activity"""
	gid = ''
	eid = ''
	pos = ''
	def __init__(self):
		super(Activity, self).__init__()
	
	def setGroupId(self, gid):
		self.gid = gid
	
	def setEventId(self, eid):
		self.eid = eid

	def setType(self, pos):
		self.pos = pos

	def getGroupId(self):
		return self.gid

	def getEventId(self):
		return self.eid

	def getType(self):
		return self.pos
