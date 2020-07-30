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


####
# 類似症例検索画面を表示
def show_search_case_page(phenotypes_remove_error_ja, genes_remove_error, page, size):

    limit = int(size)

    #####
    # 類似疾患検索
    list_dict_similar_case = search_similar_case(phenotypes_remove_error_ja, genes_remove_error)

    # total件数を取得
    total_hit = len(list_dict_similar_case)
    pagination = Pagination(int(page), limit, total_hit)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_similar_case_pagination = list_dict_similar_case[start:end]

    return list_dict_similar_case_pagination, pagination, total_hit


#####
# search similar case
def search_similar_case(str_phenotypes, str_genes):
    list_phenotypes = str_phenotypes.split(",")
    list_genes      = str_genes.split(",")
    dict_genes = {}
    for gene in list_genes:
        dict_genes[gene] = 1

    # MySQL接続　初期設定
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")


    ## OpenCaseテーブルから情報取得
    ### 症例ID
    ### ソースURL
    ### 症例に対するHPOのアノテーション数
    ### 症例に対するHPOのアノテーション合計IC
    dict_source             = {}
    dict_AnnotationHPONum   = {}
    dict_AnnotationHPOSumIC = {}
    sql_OpenCase = u"select distinct CaseID, Source, AnnotationHPONum, AnnotationHPOSumIC from OpenCase"
    cursor_OpenCase = OBJ_MYSQL.cursor()
    cursor_OpenCase.execute(sql_OpenCase)
    values = cursor_OpenCase.fetchall()
    cursor_OpenCase.close()
    for value in values:
        case_id            = value[0]
        source             = value[1]
        AnnotationHPONum   = value[2]
        AnnotationHPOSumIC = value[3]

        if "MyGene2" in source:
            dict_source[case_id] = source.replace('api/public/family/fullprofile', 'familyprofile') + "/profile"
        else:
            dict_source[case_id] = source
        dict_AnnotationHPONum[case_id]   = AnnotationHPONum
        dict_AnnotationHPOSumIC[case_id] = AnnotationHPOSumIC


    ## OntoTermHPテーブルまたはOntoTermHPInformationテーブルからHPの全termを取得
    ### localeがenの場合はOntoTermHPから英語のHPO termを取得
    ### localeがenでない場合はOntoTermHPInformationから日本語のHPO termを取得 
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
        case_id = value[0]
        ic      = value[1]
        dict_IC[case_id] = ic

        
    ####
    ## 各疾患とのスコアを算出し、データを収納
    ### インデックステーブルを利用して、各疾患でのICの合計を取得
    ### http://stackoverflow.com/questions/4574609/executing-select-where-in-using-mysqldb
    #### mysql> desc IndexCaseHP;
    #### +--------------------+------------------+------+-----+---------+----------------+
    #### | Field              | Type             | Null | Key | Default | Extra          |
    #### +--------------------+------------------+------+-----+---------+----------------+
    #### | id                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    #### | CaseID             | varchar(300)     | NO   | MUL | NULL    |                |
    #### | CaseOntoIDHP       | varchar(300)     | NO   | MUL | NULL    |                |
    #### | CaseOntoIDHPSource | varchar(30)      | NO   | MUL | NULL    |                |
    #### | IndexOntoIDHP      | varchar(300)     | NO   | MUL | NULL    |                |
    #### | CommonRootHP       | varchar(300)     | NO   | MUL | NULL    |                |
    #### | CommonRootHPIC     | varchar(300)     | NO   |     | NULL    |                |
    #### +--------------------+------------------+------+-----+---------+----------------+
    sql = u"select a.CaseID, a.IndexOntoIDHP, a.CaseOntoIDHP, a.CaseOntoIDHPSource, a.CommonRootHP, a.CommonRootHPIC, (b.IC - a.CommonRootHPIC) from IndexCaseHP as a left join IC as b on a.IndexOntoIDHP=b.OntoID where a.IndexOntoIDHP in (%s) and b.OntoName='HP' order by a.CaseID, (b.IC - a.CommonRootHPIC)"
    in_p=', '.join(map(lambda x: '%s', list_phenotypes))
    sql = sql % in_p
    cursor = OBJ_MYSQL.cursor()
    cursor.execute(sql, list_phenotypes)
    values = cursor.fetchall()
    cursor.close()


    ####
    ## データを収納
    list_dict_similar_case = []
    dict_similar_cases = {}
    dict_over_thres_count = {}
    # t10
    thres_delta_ic, thres_count, thres_weight = 7.5, 3, 0.25

    for value in values:
        case_id                = value[0]
        onto_id_hp_index       = value[1]
        onto_id_hp_case        = value[2]
        onto_id_hp_case_source = value[3]
        onto_id_hp_common_root = value[4]
        ic                     = 0 if value[5] == "" else float(value[5])
        delta_ic               = float(value[6])
        weight                 = 1

        # 入力HPOとCommonHPOの差分カウントおよびカウント回数の条件を満たした場合のweight設定
        if case_id not in dict_over_thres_count:
            dict_over_thres_count[case_id] = 0
        if delta_ic < thres_delta_ic:
            dict_over_thres_count[case_id] += 1
        if delta_ic >= thres_delta_ic and dict_over_thres_count[case_id] >= thres_count:
            weight = thres_weight

        if case_id in dict_similar_cases:
            onto_term_hp_case = dict_OntoTerm_hp[onto_id_hp_case] if onto_id_hp_case in dict_OntoTerm_hp else ""
            dict_id_term_hp_case = {}
            dict_id_term_hp_case['onto_id_hp_case'] = onto_id_hp_case
            dict_id_term_hp_case['onto_term_hp_case'] = onto_term_hp_case
            (dict_similar_cases[case_id]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_cases[case_id]['onto_id_hp_case']).append(onto_id_hp_case)
            (dict_similar_cases[case_id]['onto_id_term_hp_case']).append(dict_id_term_hp_case)
            (dict_similar_cases[case_id]['onto_id_hp_case_source']).append(onto_id_hp_case_source)
            (dict_similar_cases[case_id]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_cases[case_id]['onto_term_hp_case']).append(onto_term_hp_case)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_cases[case_id]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_cases[case_id]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_cases[case_id]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_cases[case_id]['sum_ic_denominator'] += 0
        else:
            dict_similar_cases[case_id] = {}
            dict_similar_cases[case_id]['onto_id_hp_index']       = []
            dict_similar_cases[case_id]['onto_id_hp_case']        = []
            dict_similar_cases[case_id]['onto_id_term_hp_case']   = []
            dict_similar_cases[case_id]['onto_id_hp_case_source'] = []
            dict_similar_cases[case_id]['onto_id_hp_common_root'] = []
            dict_similar_cases[case_id]['onto_term_hp_case']      = []
            dict_similar_cases[case_id]['sum_ic']                 = 0
            dict_similar_cases[case_id]['sum_ic_denominator']     = 0

            onto_term_hp_case = dict_OntoTerm_hp[onto_id_hp_case] if onto_id_hp_case in dict_OntoTerm_hp else ""
            dict_id_term_hp_case = {}
            dict_id_term_hp_case['onto_id_hp_case'] = onto_id_hp_case
            dict_id_term_hp_case['onto_term_hp_case'] = onto_term_hp_case
            (dict_similar_cases[case_id]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_cases[case_id]['onto_id_hp_case']).append(onto_id_hp_case)
            (dict_similar_cases[case_id]['onto_id_term_hp_case']).append(dict_id_term_hp_case)
            (dict_similar_cases[case_id]['onto_id_hp_case_source']).append(onto_id_hp_case_source)
            (dict_similar_cases[case_id]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_cases[case_id]['onto_term_hp_case']).append(onto_term_hp_case)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_cases[case_id]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_cases[case_id]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_cases[case_id]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_cases[case_id]['sum_ic_denominator'] += 0


    # CaseGeneテーブルから各症例に紐づけられた遺伝子のなかで，ユーザが指定した遺伝子を疾患原因遺伝子を取得
    dict_case_gene = {}
    sql_CaseGene = u"select CaseID, EntrezID, Symbol, SymbolSynonym from CaseGene"
    cursor_CaseGene = OBJ_MYSQL.cursor()
    cursor_CaseGene.execute(sql_CaseGene)
    values = cursor_CaseGene.fetchall()
    cursor_CaseGene.close()
    for value in values:
        case_id        = value[0]
        entrez_id      = value[1]
        symbol         = value[2]
        symbol_synonym = value[3]

        # ユーザが指定した遺伝子のみ収納
        if entrez_id not in dict_genes:
            continue

        if case_id in dict_case_gene:
            dict_case_symbol_synonym = {}
            dict_case_symbol_synonym['entrez_id']      = entrez_id
            dict_case_symbol_synonym['symbol']         = symbol
            dict_case_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_case_gene[case_id]['case_symbol_synonym']).append(dict_case_symbol_synonym)
        else:
            dict_case_gene[case_id] = {}
            dict_case_gene[case_id]['case_symbol_synonym'] = []
            dict_case_symbol_synonym = {}
            dict_case_symbol_synonym['entrez_id']      = entrez_id
            dict_case_symbol_synonym['symbol']         = symbol
            dict_case_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_case_gene[case_id]['case_symbol_synonym']).append(dict_case_symbol_synonym)

    # ユーザが指定した遺伝子を疾患原因遺伝子に持つ症例をCaseGeneテーブルから取得
    dict_filter_case_gene = {}
    if str_genes != "":
        sql_CaseGene = u"select CaseID, EntrezID, Symbol, SymbolSynonym from CaseGene where EntrezID in (%s)"
        in_p=', '.join(map(lambda x: '%s', list_genes))
        sql_CaseGene = sql_CaseGene % in_p
        cursor_CaseGene = OBJ_MYSQL.cursor()
        cursor_CaseGene.execute(sql_CaseGene, list_genes)
        values = cursor_CaseGene.fetchall()
        cursor_CaseGene.close()
        for value in values:
            case_id        = value[0]
            entrez_id      = value[1]
            symbol         = value[2]
            symbol_synonym = value[3]

            if case_id in dict_filter_case_gene:
                dict_case_symbol_synonym = {}
                dict_case_symbol_synonym['entrez_id']      = entrez_id
                dict_case_symbol_synonym['symbol']         = symbol
                dict_case_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_case_gene[case_id]['case_symbol_synonym']).append(dict_case_symbol_synonym)
            else:
                dict_filter_case_gene[case_id] = {}
                dict_filter_case_gene[case_id]['case_symbol_synonym'] = []
                dict_case_symbol_synonym = {}
                dict_case_symbol_synonym['entrez_id']      = entrez_id
                dict_case_symbol_synonym['symbol']         = symbol
                dict_case_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_case_gene[case_id]['case_symbol_synonym']).append(dict_case_symbol_synonym)

    OBJ_MYSQL.close()

    ####
    # 類似疾患検索結果を収納
    for case_id in dict_similar_cases.keys():

        # IndexCaseHPの中に、オントロジーには含まれないCase IDが含まれているため、それらの処理を飛ばす
        if case_id not in dict_AnnotationHPONum:
            continue

        # ユーザが入力したgenesでフィルタリング
        if str_genes != "" and not case_id in dict_filter_case_gene:
            continue

        dict_similar_case                           = {}
        dict_similar_case['case_id']                = case_id
        ## 関連Phenotypes
        dict_similar_case['sum_ic']                 = dict_similar_cases[case_id]['sum_ic']
        dict_similar_case['sum_ic_denominator']     = dict_similar_cases[case_id]['sum_ic_denominator']
        ## 類似度スコア計算
        if dict_similar_cases[case_id]['sum_ic_denominator'] != 0:
            dict_similar_case['match_score'] = float(dict_similar_cases[case_id]['sum_ic'] / dict_similar_cases[case_id]['sum_ic_denominator'])
        else:
            dict_similar_case['match_score'] = 0
        ## 症例情報
        dict_similar_case['source']                 = dict_source[case_id]
        dict_similar_case['onto_id_hp_index']       = ",".join(dict_similar_cases[case_id]['onto_id_hp_index'])
        dict_similar_case['onto_id_hp_case']        = ",".join(dict_similar_cases[case_id]['onto_id_hp_case'])
        dict_similar_case['onto_id_term_hp_case']   = sorted(dict_similar_cases[case_id]['onto_id_term_hp_case'], key=lambda x: x['onto_term_hp_case'])
        dict_similar_case['onto_id_hp_case_source'] = ",".join(dict_similar_cases[case_id]['onto_id_hp_case_source'])
        dict_similar_case['onto_id_hp_common_root'] = ",".join(dict_similar_cases[case_id]['onto_id_hp_common_root'])
        dict_similar_case['onto_term_hp_case']      = ",".join(dict_similar_cases[case_id]['onto_term_hp_case'])
        ## 関連Genes/Variants
        dict_similar_case['case_symbol_synonym']    = sorted(dict_case_gene[case_id]['case_symbol_synonym'], key=lambda x: x['symbol']) if case_id in dict_case_gene else []
        ## HPOアノテーション数とHPOアノテーション合計IC
        dict_similar_case['annotation_hp_num']      = dict_AnnotationHPONum[case_id]
        dict_similar_case['annotation_hp_sum_ic']   = dict_AnnotationHPOSumIC[case_id]

        list_dict_similar_case.append(dict_similar_case)

        
    ####
    # スコアを基にランキングを作成
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    ## スコアが同一の場合は、以下の値でランキング
    ### アノテーションされたHPOの数
    ### アノテーションされたHPOのICの合計値
    list_dict_similar_case_sorted = []
    rank = 0
    rank_deposit = 0
    prev_match_score = 0
    for dict_similar_case in sorted(list_dict_similar_case, key=lambda x: (-float(x['match_score']),int(x['annotation_hp_num']),-float(x['annotation_hp_sum_ic']))):
        if dict_similar_case['match_score'] != prev_match_score:
            rank = rank + 1 + rank_deposit 
            dict_similar_case['rank'] = rank
            prev_match_score = dict_similar_case['match_score']
            rank_deposit = 0
        else:
            dict_similar_case['rank'] = rank
            prev_match_score = dict_similar_case['match_score']
            rank_deposit += 1

        list_dict_similar_case_sorted.append(dict_similar_case)

    return list_dict_similar_case_sorted

