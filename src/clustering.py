'''
Created on Feb 1, 2013

@author: feiwang03
'''

import csv
import math
import numpy as np
import scipy.sparse as ss
import scipy.interpolate as sinter
from sklearn.cluster import Ward

import pickle
import simplejson as json

class sentimentCluster(object):
    '''
    classdocs
    '''
    
    def __init__(self,params):
        '''
        Constructor
        '''
        self.clustering_method = params['clustering_method']
        self.smoothing_method = params['smoothing_method']
        self.smoothness_threshold = params['smoothness_threshold']
        self.num_clusters = params['num_clusters']
    
    def import_user_matrices(self,user_word_matrices):
        # user_word_matrices should be a list of sparse user_word matrices
        self.user_matrices = user_word_matrices[:]
        
    def import_word_list(self,word_list):
        # word list is a list of words
        self.word_list = word_list[:]
    
    def import_user_list(self,user_list):
        self.user_list = np.array(user_list[:])
        
    def match_word_sentiment(self,labeled_word_list_file):
        # matching with external labeled word list to get word sentiments
        labeled_list = []
        labeled_sentiment = []
        
        self.word_sentiment = []
        
        for rows in csv.reader(open(labeled_word_list_file),delimiter = '\t'):
            labeled_list.append(rows[0])
            labeled_sentiment.append(np.double(rows[1]))
            
        for word in self.word_list:
            
            if word in labeled_list:
                self.word_sentiment.append(labeled_sentiment[labeled_list.index(word)])
            else:
                self.word_sentiment.append(0.0)
            '''
            word_sent = 0.0
            num_match = 0
            for labeled_word in labeled_list:
                if labeled_word in word:
                    print labeled_word,word
                    word_sent+=labeled_sentiment[labeled_list.index(labeled_word)]
                    num_match+=1
            if num_match:
                self.word_sentiment.append(word_sent/np.double(num_match))
            else:
                self.word_sentiment.append(0.0)
            '''
            
    def construct_sentiment_curves(self):
        # construct user sentiment curves
        # word_sentiment_vec needs to be a column vector
        word_sentiment_vec = np.array(self.word_sentiment)
        self.sentiment_curves = []
        for user_matrix in self.user_matrices:
            curve = user_matrix*word_sentiment_vec
            size = len(np.nonzero(curve)[0])
            curve = curve / math.sqrt(size)
            self.sentiment_curves.append(curve)
            
        self.sentiment_curves = np.array(self.sentiment_curves)
        x = np.arange(len(self.user_matrices))
        num_user = self.sentiment_curves.shape[1]
        for i in range(num_user):
            y = self.sentiment_curves[:,i]
            ind = np.where(y!=0.0)[0]
            xi = x[ind]
            yi = y[ind]
            s = sinter.UnivariateSpline(xi,yi)
            self.sentiment_curves[:,i] = s(x)
    
            
    def estimate_smoothness(self):
        # estimate the smoothness of the sentiment curves
        num_curves = self.sentiment_curves.shape[1]
        num_time = self.sentiment_curves.shape[0]
        self.curve_smoothness = []
        for j in range(num_curves):
            smoothness = 0.0
            for i in range(1,num_time):
                if self.smoothing_method == 'l2':
                    smoothness += (self.sentiment_curves[i][j]-self.sentiment_curves[i-1][j])**2
                
            self.curve_smoothness.append(smoothness)
        self.curve_smoothness = np.array(self.curve_smoothness)
            
    def filtering_smoothness(self):
        inds = np.argsort(self.curve_smoothness)
        num_curves = self.curve_smoothness.shape[0]
        inds_remain = inds[:np.int(np.double(num_curves)*self.smoothness_threshold)]
        self.curve_smoothness = self.curve_smoothness[inds_remain]
        self.sentiment_curves = self.sentiment_curves[:,inds_remain]
        self.user_list = self.user_list[inds_remain]
        
    def filtering_density(self,portion):
        user_vectors = []
        for user_matrix in self.user_matrices:
            user_vectors.append(np.array(user_matrix.sum(axis=1))[:,0])
        user_vectors = np.array(user_vectors)
        user_nonzero = np.sum(user_vectors>0,axis=0)
        ind_remaining = list(np.where(np.double(user_nonzero)>=np.double(user_vectors.shape[0])*np.double(portion))[0])
        user_matrices_remaining = []
        for i in range(len(self.user_matrices)):
            user_matrices_remaining.append(self.user_matrices[i][ind_remaining,:])
        self.user_matrices = user_matrices_remaining[:]
        
    def clustering_curves(self):
        # clustering the curves
        if self.clustering_method== 'hierarchical':
            ward = Ward(n_clusters = self.num_clusters).fit(self.sentiment_curves.T)
            self.cluster_labels = ward.labels_
            
    def construct_word_graph(self):
        if self.user_matrices == []:
            print "error: please import user matrices first"
            return
        num_words = self.user_matrices[0].shape[1]
        self.word_mat = ss.lil_matrix((num_words,num_words))
        for user_matrix in self.user_matrices:
            self.word_mat = self.word_mat+user_matrix.T*user_matrix
            
    def propagate_word_sentiment(self,word_list,labeled_word_list_file,mu):
        self.import_word_list(word_list)
        self.match_word_sentiment(labeled_word_list_file)
        self.construct_word_graph()
        num_words = len(self.word_sentiment)
        alpha = 1.0/(1.0+mu)
        beta = 1-alpha
        A = np.eye(num_words)-alpha*self.word_mat.toarray()
        b = beta*np.reshape(self.word_sentiment,(num_words,1))
        f = np.linalg.solve(A, b)
        self.word_sentiment = f[:,0]
    
    def output(self):
        #output in the format of (userid, clusterid, sentiment, time)
        num_curves = self.sentiment_curves.shape[1]
        num_time = self.sentiment_curves.shape[0]
        results = []
        for j in range(num_curves):
            for i in range(num_time):
                results.append((self.user_list[j], self.cluster_labels[j], self.sentiment_curves[i][j], i))
        return results
        
    def clustering_main(self,user_word_matrices,word_list,user_list,labeled_word_list_file,portion,alpha):
        # main function
        self.import_user_list(user_list)
        self.import_user_matrices(user_word_matrices)
        self.filtering_density(portion)
        self.propagate_word_sentiment(word_list,labeled_word_list_file,alpha)
        self.construct_sentiment_curves()
        self.estimate_smoothness()
        self.filtering_smoothness()
        self.clustering_curves()

