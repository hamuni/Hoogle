
#-*- coding: utf-8 -*-

from flask import Flask, flash, render_template, redirect, url_for, request, session
from module.database import Database
from module import engine_doc2vec as Engine

app = Flask(__name__)
if __name__ == '__main__':
    db = Database()
    con = db.connect()
    cur = con.cursor()
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

    model = Engine.load_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signUp')
def signUp():
    if 'user_id' in session and session['user_id'] != None:
        return redirect(url_for('index'))
    else:
        return render_template('signUp.html')


@app.route('/signUpUser', methods=['POST'])
def signUpUser():
    if 'user_id' in session and session['user_id'] != None:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        user_id_form  = request.form['user_id']
        password_form  = request.form['password']
        passwordConfirm_form  = request.form['passwordConfirm']

        if not user_id_form or not password_form or not passwordConfirm_form:
            error = "입력하지 않은 항목이 존재합니다."
            return render_template('signUp.html', error=error)

        cur.execute("SELECT * FROM user WHERE user_id = %s", (user_id_form)) # CHECKS IF USERNAME EXSIST
        if cur.fetchone() != None:
            error = "이미 존재하는 ID"
            return render_template('signUp.html', error=error)

        if password_form != passwordConfirm_form:
            error = "비밀번호와 재입력한 비밀번호가 일치하지 않습니다."
            return render_template('signUp.html', error=error)

        success = db.sign_up(user_id_form, password_form)

        if success:
            return render_template('index.html')
        else:
            error = "정상처리되지 않았습니다."
            return render_template('index.html', error=error)


@app.route('/login')
def loginPage():
    if 'user_id' in session and session['user_id'] != None:
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session['user_id'] = None
    return redirect(url_for('index'))

@app.route('/loginUser', methods=['POST'])
def loginUser():
    if 'user_id' in session and session['user_id'] != None:
        return redirect(url_for('index'))

    error = None
    if request.method != 'POST':
        return redirect(url_for('index'))

    user_id_form  = request.form['user_id']
    password_form  = request.form['password']

    if not user_id_form or not password_form:
        error = "입력하지 않은 항목이 존재합니다."
        return render_template('login.html', error=error)

    cur.execute("SELECT * FROM user WHERE user_id = %s",(user_id_form))
    if cur.fetchone() == None: #아이디 존재여부 확인
        error = "존재하지 않는 ID"
        return render_template('login.html', error=error)

    cur.execute("SELECT * FROM user WHERE user_id = %s",(user_id_form))
    data = cur.fetchone()
    if password_form == data['password']: #비밀번호 일치
        session['user_id'] = request.form['user_id']
        return redirect(url_for('index'))
    else:
        error = "비밀번호가 일치하지 않습니다."
        return render_template('login.html', error=error)



@app.route('/search', methods=['GET'])
def search():
    error = None
    if request.method == 'GET':
        str_query = request.args.get('query')
        if not str_query:
            empty = list()
            return render_template('search.html', data=empty)

        #로그인 한 상태에서 검색한 경우, 쿼리 히스토리 저장
        if 'user_id' in session and session['user_id'] != None:
            db.insert_query_history(session['user_id'], str_query)

        token_query = Engine.tokenizeQuery(str_query)
        removed_stopwords_query = Engine.removeStopwords(token_query)
        Idf = db.select_idf_values(removed_stopwords_query)

        #토큰 수 두 개 이하의 쿼리는 유저 관심도 및 텀프리퀀시 중심으로 가중치 반영
        if len(removed_stopwords_query) > 2:
            WEIGHT_SIMILARITY = 4.0
            WEIGHT_LATEST = 1.0
            WEIGHT_CATEGORY = 0.3
            WEIGHT_USER_INTEREST = 0.4
            WEIGHT_TERM_FREQUENCY = 0.3
            WEIGHT_ADDNEWEST = 1.0
            WEIGHT_IDF=1.0
        else:
            WEIGHT_SIMILARITY = 2.4
            WEIGHT_LATEST = 1.0
            WEIGHT_CATEGORY = 0.1
            WEIGHT_USER_INTEREST = 2.0
            WEIGHT_TERM_FREQUENCY = 1.6
            WEIGHT_ADDNEWEST = 1.0
            WEIGHT_IDF = 1.0

        news_and_weight = db.get_article_of_most_similar(model, token_query, WEIGHT_SIMILARITY)
        Engine.addWeightCategory(news_and_weight, str_query, WEIGHT_CATEGORY)
        Engine.addWeightLatest(news_and_weight, WEIGHT_LATEST)
        Engine.addWeightTermFrequency(news_and_weight, removed_stopwords_query, WEIGHT_TERM_FREQUENCY)
        Engine.addWeightIDF(news_and_weight,removed_stopwords_query,WEIGHT_IDF,Idf)

        if 'user_id' in session and session['user_id'] != None: #로그인 상태일 때만 유저관심사 적용
            user_id = session['user_id']
            query_history_list = db.select_query_history(user_id)
            query_list = [query_history['query'] for query_history in query_history_list]
            if len(query_list) > 3: # 로그인 한 상태로 4번 이상 검색히스토리가 있을 경우에만 적용
                predicted_category = Engine.predictUserInterest(query_list)
                Engine.addWeightUserInterest(news_and_weight, predicted_category, WEIGHT_USER_INTEREST)

        #tfidf_latest_news = Engine.tfidfAtLatestNews(new_content, input_query, 2)
        #if news_and_weight != None:
        #    print('\n Latest News TF-IDF:')
        #    for idx, news_weight in enumerate(tfidf_latest_news[:2]):
        #        news = news_weight.getNews()
        #        print("%d." % (idx+1)," %s" % news['date']," %s" % news['title']," %s" % news['category'], " score: %f" % news_weight.getWeight())

        Engine.sortingByWeight(news_and_weight)
        sorted_news = [ nw.getNews() for nw in news_and_weight ]
    return render_template('search.html', data=sorted_news)

@app.route('/queryHistory')
def query_history():
    if not 'user_id' in session or session['user_id'] == None:
        return redirect(url_for('index'))

    user_id = session['user_id']
    query_history_list = db.select_query_history(user_id)
    query_list = [query_history['query'] for query_history in query_history_list]
    #5번 이상 검색히스토리가 있을 경우에 관심사를 분류
    if len(query_list) > 4:
        predicted_category = Engine.predictUserInterest(query_list)
        category_name = set(predicted_category)
        category_count = {}
        for category in category_name:
            category_count[category] = (predicted_category == category).sum()
        print(category_count)
    return render_template('queryHistory.html', data=query_history_list)

@app.route('/make_model')
def make_model():
    from module import make_model_doc2vec as EngineMaker
    whole_news = db.get_whole_news()

    if whole_news != False:
        EngineMaker.make_model(whole_news)
    return redirect(url_for('index'))

@app.route('/make_classifier')
def make_classifier():
    from module import make_model_LSTM_classifier as ClassifierMaker
    whole_news = db.get_whole_news()

    if whole_news != False:
        ClassifierMaker.make_classifier(whole_news)
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html')

if __name__ == '__main__':
    app.run(debug = True, port=80, host="127.0.0.1")
