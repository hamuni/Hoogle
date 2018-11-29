
import pymysql
import gzip
from datetime import date
import pandas as pd
from module import engine_doc2vec as engine

class Database:
    def connect(self):
        return pymysql.connect(host='localhost', user='root', password='', db='newsengine', charset='utf8', cursorclass=pymysql.cursors.DictCursor)

    def sign_up(self, user_id, password):
        con = Database.connect(self)
        cursor = con.cursor()
        try:
            cursor.execute("INSERT INTO user(user_id, password) VALUES(%s,%s)", (user_id, password))
            con.commit()
            return True
        except:
            con.rollback()
            return False
        finally:
            con.close()

    def get_article_of_most_similar(self, model, str_query, weight):
        con = Database.connect(self)
        cursor = con.cursor()

        translated_similar_news = list()
        similar_news = engine.get_similar_news(model, str_query, 300)
        try:
            for s in similar_news:
                url = s[0]
                similarity = s[1]
                cursor.execute("SELECT * FROM news where url = %s", (url))
                news_from_db = cursor.fetchone()
                news_and_weight = engine.makeNewsAndWeight(news_from_db, similarity * weight)
                translated_similar_news.append(news_and_weight)

            con.commit()
            return translated_similar_news
        except:
            con.rollback()
            return None
        finally:
            con.close()
        return translated_similar_news

    def insert_query_history(self, user_id, query):
        con = Database.connect(self)
        cursor = con.cursor()
        try:
            cursor.execute("INSERT INTO query_history(user_id, query) VALUES(%s,%s)", (user_id, query))
            con.commit()
            return True
        except:
            con.rollback()
            return False
        finally:
            con.close()

    def select_query_history(self, user_id):
        con = Database.connect(self)
        cursor = con.cursor()
        try:
            cursor.execute("SELECT * FROM query_history WHERE user_id = %s ORDER BY reg_date DESC", (user_id))
            return cursor.fetchall()
        except:
            con.rollback()
            return False
        finally:
            con.close()

    def select_idf_values(self, tokenizedQuery):
        con = Database.connect(self)
        cursor = con.cursor()
        try:
            word_Df={}
            for word in tokenizedQuery:
                cursor.execute("SELECT number FROM idf where word = %s", (word))
                data = cursor.fetchone()
                if data == None:
                    word_Df[word] = 1
                else:
                    word_Df[word] = data['number']
            return word_Df
        except:
            con.rollback()
            return False
        finally:
            con.close()


################ Make Doc2Vec Model ###############
    def get_whole_news(self):
        con = Database.connect(self)
        cursor = con.cursor()
        try:
            cursor.execute("SELECT * FROM news")
            return cursor.fetchall()
        except:
            con.rollback()
            return False
        finally:
            con.close()
