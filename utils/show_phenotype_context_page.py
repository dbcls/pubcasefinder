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
def show_phenotype_context_page(id_disease, id_phenotype, page, size):

    list_dict_phenotype_context = []
    limit = int(size)
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    term_disease = ""
    term_phenotype = ""
    disease_definition = ""
    phenotype_definition = ""

    if id_disease != "" and id_phenotype != "":

        # Disease definitionを取得
        sql_Orphanet = u"select DiseaseDefinition from Orphanet where OntoID=%s group by OntoID"
        cursor_Orphanet = OBJ_MYSQL.cursor()
        cursor_Orphanet.execute(sql_Orphanet, (id_disease,))
        values = cursor_Orphanet.fetchall()
        cursor_Orphanet.close()
        disease_definition = values[0][0] if values else ''

        # Phenotype definitionを取得
        sql_OntoTermHPInformation = u"select OntoDefinition from OntoTermHPInformation where OntoID=%s"
        cursor_OntoTermHPInformation = OBJ_MYSQL.cursor()
        cursor_OntoTermHPInformation.execute(sql_OntoTermHPInformation, (id_phenotype,))
        values = cursor_OntoTermHPInformation.fetchall()
        cursor_OntoTermHPInformation.close()
        phenotype_definition = values[0][0] if values else ''

        # idからtermを取得
        ## term_disease
        sql_OntoTerm = u"select OntoTerm from OntoTermORDO where OntoType='label' and OntoID=%s"
        cursor_OntoTerm = OBJ_MYSQL.cursor()
        cursor_OntoTerm.execute(sql_OntoTerm, (id_disease,))
        values_OntoTerm = cursor_OntoTerm.fetchall()
        cursor_OntoTerm.close()
        term_disease = values_OntoTerm[0][0]
        ## term_phenotype
        sql_OntoTermHP = u"select OntoTerm from OntoTermHP where OntoType='label' and OntoID=%s"
        cursor_OntoTermHP = OBJ_MYSQL.cursor()
        cursor_OntoTermHP.execute(sql_OntoTermHP, (id_phenotype,))
        values_OntoTermHP = cursor_OntoTermHP.fetchall()
        cursor_OntoTermHP.close()
        term_phenotype = values_OntoTermHP[0][0]

        # contextを取得
        sql_AnnotOntoORDOHP = u"select a.id, a.PMID, a.OntoIDORDO, b.BibType, b.SentenceNo, b.OntoStartInSentence, b.OntoEndInSentence, a.OntoIDHP, c.BibType, c.SentenceNo, c.OntoStartInSentence, c.OntoEndInSentence from AnnotOntoORDOHP as a left join AnnotOntoORDO as b on a.PointerORDO = b.id left join AnnotOntoHP as c on a.PointerHP = c.id where a.FlgCoLocation=1 and a.OntoIDORDO=%s and a.OntoIDHP=%s"
        cursor_AnnotOntoORDOHP = OBJ_MYSQL.cursor()
        cursor_AnnotOntoORDOHP.execute(sql_AnnotOntoORDOHP, (id_disease, id_phenotype,))
        values_AnnotOntoORDOHP = cursor_AnnotOntoORDOHP.fetchall()
        cursor_AnnotOntoORDOHP.close()
        for value_AnnotOntoORDOHP in values_AnnotOntoORDOHP:
            id_AnnotOntoORDOHP      = value_AnnotOntoORDOHP[0]
            PMID                    = value_AnnotOntoORDOHP[1]
            OntoIDORDO              = value_AnnotOntoORDOHP[2]
            BibTypeORDO             = value_AnnotOntoORDOHP[3]
            SentenceNoORDO          = value_AnnotOntoORDOHP[4]
            OntoStartInSentenceORDO = value_AnnotOntoORDOHP[5]
            OntoEndInSentenceORDO   = value_AnnotOntoORDOHP[6]
            OntoIDHP                = value_AnnotOntoORDOHP[7]
            BibTypeHP               = value_AnnotOntoORDOHP[8]
            SentenceNoHP            = value_AnnotOntoORDOHP[9]
            OntoStartInSentenceHP   = value_AnnotOntoORDOHP[10]
            OntoEndInSentenceHP     = value_AnnotOntoORDOHP[11]

            # contextを取得
            sql_BibText = u"select Sentence from BibText where PMID=%s and BibType=%s and SentenceNo=%s"
            cursor_BibText = OBJ_MYSQL.cursor()
            cursor_BibText.execute(sql_BibText, (PMID, BibTypeORDO, SentenceNoORDO,))
            values_BibText = cursor_BibText.fetchall()
            cursor_BibText.close()
            Sentence = values_BibText[0][0]

            # 書誌情報を取得
            sql_CaseReports = u"select PMCID, title, authors, so, pyear, journal, country, sex, age, inheritanceMode from CaseReports where PMID=%s"
            cursor_CaseReports = OBJ_MYSQL.cursor()
            cursor_CaseReports.execute(sql_CaseReports, (PMID,))
            values_CaseReports = cursor_CaseReports.fetchall()
            cursor_CaseReports.close()
            PMCID           = values_CaseReports[0][0]
            title           = values_CaseReports[0][1]
            authors         = values_CaseReports[0][2]
            so              = values_CaseReports[0][3]
            pyear           = values_CaseReports[0][4]
            journal         = values_CaseReports[0][5]
            country         = values_CaseReports[0][6]
            sex             = values_CaseReports[0][7]
            age             = values_CaseReports[0][8]
            inheritanceMode = values_CaseReports[0][9]

            # ageがHP IDなので、termに変換
            if age == "HP:0003623":
                age = "Infant, Newborn"
            elif age == "HP:0003593":
                age = "Infant"
            elif age == "HP:0011463":
                age = "Child"
            elif age == "HP:0003621":
                age = "Adolescent"
            elif age == "HP:0003581":
                age = "Adult"
            elif age == "HP:0011462":
                age = "Young Adult"
            elif age == "HP:0003596":
                age = "Middle Aged"
            elif age == "HP:0003584":
                age = "Aged"

            # contextのdiseaseとphenotypeに対してマークアップを挿入
            if OntoStartInSentenceORDO >= OntoStartInSentenceHP:
                Sentence = insert("</font></b>", Sentence, OntoEndInSentenceORDO + 1)
                Sentence = insert("<b><font color=#F73859>", Sentence, OntoStartInSentenceORDO)
                Sentence = insert("</font></b>", Sentence, OntoEndInSentenceHP + 1)
                Sentence = insert("<b><font color=#337ab7>", Sentence, OntoStartInSentenceHP)
            else:
                Sentence = insert("</font></b>", Sentence, OntoEndInSentenceHP + 1)
                Sentence = insert("<b><font color=#337ab7>", Sentence, OntoStartInSentenceHP)
                Sentence = insert("</font></b>", Sentence, OntoEndInSentenceORDO + 1)
                Sentence = insert("<b><font color=#F73859>", Sentence, OntoStartInSentenceORDO)


            # htmlに渡す情報を収納
            dict_phenotype_context = {}
            dict_phenotype_context['PMID']                    = PMID
            dict_phenotype_context['OntoIDORDO']              = OntoIDORDO
            dict_phenotype_context['BibTypeORDO']             = BibTypeORDO
            dict_phenotype_context['SentenceNoORDO']          = SentenceNoORDO
            dict_phenotype_context['OntoStartInSentenceORDO'] = OntoStartInSentenceORDO
            dict_phenotype_context['OntoEndInSentenceORDO']   = OntoEndInSentenceORDO
            dict_phenotype_context['OntoIDHP']                = OntoIDHP
            dict_phenotype_context['BibTypeHP']               = BibTypeHP
            dict_phenotype_context['SentenceNoHP']            = SentenceNoHP
            dict_phenotype_context['OntoStartInSentenceHP']   = OntoStartInSentenceHP
            dict_phenotype_context['OntoEndInSentenceHP']     = OntoEndInSentenceHP
            dict_phenotype_context['Sentence']                = Sentence
            dict_phenotype_context['PMCID']                   = PMCID
            dict_phenotype_context['title']                   = title
            dict_phenotype_context['authors']                 = authors
            dict_phenotype_context['so']                      = so
            dict_phenotype_context['pyear']                   = pyear
            dict_phenotype_context['journal']                 = journal
            dict_phenotype_context['country']                 = country
            dict_phenotype_context['sex']                     = sex
            dict_phenotype_context['age']                     = age
            dict_phenotype_context['inheritanceMode']         = inheritanceMode
            list_dict_phenotype_context.append(dict_phenotype_context)

    # total件数を取得
    total_hit = len(list_dict_phenotype_context)
    pagination = Pagination(int(page), limit, total_hit)

    # ソート
    ## pyearでソート
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    list_dict_phenotype_context_sorted = []
    rank = 0
    rank_deposit = 0
    prev_sum_ic = 0
    for dict_phenotype_context in sorted(list_dict_phenotype_context, key=lambda x: (-int(x['pyear']),x['title'])):
        list_dict_phenotype_context_sorted.append(dict_phenotype_context)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_phenotype_context_pagination = list_dict_phenotype_context_sorted[start:end]

    OBJ_MYSQL.close()

    return term_disease, term_phenotype, list_dict_phenotype_context_pagination, pagination, total_hit, disease_definition, phenotype_definition


#####
# contextの途中にマークアップを挿入するためのメソッドを定義
def insert(repl, string, pos):
    front = string[:pos]
    rear = string[pos:]
    return front+repl+rear

