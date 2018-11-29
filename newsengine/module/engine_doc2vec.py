# -*- coding: utf-8 -*-

import sys
import math
import time
import numpy as np
from multiprocessing.pool import ThreadPool
from operator import attrgetter
import datetime
import re

import gensim
from gensim import models, similarities
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from . import classifier
from . import tfidf

class NewsAndWeights(object):
    def __init__(self,news,weight=0):
        self.news = news
        self._weight = weight
    def addWeight(self, weight):
        self._weight += weight
    def getNews(self):
        return self.news
    def getWeight(self):
        return self._weight
    def __repr__(self):
        return '{}: {}'.format(self.__class__.__name__,
                                  self._weight)
    def __cmp__(self, other):
        if hasattr(other, 'getKey'):
            return self.getKey().__cmp__(other.getKey())

def load_model():
    model = models.Doc2Vec.load('./module/model/doc2vec.model')
    return model




def tfidfAtLatestNews(content, query, topnumber, weight):
    #Tf-Idf 연산
    docs,doc_names= tfidf.read_doc(content)
    index, inverted_index = tfidf.index_doc(docs,doc_names)
    word_dictionary = tfidf.build_dictionary(inverted_index)
    doc_dictionary = tfidf.build_dictionary(index)
    tfidf_matrix = tfidf.compute_tfidf(index,word_dictionary,doc_dictionary)

    dot = tfidf.query_dot(query,word_dictionary,doc_dictionary)
    cos = tfidf.cosine_similarity(tfidf_matrix,dot)
    score_matrix = tfidf.dictionary_vector(cos,doc_dictionary)

    #score_matrix = tfidf.score(tfidf_matrix,word_dictionary,doc_dictionary,query)
    #새로 입력된 데이터 기반 뉴스 리스트

    news_weight_list = []
    for news in score_matrix.keys():
        weighted_score = score_matrix[news]
        news_weight_list.append(NewsAndWeights(content[news], weighted_score * weight))

    #print('\nNewly Updated Data Based :')
    #for idx, news_weight in enumerate(news_weight_list[:topnumber]):
    #    news = news_weight.getNews()
    #    print("%d." % (idx+1)," %s" % news['date']," %s" % news['title']," %s" % news['category'], " score: %f" % news_weight.getWeight())

    return news_weight_list

def get_similar_news(model, token_query, topnumber):
    model.random.seed(0)
    #print(token_query)
    infer_vector = model.infer_vector(token_query)
    similar_news = model.docvecs.most_similar([infer_vector], topn = topnumber)
    return similar_news

def makeNewsAndWeight(news_from_db, weighted_score):
    return NewsAndWeights(news_from_db, weighted_score)


def search(model, content, new_content, query):
    # N
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(makeUpdatedDateNewsList, (new_content,query,WEIGHT_ADDNEWEST,5))
    news_weight_list_updated = async_result.get()

    return sorted_docs_weight,news_weight_list_updated


def sortingByWeight(newsAndWeights):
    return sorted(newsAndWeights, key=attrgetter('_weight'), reverse=True)


def addWeightLatest(newsAndWeights, weight):
    for nw in newsAndWeights:
        delta = (nw.news['date'] - datetime.datetime.now()).days * weight * 0.0005
        nw.addWeight(delta)
    return

def addWeightCategory(newsAndWeights, str_query, weight):
    predicted_category = classifier.predict_category([str_query])
    for nw in newsAndWeights:
        if nw.news['category'] == predicted_category[0]:
            nw.addWeight(weight)
    return

def predictUserInterest(queryHistoryList):
    from . import classifier
    predicted_category_list = classifier.predict_category(queryHistoryList)
    return predicted_category_list

def addWeightUserInterest(newsAndWeights, predicted_category, weight):
    totalCountQueryHistory = len(predicted_category)
    categoryNames = set(predicted_category)
    categoryRatioDict = {}
    for categoryName in categoryNames:
        categoryRatioDict[categoryName] = (predicted_category == categoryName).sum() / totalCountQueryHistory

    for nw in newsAndWeights:
        if nw.news['category'] in categoryRatioDict:
            categoryRatio = categoryRatioDict[nw.news['category']]
            nw.addWeight(categoryRatio * weight)
    return



def removeStopwords(token_query):
    stopwrds = stopwords.words('english')
    removedStopwordsQuery = [token for token in token_query if token not in stopwrds]
    return removedStopwordsQuery

def tokenizeQuery(str_query):
    tokenizedQuery = [word_tokenize(word) for word in [str_query.lower()]]
    return tokenizedQuery[0]


def addWeightTermFrequency(newsAndWeights, query, weight):
    stopwrds = stopwords.words('english')
    query_removed_stopwords = [token for token in query if token not in stopwrds]

    for terms in query_removed_stopwords:
        for nw in newsAndWeights:
            count = nw.news['title'].count(terms) + nw.news['article'].count(terms)
            nw.addWeight(count * weight)
    return

def addWeightIDF(newsAndWeights, query, weight, IDF):
    stopwrds = stopwords.words('english')
    query_removed_stopwords = [token for token in query if token not in stopwrds]
    
    word_Df=IDF
    for terms in query_removed_stopwords:
        for nw in newsAndWeights:
            wordlist = word_tokenize(re.sub('[!"#%\'()*+,./:;<=>?\[\]\\xa0^_`{|}~’”“′‘\\\]',' ', nw.news['title'].lower()) + nw.news['article'])
            for word in wordlist:
                if (word in word_Df.keys()):
                    value_of_df =  math.log(346000/(word_Df[word]))
                    nw.addWeight(value_of_df * weight * 10)
    return
