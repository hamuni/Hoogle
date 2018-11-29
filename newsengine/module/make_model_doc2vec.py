import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

import os
import re
import string
import multiprocessing
import pandas as pd
from nltk.tokenize import word_tokenize
from stop_words import get_stop_words
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import time

def make_model(whole_news):
    docs = []
    start = time.clock()
    for news in whole_news:
        id = news['url']
        text = re.sub('[!"#%\'()*+,/:;<=>?\[\]\\xa0^_`{|}~’”“′‘\\\]',' ', news['title'].lower())
        text += " " + news['article'].lower()
        text = word_tokenize(text)
        T = TaggedDocument(text, [id])
        docs.append(T)
    end1 = time.clock()
    print("Text Preprocessing: %s"%(end1-start))

    # initialize a model
    model = Doc2Vec(size=100, window=5, alpha=0.025, min_alpha=0.025, min_count=0, dm=0, workers=multiprocessing.cpu_count())

    # build vocabulary
    model.build_vocab(docs)
    end2 = time.clock()
    print("Make Doc2Vec Model: %s"%(end2-end1))

    # train model
    model.train(docs, total_examples=len(docs), epochs=20)
    end3 = time.clock()
    print("epochs 20 times: %s"%(end3-end2))

    # save model
    model.save('./model/doc2vec.model')

    return
