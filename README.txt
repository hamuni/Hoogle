*웹 환경
Flask (version 0.13)
MySQL

*구동 전 준비사항
- Flask, MySQL 설치
- Python gensim,pymysql 라이브러리 설치
- DB Import. 함께 압축한 newsengine.sql을 자신의 MySQL에 Import (크롤링한 뉴스는 모두 DB에 저장)
- 프로젝트경로/module/database.py를 텍스트에디터로 열어서 상단에 MySQL DB정보를 입력해주시기 바랍니다.
(저희는 user='root', password='', db='newsengine' 로 설정하였습니다.)


*웹서버 구동 명령어
프로젝트경로# python server.py runserver

(크롤러는 프로젝트경로/module/newsCrawler# runCralwer.sh 를 통해 구동)
