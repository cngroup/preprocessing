from nltk.corpus import brown, stopwords
from nltk.stem.snowball import EnglishStemmer
from nltk.tokenize import RegexpTokenizer
from scipy import *
from scipy.sparse import *
from sets import Set
from twitter import *
import cPickle as pickle
import numpy
import math
import operator
import os
import re
import simplejson as json
import time
import ttp
from utils import *

class tweetTransform(object):
	
	"""docstring for tweetTransform"""
	def __init__(self, params):
		super(tweetTransform, self).__init__()
		self.filelist = params['raw_tweet_list']
		self.path = params['raw_tweet_path']
		self.num_matrix = params['num_matrix']
		
		self.statuses = []
		self.tweetparser = ttp.Parser()
		self.hashlinks = []
		self.user_dict = {}

	def load_file(self):
		filtered = open(self.filelist, 'r')
		flist = json.load(filtered)
		for filename in flist:
			f = open(self.path+filename, 'r')
			data = json.load(f)
			status = Status.NewFromJsonDict(data)
			self.statuses.append(status)
			f.close()
		filtered.close()

	def get_time(self,timestring):
		format = '%b %d, %Y %I:%M:%S %p'
		result = time.strptime(timestring, format)
		return int(time.mktime(result))

	def set_time(self):
		self.begin = self.get_time(self.statuses[0].GetCreatedAt())
		self.end = self.get_time(self.statuses[len(self.statuses)-1].GetCreatedAt())
		self.interval = (self.end-self.begin)/self.num_matrix

	def make_subsets(self):
		self.subsets = numpy.empty((self.num_matrix+1, 0)).tolist()
		for s in self.statuses:
			t = self.get_time(s.GetCreatedAt())
			index = (t-self.begin)/self.interval
			self.subsets[index].append(s)

	def preprocess(self):
		self.load_file()
		self.set_time()
		self.make_subsets()

	def build_all(self):
		for i in range(0, self.num_matrix):
			self.get_hashtags_activitity(self.subsets[i], i)
			self.get_users(self.subsets[i], i)

	def output(self):
		obj = {}
		obj['begin'] = self.begin
		obj['end'] = self.end
		obj['interval'] = self.interval
		obj['hashlinks'] = self.hashlinks
		obj['userdict'] = self.user_dict
		return obj

	def get_users(self, slist, timeid):
		for s in slist:
			rid = s.GetUser().id
			if str(rid) not in self.user_dict:
				u = MyUser(rid, s.GetUser().name)
				self.user_dict[str(rid)] = u

			retweeter = self.user_dict[str(rid)]
			retweeter.add_retweet(s.id, 0)
			self.user_dict[str(rid)] = retweeter

			if s.GetRetweeted_status() is not None:
				pid = s.GetRetweeted_status().GetUser().id
				if str(pid) not in self.user_dict:
					u = MyUser(pid, s.GetRetweeted_status().GetUser().name)
					self.user_dict[str(pid)] = u

				poster = self.user_dict[str(pid)]
				poster.add_retweet(s.GetRetweeted_status().id, 1)
				poster.add_retweeter(rid)
				self.user_dict[str(pid)] = poster

		for u in self.user_dict.viewvalues():
			likelihood = self.get_likelihood(u.get_retweet())
			diversity = self.get_diversity(u.get_retweeter())
			u.add_likelihood(likelihood, timeid)
			u.add_diversity(diversity, timeid)
			self.user_dict[str(u.get_id())] = u

	def get_likelihood(self, rawdict):
		if len(rawdict) == 0:
			return -1

		count = 0
		for v in rawdict.viewvalues():
			if v > 0:
				count += 1
		likelihood = float(count)/len(rawdict)
		return likelihood

	def get_diversity(self, rawlist): #bug
		if len(rawlist) == 0:
			return -1
		if len(rawlist) == 1:
			return 0
		
		distinct = list(Set(rawlist))
		freqList = []
		for user in distinct:
			ctr = 0
			for u in rawlist:
				if u == user:
					ctr += 1
			freqList.append(float(ctr)/len(rawlist))
		ent = 0.0
		for freq in freqList:
			ent = ent + freq * math.log(freq, 2)
		return (-ent)


	def get_hashtags_activitity(self, slist, timeid):
		for s in slist:
			uid = s.GetUser().id
			if s.GetRetweeted_status() is None:
				typeid = 'post'
			else:
				typeid = 'mention'
			pp = self.tweetparser.parse(s.text)
			tag = pp.tags
			if len(tag) > 0:
				for t in tag:
					self.hashlinks.append((t.lower(), uid, timeid, typeid))

if __name__ == '__main__':
	params = {}
	params['filelist'] = '../data/output/companylist2.txt'
	params['num_matrix'] = 20

	tweet_trans = tweetTransform(params)
	tweet_trans.preprocess()
	tweet_trans.build_all()
	print len(tweet_trans.output()['userdict'])
