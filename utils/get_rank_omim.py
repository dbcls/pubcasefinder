# -*- coding: utf-8 -*-

import os
import re
import MySQLdb

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


#####
# get rank omim
def get_rank_omim(str_phenotypes):
    list_phenotypes = str_phenotypes.split(",")

    # MySQL接続　初期設定
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")

    ## OntoTermテーブルからOMIMの全termを取得
    dict_OntoTerm_omim = {}
    sql_OntoTerm_omim = u"select distinct OntoID, OntoTerm from OntoTermOMIM where OntoType='label'"
    cursor_OntoTerm_omim = OBJ_MYSQL.cursor()
    cursor_OntoTerm_omim.execute(sql_OntoTerm_omim)
    values = cursor_OntoTerm_omim.fetchall()
    cursor_OntoTerm_omim.close()
    for value in values:
        dict_OntoTerm_omim[value[0]] = value[1]

    # OMIMテーブルから情報取得
    ## 各疾患ごとのアノテーションHPO数
    ## 各疾患ごとのアノテーションHPOの合計IC
    dict_AnnotationHPONum     = {}
    dict_AnnotationHPOSumIC   = {}
    sql_OMIM = u"select distinct OntoID, AnnotationHPONum, AnnotationHPOSumIC from OMIM"
    cursor_OMIM = OBJ_MYSQL.cursor()
    cursor_OMIM.execute(sql_OMIM)
    values = cursor_OMIM.fetchall()
    cursor_OMIM.close()
    for value in values:
        onto_id              = value[0]
        AnnotationHPONum     = value[1]
        AnnotationHPOSumIC   = value[2]
        dict_AnnotationHPONum[onto_id]     = AnnotationHPONum
        dict_AnnotationHPOSumIC[onto_id]   = AnnotationHPOSumIC

        
    # OntoTermHPテーブルまたはOntoTermHPInformationテーブルからHPの全termを取得
    ## localeがenの場合はOntoTermHPから英語のHPO termを取得
    ## localeがenでない場合はOntoTermHPInformationから日本語のHPO termを取得 
    dict_OntoTerm_hp = {}
    sql_OntoTerm_hp = ""
    if get_locale() == "ja" or get_locale() == "ja_JP":
        sql_OntoTerm_hp = u"select distinct OntoID, OntoName, OntoNameJa from OntoTermHPInformation"
    else:
        sql_OntoTerm_hp = u"select distinct OntoID, OntoTerm from OntoTermHP where OntoType='label'"
    cursor_OntoTerm_hp = OBJ_MYSQL.cursor()
    cursor_OntoTerm_hp.execute(sql_OntoTerm_hp)
    values = cursor_OntoTerm_hp.fetchall()
    cursor_OntoTerm_hp.close()
    if get_locale() == "ja" or get_locale() == "ja_JP":
        for value in values:
            dict_OntoTerm_hp[value[0]] = value[1] if value[2]=="" else value[2]
    else:
        for value in values:
            dict_OntoTerm_hp[value[0]] = value[1]


    ## ICテーブルから全HPO termのICを取得
    dict_IC = {}
    sql_IC = u"select OntoID, IC from IC where OntoName='HP'"
    cursor_IC = OBJ_MYSQL.cursor()
    cursor_IC.execute(sql_IC)
    values = cursor_IC.fetchall()
    cursor_IC.close()
    for value in values:
        onto_id_omim = value[0]
        ic = value[1]
        dict_IC[onto_id_omim] = ic

        
    ####
    ## 各疾患とのスコアを算出し、データを収納
    ### インデックステーブルを利用して、各疾患でのICの合計を取得
    ### http://stackoverflow.com/questions/4574609/executing-select-where-in-using-mysqldb
    #sql = u"select OntoIDOMIM, IndexOntoIDHP, DiseaseOntoIDHP, DiseaseOntoIDHPSource, CommonRootHP, CommonRootHPIC from IndexDiseaseHPOMIM where IndexOntoIDHP in (%s) order by OntoIDOMIM, DiseaseOntoIDHP"
    sql = u"select a.OntoIDOMIM, a.IndexOntoIDHP, a.DiseaseOntoIDHP, a.DiseaseOntoIDHPSource, a.CommonRootHP, a.CommonRootHPIC, (b.IC - a.CommonRootHPIC) from IndexDiseaseHPOMIM as a left join IC as b on a.IndexOntoIDHP=b.OntoID where a.IndexOntoIDHP in (%s) and b.OntoName='HP' order by a.OntoIDOMIM, (b.IC - a.CommonRootHPIC)"
    in_p=', '.join(map(lambda x: '%s', list_phenotypes))
    sql = sql % in_p
    cursor = OBJ_MYSQL.cursor()
    cursor.execute(sql, list_phenotypes)
    values = cursor.fetchall()
    cursor.close()

    ####
    ## データを収納
    list_dict_similar_disease = []
    dict_similar_diseases = {}
    dict_over_thres_count = {}
    # default
    #thres_delta_ic, thres_count, thres_weight = 0, 0, 1
    # t10
    thres_delta_ic, thres_count, thres_weight = 7.5, 3, 0.25

    for value in values:
        onto_id_omim              = value[0]
        onto_id_hp_index          = value[1]
        onto_id_hp_disease        = value[2]
        onto_id_hp_disease_source = value[3]
        onto_id_hp_common_root    = value[4]
        ic                        = 0 if value[5] == "" else float(value[5])
        delta_ic                  = float(value[6])
        weight = 1

        # 入力HPOとCommonHPOの差分カウントおよびカウント回数の条件を満たした場合のweight設定
        if onto_id_omim not in dict_over_thres_count:
            dict_over_thres_count[onto_id_omim] = 0
        if delta_ic < thres_delta_ic:
            dict_over_thres_count[onto_id_omim] += 1
        if delta_ic >= thres_delta_ic and dict_over_thres_count[onto_id_omim] >= thres_count:
            weight = thres_weight

        if onto_id_omim in dict_similar_diseases:
            onto_term_hp_disease = dict_OntoTerm_hp[onto_id_hp_disease] if onto_id_hp_disease in dict_OntoTerm_hp else ""
            dict_id_term_hp_disease = {}
            dict_id_term_hp_disease['onto_id_hp_disease'] = onto_id_hp_disease
            dict_id_term_hp_disease['onto_term_hp_disease'] = onto_term_hp_disease
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_disease']).append(onto_id_hp_disease)
            (dict_similar_diseases[onto_id_omim]['onto_id_term_hp_disease']).append(dict_id_term_hp_disease)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_disease_source']).append(onto_id_hp_disease_source)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_diseases[onto_id_omim]['onto_term_hp_disease']).append(onto_term_hp_disease)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_omim]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_omim]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_omim]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_omim]['sum_ic_denominator'] += 0
        else:
            dict_similar_diseases[onto_id_omim] = {}
            dict_similar_diseases[onto_id_omim]['onto_id_hp_index']          = []
            dict_similar_diseases[onto_id_omim]['onto_id_hp_disease']        = []
            dict_similar_diseases[onto_id_omim]['onto_id_term_hp_disease']   = []
            dict_similar_diseases[onto_id_omim]['onto_id_hp_disease_source'] = []
            dict_similar_diseases[onto_id_omim]['onto_id_hp_common_root']    = []
            dict_similar_diseases[onto_id_omim]['onto_term_hp_disease']      = []
            dict_similar_diseases[onto_id_omim]['sum_ic']                    = 0
            dict_similar_diseases[onto_id_omim]['sum_ic_denominator']        = 0

            onto_term_hp_disease = dict_OntoTerm_hp[onto_id_hp_disease] if onto_id_hp_disease in dict_OntoTerm_hp else ""
            dict_id_term_hp_disease = {}
            dict_id_term_hp_disease['onto_id_hp_disease'] = onto_id_hp_disease
            dict_id_term_hp_disease['onto_term_hp_disease'] = onto_term_hp_disease
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_disease']).append(onto_id_hp_disease)
            (dict_similar_diseases[onto_id_omim]['onto_id_term_hp_disease']).append(dict_id_term_hp_disease)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_disease_source']).append(onto_id_hp_disease_source)
            (dict_similar_diseases[onto_id_omim]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_diseases[onto_id_omim]['onto_term_hp_disease']).append(onto_term_hp_disease)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_omim]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_omim]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_omim]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_omim]['sum_ic_denominator'] += 0


    ####
    # 類似疾患検索結果を収納
    for onto_id_omim in dict_similar_diseases.keys():

        # IndexDiseaseHPOMIMの中に、オントロジーには含まれないOMIM IDが含まれているため、それらの処理を飛ばす
        ## TODO: 実際は、IndexDiseaseHPOMIM関連から、データの作成時にそれらのOMIM IDを除く必要がある。 20180913 藤原
        if onto_id_omim not in dict_AnnotationHPONum:
            continue

        dict_similar_disease = {}
        dict_similar_disease['onto_id_omim']              = onto_id_omim
        ## 関連Phenotypes
        dict_similar_disease['sum_ic']                    = dict_similar_diseases[onto_id_omim]['sum_ic']
        dict_similar_disease['sum_ic_denominator']        = dict_similar_diseases[onto_id_omim]['sum_ic_denominator']
        if dict_similar_diseases[onto_id_omim]['sum_ic_denominator'] != 0:
            dict_similar_disease['match_score']           = float(dict_similar_diseases[onto_id_omim]['sum_ic'] / dict_similar_diseases[onto_id_omim]['sum_ic_denominator'])
        else:
            dict_similar_disease['match_score'] = 0
        dict_similar_disease['onto_id_hp_index']          = ",".join(dict_similar_diseases[onto_id_omim]['onto_id_hp_index'])
        dict_similar_disease['onto_id_hp_disease']        = ",".join(dict_similar_diseases[onto_id_omim]['onto_id_hp_disease'])
        dict_similar_disease['onto_id_term_hp_disease']   = sorted(dict_similar_diseases[onto_id_omim]['onto_id_term_hp_disease'], key=lambda x: x['onto_term_hp_disease'])
        dict_similar_disease['onto_id_hp_disease_source'] = ",".join(dict_similar_diseases[onto_id_omim]['onto_id_hp_disease_source'])
        dict_similar_disease['onto_id_hp_common_root']    = ",".join(dict_similar_diseases[onto_id_omim]['onto_id_hp_common_root'])
        dict_similar_disease['onto_term_hp_disease']      = ",".join(dict_similar_diseases[onto_id_omim]['onto_term_hp_disease'])
        ## HPOアノテーション数とHPOアノテーション合計IC
        dict_similar_disease['annotation_hp_num']        = dict_AnnotationHPONum[onto_id_omim]
        dict_similar_disease['annotation_hp_sum_ic']     = dict_AnnotationHPOSumIC[onto_id_omim]

        list_dict_similar_disease.append(dict_similar_disease)

        
    ####
    # スコアを基にランキングを作成
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    ## スコアが同一の場合は、以下の値でランキング
    ### アノテーションされたHPOの数
    ### アノテーションされたHPOのICの合計値
    list_dict_similar_disease_sorted = []
    rank = 0
    rank_deposit = 0
    prev_match_score = 0
    for dict_similar_disease in sorted(list_dict_similar_disease, key=lambda x: (-float(x['match_score']),int(x['annotation_hp_num']),-float(x['annotation_hp_sum_ic']))):

        if dict_similar_disease['match_score'] != prev_match_score:
            rank = rank + 1 + rank_deposit 
            dict_similar_disease['rank'] = rank
            prev_match_score = dict_similar_disease['match_score']
            rank_deposit = 0
        else:
            dict_similar_disease['rank'] = rank
            prev_match_score = dict_similar_disease['match_score']
            rank_deposit += 1

        list_dict_similar_disease_sorted.append(dict_similar_disease)

    app.logger.error('finish')

    return list_dict_similar_disease_sorted

