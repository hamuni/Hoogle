'''
Add the new data to the pre-exiting Json files
and
Insert the new data into the DB
'''

import gzip
import pandas as pd
import shutil
import json
import os
import datetime
import pymysql
import codecs
from nltk.tokenize import word_tokenize

def dateTransition(content):
    for one_set in content:
        year = int(one_set['date'][0:4])
        month = int(one_set['date'][4:6])
        day = int(one_set['date'][6:8])
        one_set['date'] = str(datetime.date(year,month,day))
    return content

def getItemsFromFiles():

    conn = pymysql.connect(host='localhost', user='root', password='root', db='newsengine', charset='utf8')

    with conn.cursor() as cursor:
        sql_query = "SELECT * FROM news" 
        cursor.execute(sql_query)
        news_list=[]
        while(not(cursor.fetchone() == None)):
            news=cursor.fetchone() 

            temp = {}
            url = news[0]
            category = news[1]
            article = news[4]
            date = news[3]
            title = news[2] 

            temp['url'] = url
            temp['category'] = category
            temp['article'] = article
            temp['date'] = date
            temp['title'] = title
            news_list.append(temp)

    conn.commit()
    conn.close()

    path_ = "./data/new_news.json"
    with open(path_,'rb') as g:
        new_news = g.read()
    #Open the pre-exisisting News Data
    
    model_data = pd.Series([news for news in news_list], index = [news['url'] for news in news_list])

    #Open the newly updated Data
    new_data =pd.read_json(new_news, typ='series', orient='records')
    newly_updated = pd.Series([news for news in new_data], index = [news['url'] for news in new_data])
    newly_updated = dateTransition(newly_updated) # Date 변환, 크로울링 과정으로 빼야할 필요

    for news in newly_updated:
        string = news['article']
        string.replace("'","`")
        string.replace('"','`')
        news['article']=string

    g.close()
    os.remove('./data/new_url.json')
    os.remove('./data/new_news.json')
 
    return model_data, newly_updated

def InsertIntoDB(original_data,contents):
    # DB에 넣은후 새로 업데이트된 data for model 리턴 
    today =datetime.date.today()
    conn = pymysql.connect(host='localhost', user='root', password='root', db='newsengine', charset='utf8')
    #file updating
    i = 0
    for news in contents:
        if news['url'] not in original_data.keys():
            i+=1
            original_data[news['url']]=news
            title = news['title'].replace("'","\\'").replace('"','\\"')
            article = news['article'].replace("'","\\'").replace('"','\\"')
            with conn.cursor() as cursor:
                sql_query = "INSERT INTO `new_news` (`title`,`date`,`url`,`category`,`article`) VALUES('"+title+"','"+str(today)+"','"+news['url']+"','"+news['category']+"','"+article+"')"    
                cursor.execute(sql_query)
            conn.commit()
    
    conn.close()
    '''
    with conn.cursor() as cursor:
        sql_query = "INSERT INTO `trans_log` (`id`,`date`,`type`,`number`) VALUES('')"    
        cursor.execute(sql_query)
   '''
    updated_json=[]
    for news in original_data:
        updated_json.append(news)
    
    return updated_json


def savetheDataForModel(original_data,updated_json):
    ## updated json file for the making model
    conn = pymysql.connect(host='localhost', user='root', password='root', db='newsengine', charset='utf8')
    for news in updated_json:
        if news['url'] not in original_data.keys():
              with conn.cursor() as cursor:
                   cursor.execute("INSERT INTO news(title,date,article,category,url) VALUES(%s,%s,%s,%s)",(news['title'],news['date'],news['article'],news['category'],news['url']))
                   con.commit()
    return    

def DeletetheDBItem(table):
    conn = pymysql.connect(host='localhost', user='root', password='root', db='newsengine', charset='utf8')
    with conn.cursor() as cursor:
        sql = 'DELETE FROM '+table
        cursor.execute(sql)
    conn.commit()
    conn.close()
    return

def insertDF(content):
    dictionary = {}

    DeletetheDBItem('idf')
    print('Start building the words dictionary..')
    for news in content:
        for word in word_tokenize(news['article'].lower()):
            if word not in dictionary.keys():
                dictionary[word] = 1
            else :
                dictionary[word] += 1

    conn = pymysql.connect(host='localhost', user='root', password='root', db='newsengine', charset='utf8')
    #file updating
    
    print('Finish')
    print('Start Inserting the Data')

    for word in dictionary.keys():
        number = dictionary[word]
        with conn.cursor() as cursor:
            sql_query = "INSERT INTO `idf` (`id`,`word`,`number`) VALUES("+str(0)+",'"+word+"','"+str(number)+"')"    
            cursor.execute(sql_query)
        conn.commit()
    conn.close()

    return

# 파일로드
original_data, newly_updated = getItemsFromFiles()

# 기존 new_news DB 삭제
DeletetheDBItem('new_news')

# json 파일 연결 및 DB 삽입
updated_json =InsertIntoDB(original_data,newly_updated)

#insertDF(updated_json)

# json 파일 저장  임시 파일 삭제
savetheDataForModel(original_data,updated_json)


