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
def show_search_gene_page(phenotypes_remove_error_ja, genes_remove_error, page, size):

    limit = int(size)

    #####
    # 類似疾患検索
    list_dict_similar_gene = search_similar_gene(phenotypes_remove_error_ja, genes_remove_error)

    # total件数を取得
    total_hit = len(list_dict_similar_gene)
    pagination = Pagination(int(page), limit, total_hit)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_similar_gene_pagination = list_dict_similar_gene[start:end]

    return list_dict_similar_gene_pagination, pagination, total_hit


#####
# search similar gene
def search_similar_gene(str_phenotypes, str_genes):
    list_phenotypes = str_phenotypes.split(",")
    list_genes      = str_genes.split(",")
    dict_genes = {}
    for gene in list_genes:
        dict_genes[gene] = 1

    # MySQL接続　初期設定
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")


    ####
    # OMIMテーブルから疾患情報を取得
    dict_omim_orphanet = {}
    sql_OMIM = u"select OntoID, OntoTerm, OntoTermJa, InheritanceTypeOf from OMIM group by OntoID"
    cursor_OMIM = OBJ_MYSQL.cursor()
    cursor_OMIM.execute(sql_OMIM)
    values = cursor_OMIM.fetchall()
    cursor_OMIM.close()
    for value in values:
        onto_id_omim      = value[0]
        onto_term_en_omim = value[1]
        onto_term_ja_omim = value[2] if value[2] else onto_term_en_omim
        inheritance_omim  = value[3]

        if onto_id_omim in dict_omim_orphanet:
            dict_omim_orphanet[onto_id_omim]['term_en']     = onto_term_en_omim
            dict_omim_orphanet[onto_id_omim]['term_ja']     = onto_term_ja_omim
            dict_omim_orphanet[onto_id_omim]['inheritance'] = inheritance_omim
        else:
            dict_omim_orphanet[onto_id_omim] = {}
            dict_omim_orphanet[onto_id_omim]['term_en']     = onto_term_en_omim
            dict_omim_orphanet[onto_id_omim]['term_ja']     = onto_term_ja_omim
            dict_omim_orphanet[onto_id_omim]['inheritance'] = inheritance_omim


    ####
    # Orphanetテーブルから疾患情報を取得
    sql_Orphanet = u"select OntoID, OntoTerm, OntoTermJa, InheritanceTypeOf from Orphanet group by OntoID"
    cursor_Orphanet = OBJ_MYSQL.cursor()
    cursor_Orphanet.execute(sql_Orphanet)
    values = cursor_Orphanet.fetchall()
    cursor_Orphanet.close()
    for value in values:
        onto_id_orphanet      = value[0]
        onto_term_en_orphanet = value[1]
        onto_term_ja_orphanet = value[2] if value[2] else onto_term_en_orphanet
        inheritance_orphanet  = value[3]

        if onto_id_orphanet in dict_omim_orphanet:
            dict_omim_orphanet[onto_id_orphanet]['term_en']     = onto_term_en_orphanet
            dict_omim_orphanet[onto_id_orphanet]['term_ja']     = onto_term_ja_orphanet
            dict_omim_orphanet[onto_id_orphanet]['inheritance'] = inheritance_orphanet
        else:
            dict_omim_orphanet[onto_id_orphanet] = {}
            dict_omim_orphanet[onto_id_orphanet]['term_en']     = onto_term_en_orphanet
            dict_omim_orphanet[onto_id_orphanet]['term_ja']     = onto_term_ja_orphanet
            dict_omim_orphanet[onto_id_orphanet]['inheritance'] = inheritance_orphanet


    ####
    ## GeneFromHPOテーブルから情報取得
    ## mysql> desc GeneFromHPO;
    ## +--------------------+------------------+------+-----+---------+----------------+
    ## | Field              | Type             | Null | Key | Default | Extra          |
    ## +--------------------+------------------+------+-----+---------+----------------+
    ## | id                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    ## | EntrezID           | varchar(300)     | NO   | MUL | NULL    |                |
    ## | Symbol             | varchar(300)     | YES  | MUL | NULL    |                |
    ## | Source             | varchar(30)      | NO   | MUL | NULL    |                |
    ## | DiseaseID          | varchar(300)     | YES  | MUL | NULL    |                |
    ## | AnnotationHPONum   | int(10) unsigned | NO   |     | 0       |                |
    ## | AnnotationHPOSumIC | float unsigned   | NO   |     | 0       |                |
    ## +--------------------+------------------+------+-----+---------+----------------+
    dict_symbol             = {}
    dict_AnnotationHPONum   = {}
    dict_AnnotationHPOSumIC = {}
    dict_gene_disease = {}
    sql_GeneFromHPO = u"select distinct EntrezID, Symbol, Source, DiseaseID, AnnotationHPONum, AnnotationHPOSumIC from GeneFromHPO"
    cursor_GeneFromHPO = OBJ_MYSQL.cursor()
    cursor_GeneFromHPO.execute(sql_GeneFromHPO)
    values = cursor_GeneFromHPO.fetchall()
    cursor_GeneFromHPO.close()
    for value in values:
        gene_id            = value[0]
        symbol             = value[1]
        source             = value[2]
        disease_id         = value[3]
        AnnotationHPONum   = value[4]
        AnnotationHPOSumIC = value[5]
        dict_symbol[gene_id]             = symbol
        dict_AnnotationHPONum[gene_id]   = AnnotationHPONum
        dict_AnnotationHPOSumIC[gene_id] = AnnotationHPOSumIC

        # 各遺伝子に紐づけられた疾患を収納
        if gene_id in dict_gene_disease:
            dict_id_en_ja_inheritance = {}
            dict_id_en_ja_inheritance['disease_id']  = disease_id
            dict_id_en_ja_inheritance['term_en']     = dict_omim_orphanet[disease_id]['term_en'] if disease_id in dict_omim_orphanet else ""
            dict_id_en_ja_inheritance['term_ja']     = dict_omim_orphanet[disease_id]['term_ja'] if disease_id in dict_omim_orphanet else ""
            dict_id_en_ja_inheritance['inheritance'] = dict_omim_orphanet[disease_id]['inheritance'] if disease_id in dict_omim_orphanet else ""
            (dict_gene_disease[gene_id]['disease_id_en_ja_inheritance']).append(dict_id_en_ja_inheritance)
        else:
            dict_gene_disease[gene_id] = {}
            dict_id_en_ja_inheritance = {}
            dict_id_en_ja_inheritance['disease_id']  = disease_id if disease_id in dict_omim_orphanet else ""
            dict_id_en_ja_inheritance['term_en']     = dict_omim_orphanet[disease_id]['term_en'] if disease_id in dict_omim_orphanet else ""
            dict_id_en_ja_inheritance['term_ja']     = dict_omim_orphanet[disease_id]['term_ja'] if disease_id in dict_omim_orphanet else ""
            dict_id_en_ja_inheritance['inheritance'] = dict_omim_orphanet[disease_id]['inheritance'] if disease_id in dict_omim_orphanet else ""
            dict_gene_disease[gene_id]['disease_id_en_ja_inheritance'] = []
            (dict_gene_disease[gene_id]['disease_id_en_ja_inheritance']).append(dict_id_en_ja_inheritance)


    ####
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


    ####
    ## ICテーブルから全HPO termのICを取得
    dict_IC = {}
    sql_IC = u"select OntoID, IC from IC where OntoName='HP'"
    cursor_IC = OBJ_MYSQL.cursor()
    cursor_IC.execute(sql_IC)
    values = cursor_IC.fetchall()
    cursor_IC.close()
    for value in values:
        gene_id = value[0]
        ic      = value[1]
        dict_IC[gene_id] = ic

        
    ####
    ## 各疾患とのスコアを算出し、データを収納
    ### インデックステーブルを利用して、各疾患でのICの合計を取得
    ### http://stackoverflow.com/questions/4574609/executing-select-where-in-using-mysqldb
    ### mysql> desc IndexGenePhenotypeFromHPO;
    ### +--------------------+------------------+------+-----+---------+----------------+
    ### | Field              | Type             | Null | Key | Default | Extra          |
    ### +--------------------+------------------+------+-----+---------+----------------+
    ### | id                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    ### | EntrezID           | varchar(300)     | NO   | MUL | NULL    |                |
    ### | GeneOntoIDHP       | varchar(300)     | NO   | MUL | NULL    |                |
    ### | GeneOntoIDHPSource | varchar(30)      | NO   | MUL | NULL    |                |
    ### | IndexOntoIDHP      | varchar(300)     | NO   | MUL | NULL    |                |
    ### | CommonRootHP       | varchar(300)     | NO   | MUL | NULL    |                |
    ### | CommonRootHPIC     | varchar(300)     | NO   |     | NULL    |                |
    ### +--------------------+------------------+------+-----+---------+----------------+
    sql = u"select a.EntrezID, a.IndexOntoIDHP, a.GeneOntoIDHP, a.GeneOntoIDHPSource, a.CommonRootHP, a.CommonRootHPIC, (b.IC - a.CommonRootHPIC) from IndexGenePhenotypeFromHPO as a left join IC as b on a.IndexOntoIDHP=b.OntoID where a.IndexOntoIDHP in (%s) and b.OntoName='HP' order by a.EntrezID, (b.IC - a.CommonRootHPIC)"
    in_p=', '.join(map(lambda x: '%s', list_phenotypes))
    sql = sql % in_p
    cursor = OBJ_MYSQL.cursor()
    cursor.execute(sql, list_phenotypes)
    values = cursor.fetchall()
    cursor.close()


    ####
    ## データを収納
    list_dict_similar_gene = []
    dict_similar_genes = {}
    dict_over_thres_count = {}
    # t10
    thres_delta_ic, thres_count, thres_weight = 7.5, 3, 0.25

    for value in values:
        gene_id                = value[0]
        onto_id_hp_index       = value[1]
        onto_id_hp_gene        = value[2]
        onto_id_hp_gene_source = value[3]
        onto_id_hp_common_root = value[4]
        ic                     = 0 if value[5] == "" else float(value[5])
        delta_ic               = float(value[6])
        weight                 = 1

        # 入力HPOとCommonHPOの差分カウントおよびカウント回数の条件を満たした場合のweight設定
        if gene_id not in dict_over_thres_count:
            dict_over_thres_count[gene_id] = 0
        if delta_ic < thres_delta_ic:
            dict_over_thres_count[gene_id] += 1
        if delta_ic >= thres_delta_ic and dict_over_thres_count[gene_id] >= thres_count:
            weight = thres_weight

        if gene_id in dict_similar_genes:
            onto_term_hp_gene = dict_OntoTerm_hp[onto_id_hp_gene] if onto_id_hp_gene in dict_OntoTerm_hp else ""
            dict_id_term_hp_gene = {}
            dict_id_term_hp_gene['onto_id_hp_gene'] = onto_id_hp_gene
            dict_id_term_hp_gene['onto_term_hp_gene'] = onto_term_hp_gene
            (dict_similar_genes[gene_id]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_genes[gene_id]['onto_id_hp_gene']).append(onto_id_hp_gene)
            (dict_similar_genes[gene_id]['onto_id_term_hp_gene']).append(dict_id_term_hp_gene)
            (dict_similar_genes[gene_id]['onto_id_hp_gene_source']).append(onto_id_hp_gene_source)
            (dict_similar_genes[gene_id]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_genes[gene_id]['onto_term_hp_gene']).append(onto_term_hp_gene)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_genes[gene_id]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_genes[gene_id]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_genes[gene_id]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_genes[gene_id]['sum_ic_denominator'] += 0
        else:
            dict_similar_genes[gene_id] = {}
            dict_similar_genes[gene_id]['onto_id_hp_index']       = []
            dict_similar_genes[gene_id]['onto_id_hp_gene']        = []
            dict_similar_genes[gene_id]['onto_id_term_hp_gene']   = []
            dict_similar_genes[gene_id]['onto_id_hp_gene_source'] = []
            dict_similar_genes[gene_id]['onto_id_hp_common_root'] = []
            dict_similar_genes[gene_id]['onto_term_hp_gene']      = []
            dict_similar_genes[gene_id]['sum_ic']                 = 0
            dict_similar_genes[gene_id]['sum_ic_denominator']     = 0

            onto_term_hp_gene = dict_OntoTerm_hp[onto_id_hp_gene] if onto_id_hp_gene in dict_OntoTerm_hp else ""
            dict_id_term_hp_gene = {}
            dict_id_term_hp_gene['onto_id_hp_gene'] = onto_id_hp_gene
            dict_id_term_hp_gene['onto_term_hp_gene'] = onto_term_hp_gene
            (dict_similar_genes[gene_id]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_genes[gene_id]['onto_id_hp_gene']).append(onto_id_hp_gene)
            (dict_similar_genes[gene_id]['onto_id_term_hp_gene']).append(dict_id_term_hp_gene)
            (dict_similar_genes[gene_id]['onto_id_hp_gene_source']).append(onto_id_hp_gene_source)
            (dict_similar_genes[gene_id]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_genes[gene_id]['onto_term_hp_gene']).append(onto_term_hp_gene)

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if onto_id_hp_index in dict_IC and dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_genes[gene_id]['sum_ic'] += ic * weight
                # GeneYenta: 分母
                dict_similar_genes[gene_id]['sum_ic_denominator'] += dict_IC[onto_id_hp_index] * weight
            else:
                # GeneYenta: 分子
                dict_similar_genes[gene_id]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_genes[gene_id]['sum_ic_denominator'] += 0


    # ユーザが指定した遺伝子を収納
    dict_filter_gene_gene = {}
    if str_genes != "":
        sql_GenePhenotypeFromHPO = u"select EntrezID, Symbol, SymbolSynonym from GenePhenotypeFromHPO where EntrezID in (%s)"
        in_p=', '.join(map(lambda x: '%s', list_genes))
        sql_GenePhenotypeFromHPO = sql_GenePhenotypeFromHPO % in_p
        cursor_GenePhenotypeFromHPO = OBJ_MYSQL.cursor()
        cursor_GenePhenotypeFromHPO.execute(sql_GenePhenotypeFromHPO, list_genes)
        values = cursor_GenePhenotypeFromHPO.fetchall()
        cursor_GenePhenotypeFromHPO.close()
        for value in values:
            entrez_id      = value[0]
            symbol         = value[1]
            symbol_synonym = value[2]

            if gene_id in dict_filter_gene_gene:
                dict_gene_symbol_synonym = {}
                dict_gene_symbol_synonym['entrez_id']      = entrez_id
                dict_gene_symbol_synonym['symbol']         = symbol
                dict_gene_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_gene_gene[entrez_id]['gene_symbol_synonym']).append(dict_gene_symbol_synonym)
            else:
                dict_filter_gene_gene[entrez_id] = {}
                dict_filter_gene_gene[entrez_id]['gene_symbol_synonym'] = []
                dict_gene_symbol_synonym = {}
                dict_gene_symbol_synonym['entrez_id']      = entrez_id
                dict_gene_symbol_synonym['symbol']         = symbol
                dict_gene_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_gene_gene[entrez_id]['gene_symbol_synonym']).append(dict_gene_symbol_synonym)

    OBJ_MYSQL.close()


    ####
    # 類似疾患検索結果を収納
    for gene_id in dict_similar_genes.keys():

        # IndexCaseHPの中に、オントロジーには含まれないCase IDが含まれているため、それらの処理を飛ばす
        if gene_id not in dict_AnnotationHPONum:
            continue

        # ユーザが入力したgenesでフィルタリング
        if str_genes != "" and not gene_id in dict_filter_gene_gene:
            continue

        dict_similar_gene                           = {}
        dict_similar_gene['gene_id']                = gene_id
        ## 関連Phenotypes
        dict_similar_gene['sum_ic']                 = dict_similar_genes[gene_id]['sum_ic']
        dict_similar_gene['sum_ic_denominator']     = dict_similar_genes[gene_id]['sum_ic_denominator']
        ## 類似度スコア計算
        if dict_similar_genes[gene_id]['sum_ic_denominator'] != 0:
            dict_similar_gene['match_score'] = float(dict_similar_genes[gene_id]['sum_ic'] / dict_similar_genes[gene_id]['sum_ic_denominator'])
        else:
            dict_similar_gene['match_score'] = 0
        ## 遺伝子情報
        dict_similar_gene['symbol']                 = dict_symbol[gene_id]
        dict_similar_gene['onto_id_hp_index']       = ",".join(dict_similar_genes[gene_id]['onto_id_hp_index'])
        dict_similar_gene['onto_id_hp_gene']        = ",".join(dict_similar_genes[gene_id]['onto_id_hp_gene'])
        dict_similar_gene['onto_id_term_hp_gene']   = sorted(dict_similar_genes[gene_id]['onto_id_term_hp_gene'], key=lambda x: x['onto_term_hp_gene'])
        dict_similar_gene['onto_id_hp_gene_source'] = ",".join(dict_similar_genes[gene_id]['onto_id_hp_gene_source'])
        dict_similar_gene['onto_id_hp_common_root'] = ",".join(dict_similar_genes[gene_id]['onto_id_hp_common_root'])
        dict_similar_gene['onto_term_hp_gene']      = ",".join(dict_similar_genes[gene_id]['onto_term_hp_gene'])
        ## 疾患情報
        #dict_similar_gene['gene_symbol_synonym']    = sorted(dict_gene_disease[gene_id]['gene_symbol_synonym'], key=lambda x: x['symbol']) if gene_id in dict_gene_disease else []
        dict_similar_gene['disease_id_en_ja_inheritance']    = dict_gene_disease[gene_id]['disease_id_en_ja_inheritance'] if gene_id in dict_gene_disease else []
        ## HPOアノテーション数とHPOアノテーション合計IC
        dict_similar_gene['annotation_hp_num']      = dict_AnnotationHPONum[gene_id]
        dict_similar_gene['annotation_hp_sum_ic']   = dict_AnnotationHPOSumIC[gene_id]

        list_dict_similar_gene.append(dict_similar_gene)

        
    ####
    # スコアを基にランキングを作成
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    ## スコアが同一の場合は、以下の値でランキング
    ### アノテーションされたHPOの数
    ### アノテーションされたHPOのICの合計値
    list_dict_similar_gene_sorted = []
    rank = 0
    rank_deposit = 0
    prev_match_score = 0
    for dict_similar_gene in sorted(list_dict_similar_gene, key=lambda x: (-float(x['match_score']),int(x['annotation_hp_num']),-float(x['annotation_hp_sum_ic']))):
        if dict_similar_gene['match_score'] != prev_match_score:
            rank = rank + 1 + rank_deposit 
            dict_similar_gene['rank'] = rank
            prev_match_score = dict_similar_gene['match_score']
            rank_deposit = 0
        else:
            dict_similar_gene['rank'] = rank
            prev_match_score = dict_similar_gene['match_score']
            rank_deposit += 1

        list_dict_similar_gene_sorted.append(dict_similar_gene)

    return list_dict_similar_gene_sorted

