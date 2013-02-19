import time
import pickle
import numpy
from sets import Set
import simplejson as json
from utils import *
from clustering import sentimentCluster
from tweet_transform2 import tweetTransform

class jsonFactory(object):
	"""docstring for jsonFactory"""
	def __init__(self, param):
		super(jsonFactory, self).__init__()
		self.params = param;
		self.hash_dict = {}

	def run_factory(self): 
		print 'sentiment clustering..'
		self.cluster_community()
		print 'preprocessing ...'
		self.preprocess()
		print 'generate temporal user groups'
		self.add_usergroup()
		print 'compute hash-tag activities' 
		self.add_hashtag_activity()
		print 'output json file for visualization'
		self.export_json()

	def preprocess(self):
		tweet_trans = tweetTransform(self.params)
		tweet_trans.preprocess()
		tweet_trans.build_all()
		preprocess_result = tweet_trans.output()
		self.user_dict = preprocess_result['userdict']
		self.begin = preprocess_result['begin']
		self.end = preprocess_result['end']
		self.interval = preprocess_result['interval']
		self.hashtupple = preprocess_result['hashlinks']

	def cluster_community(self):
		obj = pickle.load(open(self.params['user_word']))
		wordlist = json.load(open(self.params['word_list']))
		userlist = json.load(open(self.params['user_list']))
		sen_clu = sentimentCluster(self.params)
		sen_clu.clustering_main(obj, wordlist, userlist, self.params['emotion_label'], 0.5, 0.5)
		self.clu_result = sen_clu.output()

	def add_usergroup(self):
		self.clusters = numpy.empty((self.params['cluster_num'], 0)).tolist()
		for tupple in self.clu_result:
			index = int(tupple[1])
			self.clusters[index].append(tupple)
		cid = 0
		self.community = []
		for c in self.clusters:  #cluster set |5|
			com = {}
			com['cid'] = cid
			group = numpy.empty((self.params['matrix_num'], 0)).tolist() #group set |20|
			for tupple in c:
				index = tupple[3]
				group[index].append(tupple)

			groups = []
			for i in range(0, self.params['matrix_num']):
				gset = group[i]
				g = {}
				g['gid'] = str(cid)+'_'+str(i)
				g['time'] = str(i)
				sentiment = 0
				users = []
				for t in gset:
					uid = t[0]
					if str(uid) not in self.user_dict:
						print 'error'
						continue
					user = self.user_dict[str(uid)]
					user.set_community(str(cid))
					self.user_dict[str(uid)] = user
					sentiment += t[2]
					u = {}
					u['id'] = user.get_id()
					u['name'] = user.get_name()
					u['retweeternum'] = len(user.get_retweeter()) 
					u['statusnum'] = len(user.get_retweet())
					if str(i) not in user.get_likelihood():
						u['likelihood'] = -1
					else:
						u['likelihood'] = user.get_likelihood()[str(i)]
					if str(i) not in user.get_diversity():
						u['diversity'] = -1
					else:
						u['diversity'] = user.get_diversity()[str(i)]
					users.append(u)
				g['user'] = users
				if len(gset) == 0:
					g['sentiment'] = 0
				else:
					g['sentiment'] = sentiment/len(gset)
				groups.append(g)
			cid += 1
			com['group'] = groups
			self.community.append(com)

	def add_hashtag_activity(self):
		self.index_hashtags()
		eventset = numpy.empty((self.params['matrix_num'], 0)).tolist()
		for tupple in self.hashtupple:
			eventset[tupple[2]].append(tupple)

		hashall = Set()
		self.event = []
		for i in range(0, self.params['matrix_num']):
			hashset = Set()
			evn = eventset[i]
			e = {}
			e['time'] = str(i)
			for h in evn:
				hashset.add(h[0])
			harray = []
			for h in hashset:
				if h not in self.hash_dict:
					continue
				if str(i) not in self.hash_dict[h].get_mention():
					continue
				tag = {}
				tag['tag'] = h
				tag['mention'] = self.hash_dict[h].get_mention()[str(i)]
				harray.append(tag)
				hashall.add(h)
			e['hashtag'] = harray
			self.event.append(e)

		self.hashlink = []
		for h in hashall:
			tag = {}
			tag['tag'] = h
			tag['timelist'] = sorted(self.hash_dict[h].get_mention().keys())
			self.hashlink.append(tag)

		self.activtity = []
		for i in range(0, self.params['matrix_num']):
			cal = {}
			for j in range(0, self.params['cluster_num']):
				pm = {}
				pm['mention'] = 0
				pm['post'] = 0
				cal[str(j)] = pm
			hset = eventset[i]
			for h in hset:
				cid = self.user_dict[str(h[1])].get_community()
				if cid == -1:
					continue
				if h[3] == 'mention':
					cal[str(cid)]['mention'] += 1
				else:
					cal[str(cid)]['post'] += 1
			for j in range(0, self.params['num_cluster']):
				act = {}
				act['gid'] = str(j)+'_'+str(i)
				act['eid'] = str(i)
				if cal[str(j)]['mention'] >= cal[str(j)]['post']:
					act['type'] = 'mention'
				else:
					act['type'] = 'post'
				self.activtity.append(act)

	def index_hashtags(self):
		for tupple in self.hashtupple:
			if self.user_dict[str(tupple[1])].get_community() == -1:
				continue
			if tupple[0] not in self.hash_dict:
				h = HashTag()
				h.set_tag(tupple[0])
				cid = self.user_dict[str(tupple[1])].get_community()
				h.add_mention(cid, tupple[2], self.params['num_cluster'])
				self.hash_dict[tupple[0]] = h
			else:
				h = self.hash_dict[tupple[0]]
				cid = self.user_dict[str(tupple[1])].get_community()
				h.add_mention(cid, tupple[2], self.params['num_cluster'])
				self.hash_dict[tupple[0]] = h

	def export_json(self):
		obj = {}
		obj['start'] = self.begin
		obj['end'] = self.end
		obj['segment'] = self.interval
		obj['community'] = self.community
		obj['event'] = self.event
		obj['hashlink'] = self.hashlink
		obj['activity'] = self.activtity
		f = open(self.params['output'],'w')
		f.write(json.dumps(obj))
		f.close()

if __name__ == '__main__':
	params = {}
	params['raw_tweet_list'] = '../data/output/companylist2.txt'
	params['output'] = '../data/output/test3.json'
	params['raw_tweet_path'] = '../data/company/'
	params['clustering_method'] = 'hierarchical'
	params['smoothing_method'] = 'l2'
	params['smoothness_threshold'] = 0.5
	params['user_word'] = '../data/output/userword.obj'
	params['word_list'] = '../data/output/wordlist.txt'
	params['user_list'] = '../data/output/userlist.txt'
	params['emotion_label'] = '../data/AFINN-111.txt'
	params['num_clusters'] = 10;
	params['num_matrix'] = 20;
	
	json_fac = jsonFactory(params)
	json_fac.run_factory()

