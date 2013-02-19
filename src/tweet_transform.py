from nltk.corpus import brown, stopwords
from nltk.stem.snowball import EnglishStemmer
from nltk.tokenize import RegexpTokenizer
from scipy import *
from scipy.sparse import *
from sets import Set
from twitter import *
import cPickle as pickle
import numpy
import operator
import os
import re
import simplejson as json
import time
import ttp

#install nltk

filedir = 'data/company/'
filelist = os.listdir(filedir)
filelist = './companylist.txt'

focususer = Set()
statuses = []
NUM_MATRIX = 20
MATRIX_ALL = []
wordset = Set()
userset = Set()
hashtagset = Set()
stemmer = EnglishStemmer()
p = ttp.Parser()
timerange = [0, 0] 

def main():
	# filterFiles()
	# print len(focususer)
	# loadFiles()
	# print len(statuses)

	f = open(filelist, 'r')
	flist = json.load(f)
	loadFilesByList(flist)
	buildIndex()
	buildMatrix()
	f.close()

def buildMatrix():
	begin = getTime(statuses[0].GetCreatedAt())
	end = getTime(statuses[len(statuses)-1].GetCreatedAt())
	interval = (end-begin)/NUM_MATRIX;

	subsets = numpy.empty((NUM_MATRIX+1, 0)).tolist()
	for s in statuses:
		t = getTime(s.GetCreatedAt())
		index = (t-begin)/interval
		subsets[index].append(s)

	users = list(userset)
	words = list(wordset)
	hashtags = list(hashtagset)

	for u in subsets:
		buildMatrixByTime(u, users, words, hashtags)

	i = 0
	for m in MATRIX_ALL:
		hashword = open('../output/hashword_'+str(i)+'.dat', 'wb')
		userword = open('../output/userword_'+str(i)+'.dat', 'wb')
		userhash = open('../output/userhash_'+str(i)+'.dat', 'wb')
		userreply = open('../output/userreply_'+str(i)+'.dat', 'wb')
		userretweet = open('../output/userretweet_'+str(i)+'.dat', 'wb')
		pickle.dump(m['hashword'], hashword, pickle.HIGHEST_PROTOCOL)
		pickle.dump(m['userword'], userword, pickle.HIGHEST_PROTOCOL)
		pickle.dump(m['userhash'], userhash, pickle.HIGHEST_PROTOCOL)
		pickle.dump(m['userreply'], userreply, pickle.HIGHEST_PROTOCOL)
		pickle.dump(m['userretweet'], userretweet, pickle.HIGHEST_PROTOCOL)
		hashword.close()
		userword.close()
		userhash.close()
		userreply.close()
		userretweet.close()
		print 'finish..matrix' + str(i)
		i += 1

	userlist = open('../output/userlist.txt', 'wb')
	json.dump(users, userlist)
	userlist.close()

	wordlist = open('../output/wordlist.txt', 'wb')
	json.dump(words, wordlist)
	wordlist.close()

	hashlist = open('../output/hashlist.txt', 'wb')
	json.dump(hashtags, hashlist)
	hashlist.close()

def buildMatrixByTime(slist, users, words, hashtags):
	matrixsets = {}
	userword = dok_matrix((len(users),len(words)), dtype=int)
	userhash = dok_matrix((len(users), len(hashtags)), dtype=int)
	userreply = dok_matrix((len(users), len(users)), dtype=int)
	userretweet = dok_matrix((len(users), len(users)), dtype=int)
	hashword = dok_matrix((len(hashtags),len(words)), dtype=int)
	for s in slist:
		uid = users.index(s.GetUser().id)
		w = getWords(s.text)
		if w is not None:
			for ww in w:
				wid = words.index(ww)
				userword[uid, wid] = userword[uid, wid]+1

		if s.GetInReplyToUserId() != -1:
			rid = users.index(s.GetInReplyToUserId())
			userreply[uid, rid] = userreply[uid, rid]+1
		if s.GetRetweeted_status() is not None:
			rid = users.index(s.GetRetweeted_status().GetUser().id)
			userretweet[uid, rid] = userretweet[uid, rid]+1

		result = p.parse(s.text)
		tag = result.tags
		if len(tag) > 0:
			for t in tag:
				hid = hashtags.index(t.lower())
				userhash[uid, hid] = userhash[uid, hid]+1
				if w is not None:
					for ww in w:
						wid = words.index(ww)
						hashword[hid, wid] = hashword[hid, wid]+1
	matrixsets['userword'] = userword.tocsr().todense()
	matrixsets['userhash'] = userhash.tocsr().todense()
	matrixsets['userreply'] = userreply.tocsr().todense()
	matrixsets['userretweet'] = userretweet.tocsr().todense()
	matrixsets['hashword'] = hashword.tocsr().todense()
	MATRIX_ALL.append(matrixsets)



def getTime(timestring):
	format = '%b %d, %Y %I:%M:%S %p'
	result = time.strptime(timestring, format)
	return int(time.mktime(result))

def buildIndex():
	for s in statuses:
		w = getWords(s.text)
		if w is not None:
			for ww in w:
				wordset.add(ww)
		
		userset.add(s.GetUser().id)
		if s.GetInReplyToUserId() != -1:
			userset.add(s.GetInReplyToUserId())
		if s.GetRetweeted_status() is not None:
			userset.add(s.GetRetweeted_status().GetUser().id)

		result = p.parse(s.text)
		tag = result.tags
		if len(tag) > 0:
			for t in tag:
				hashtagset.add(t.lower())

def getWords(text):
	result = p.parse(text)
	for u in result.urls:
		text = text.replace(u, '')
	for u in result.users:
		text = text.replace('@'+u, '')
	for t in result.tags:
		text = text.replace('#'+t, '')
	text = text.replace('RT', '')
	words = RegexpTokenizer('[a-zA-Z]\w+').tokenize(text)
	stemmed_words = [stemmer.stem(w.lower()) for w in words]
	filtered_words = [w.lower() for w in stemmed_words if w.lower() not in stopwords.words('english')]
	if len(filtered_words) == 0:
		return None
	else:
		return filtered_words

def loadFilesByList(flist):
	for filename in flist:
		f = open(filename, 'r')
		data = json.load(f)
		status = Status.NewFromJsonDict(data)
		statuses.append(status)

def loadFiles():
	templist = []
	for filename in filelist:
		if filename[0] == '.':
			continue
		else:
			f = open(filedir+filename, 'r')
			data = json.load(f)
			status = Status.NewFromJsonDict(data)
			if str(status.GetUser().id) in focususer:
				templist.append(filename)
				statuses.append(status)
	output = open('./companylist.txt', 'w')
	json.dump(templist, output)
	output.close()

def filterFiles():
	userdict = {}
	for filename in filelist:
		if filename[0] == '.':
			continue
		else:
			f = open(filedir+filename, 'r')
			data = json.load(f)
			status = Status.NewFromJsonDict(data)
			uid = status.GetUser().id
			if str(uid) not in userdict:
				userdict[str(uid)] = 1
			else:
				print 'old user ' + str(uid)
				v = userdict[str(uid)]
				userdict[str(uid)] = v+1

	sortlist = sorted(userdict.iteritems(), key=operator.itemgetter(1), reverse = True)
	for k,v in sortlist:
		if v > 20:
			focususer.add(k)

if __name__ == '__main__':
	main()
