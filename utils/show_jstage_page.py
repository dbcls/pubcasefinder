# -*- coding: utf-8 -*-

import os
import re
import MySQLdb
import json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from utils.pagination import Pagination
from flask_babel import gettext,Babel

app = Flask(__name__)

app.secret_key = 'pubcasefinder1210'

# https://github.com/shibacow/flask_babel_sample/blob/master/srv.py
babel = Babel(app)
@babel.localeselector
def get_locale():
    if 'lang' not in session:
        session['lang'] = request.accept_languages.best_match(['ja', 'ja_JP', 'en'])
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')


#####
# DB設定
app.config.from_pyfile('../config.cfg')
db_sock = app.config['DBSOCK']
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


####
# フェノタイプのコンテキスト画面を表示
def show_jstage_page(id_disease, page, size):

    list_dict_jstage = []
    limit = int(size)
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    term_disease = ""

    if id_disease != "":

        # MONDO IDからtermを取得
        ## term_disease
        sql_OntoTerm = u"select OntoTerm from OntoTermMONDO where OntoType='label' and OntoID=%s"
        cursor_OntoTerm = OBJ_MYSQL.cursor()
        cursor_OntoTerm.execute(sql_OntoTerm, (id_disease,))
        values_OntoTerm = cursor_OntoTerm.fetchall()
        cursor_OntoTerm.close()
        term_disease = values_OntoTerm[0][0]

        # JStage書誌情報を取得
        sql_JStage = u"select a.id_jstage, a.title_ja, a.url_ja, a.pdate from JStage as a left join AnnotOntoMONDOJStage as b on a.id_jstage=b.id_jstage where b.id_mondo=%s order by a.pdate desc"

        cursor_JStage = OBJ_MYSQL.cursor()
        cursor_JStage.execute(sql_JStage, (id_disease,))
        values_JStage = cursor_JStage.fetchall()
        cursor_JStage.close()
        for value_JStage in values_JStage:
            id_jstage = value_JStage[0]
            title_ja  = value_JStage[1]
            url_ja    = value_JStage[2]
            pdate     = value_JStage[3]

            # htmlに渡す情報を収納
            dict_jstage = {}
            dict_jstage['id_jstage'] = id_jstage
            dict_jstage['title_ja'] = title_ja
            dict_jstage['url_ja'] = url_ja
            dict_jstage['pdate'] = pdate
            list_dict_jstage.append(dict_jstage)

    # total件数を取得
    total_hit = len(list_dict_jstage)
    pagination = Pagination(int(page), limit, total_hit)

    # ソート
    ## pyearでソート
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    #list_dict_phenotype_context_sorted = []
    #rank = 0
    #rank_deposit = 0
    #prev_sum_ic = 0
    #for dict_phenotype_context in sorted(list_dict_phenotype_context, key=lambda x: (-int(x['pyear']),x['title'])):
    #    list_dict_phenotype_context_sorted.append(dict_phenotype_context)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    #list_dict_phenotype_context_pagination = list_dict_phenotype_context_sorted[start:end]
    list_dict_jstage_pagination = list_dict_jstage[start:end]

    OBJ_MYSQL.close()

    #return term_disease, term_phenotype, list_dict_phenotype_context_pagination, pagination, total_hit, disease_definition, phenotype_definition
    return term_disease, list_dict_jstage_pagination, pagination, total_hit