if __name__ == '__main__':
    
#    dataFilePath = '../data/output/userword_'
#    numTime = 20
#    dumpFile = '../data/output/userword.obj'
#    
#    data = []
#    for i in range(numTime):
#        print i
#        obj = pickle.load(open(dataFilePath+str(i)+'.dat'))
#        data.append(ss.csr_matrix(obj))
#    pickle.dump(data, open(dumpFile,'wb'))
    
    params = {}
    params['clustering_method'] = 'hierarchical'
    params['smoothing_method'] = 'l2'
    params['smoothness_threshold'] = 0.5

    clustering_params = {}
    clustering_params['num_clusters'] = 5
    params['clustering_params'] = clustering_params
    
    file_name = '../data/output/userword.obj'
    obj = pickle.load(open(file_name))
    
    label_file = '../data/AFINN-111.txt'

    wordlist_file = '../data/output/wordlist.txt'
    wordlist = json.load(open(wordlist_file))
    
    userlist_file = '../data/output/userlist.txt'
    userlist = json.load(open(userlist_file))
    
    '''
    wordlist = []
    for rows in csv.reader(open(wordlist_file),delimiter=','):
        wordlist.append(rows[1])
    '''
    sen_clu = sentimentCluster(params)
    sen_clu.clustering_main(obj, wordlist, userlist, label_file, 0.5, 0.5)
    sen_clu.output()  
        
            