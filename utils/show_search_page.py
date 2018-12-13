# -*- coding: utf-8 -*-

import os
import re
import MySQLdb

from flask import Flask, render_template, request, redirect, url_for, jsonify
from utils.pagination import Pagination
from flask_babel import gettext,Babel


app = Flask(__name__)

# https://github.com/shibacow/flask_babel_sample/blob/master/srv.py
babel = Babel(app)
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en'])


#####
# DB設定
app.config.from_pyfile('../config.cfg')
db_sock = app.config['DBSOCK']
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


####
# 類似疾患検索画面を表示
def show_search_page(phenotypes, genes, page, size):

    limit = int(size)

    # 正しくないHPO IDやGene IDをクエリからのぞいたクエリを収納
    list_query_phenotype_remove_error = []
    list_query_gene_remove_error = []
        
    # クエリ表示用に取得したphenotypesをJSON形式に変換
    list_dict_phenotype = []
    list_dict_gene = []

    # クエリの全てのHPO IDがデータベースに含まれるか確認し、データを収納
    if phenotypes != "":
        for phenotype in phenotypes.split(","):
            OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
            #sql_OntoTerm = u"select OntoIDTerm from OntoTermHP where OntoType='label' and OntoID=%s"
            sql_OntoTerm = u"select uid_value from IndexFormHP where uid=%s"
            cursor_OntoTerm = OBJ_MYSQL.cursor()
            cursor_OntoTerm.execute(sql_OntoTerm, (phenotype,))
            values = cursor_OntoTerm.fetchall()
            cursor_OntoTerm.close()
            onto_id_term = values[0][0] if values else ''
            OBJ_MYSQL.close()

            if onto_id_term != "":
                dict_phenotype = {}
                dict_phenotype['id'] = phenotype
                dict_phenotype['name'] = onto_id_term
                list_dict_phenotype.append(dict_phenotype)
                list_query_phenotype_remove_error.append(phenotype)

    # クエリの全てのGene IDがデータベースに含まれるか確認し、データを収納
    if genes != "":
        for gene in genes.split(","):

            # Gene Symbolの場合はEntrez Gene IDを抽出
            entrez_id = ""
            pattern_entrez_id = 'HGNC'
            pattern_entrez_id_compiled = re.compile(pattern_entrez_id)
            if pattern_entrez_id_compiled.match(gene):
                OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
                sql_GeneName2ID = u"select EntrezID from GeneName2ID where GeneName=%s"
                cursor_GeneName2ID = OBJ_MYSQL.cursor()
                gene_remove_prefix_HGNC = gene.replace('HGNC:', '')
                cursor_GeneName2ID.execute(sql_GeneName2ID, (gene_remove_prefix_HGNC,))
                values = cursor_GeneName2ID.fetchall()
                cursor_GeneName2ID.close()
                entrez_id = values[0][0] if values else ''
                OBJ_MYSQL.close()
                if entrez_id != "":
                    gene = unicode("ENT:" + str(entrez_id))

            if gene != "":
                OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
                sql_IndexFormSearch = u"select uid_value from IndexFormSearchOrphanetOMIM where uid=%s"
                cursor_IndexFormSearch = OBJ_MYSQL.cursor()
                cursor_IndexFormSearch.execute(sql_IndexFormSearch, (gene,))
                values = cursor_IndexFormSearch.fetchall()
                cursor_IndexFormSearch.close()
                uid_value = values[0][0] if values else ''
                OBJ_MYSQL.close()
                if uid_value != "":
                    dict_gene = {}
                    dict_gene['id'] = gene
                    dict_gene['name'] = uid_value
                    list_dict_gene.append(dict_gene)
                    list_query_gene_remove_error.append(gene)

    #####
    # 類似疾患検索
    ## 日本語HP IDに対応（HP:xxxxx_ja）
    phenotypes_remove_error = ','.join(list_query_phenotype_remove_error)
    genes_remove_error = ','.join(list_query_gene_remove_error)
    list_phenotypes_remove_ja = []
    for phenotype in phenotypes_remove_error.split(","):
        list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
    phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)
    ## 検索
    list_dict_similar_disease = search_similar_disease(phenotypes_remove_ja, genes_remove_error)

    # total件数を取得
    total_hit = len(list_dict_similar_disease)
    pagination = Pagination(int(page), limit, total_hit)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_similar_disease_pagination = list_dict_similar_disease[start:end]

    # 各疾患で報告されている症例報告数を収納
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    for dict_similar_disease in list_dict_similar_disease_pagination:
        onto_id_ordo = dict_similar_disease['onto_id_ordo']
        sql = u"select count(distinct PMID) from AnnotOntoORDOHP where OntoIDORDO=%s"
        cursor = OBJ_MYSQL.cursor()
        cursor.execute(sql, (onto_id_ordo,))
        #cursor.execute(sql, ("ORDO:2573",))
        values = cursor.fetchall()
        cursor.close()
        total_num_case_reports = values[0][0]
        dict_similar_disease['total_num_case_reports'] = total_num_case_reports
    OBJ_MYSQL.close()

    return list_dict_phenotype, list_dict_gene, list_dict_similar_disease_pagination, pagination, total_hit


#####
# search similar diseases
def search_similar_disease(str_phenotypes, str_genes):
    list_phenotypes = str_phenotypes.split(",")
    list_genes      = str_genes.split(",")
    dict_genes = {}
    for gene in list_genes:
        dict_genes[gene] = 1

    # MySQL接続　初期設定
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")

    ## OntoTermテーブルからORDOの全termを取得
    dict_OntoTerm_ordo = {}
    sql_OntoTerm_ordo = u"select distinct OntoID, OntoTerm from OntoTermORDO where OntoType='label'"
    cursor_OntoTerm_ordo = OBJ_MYSQL.cursor()
    cursor_OntoTerm_ordo.execute(sql_OntoTerm_ordo)
    values = cursor_OntoTerm_ordo.fetchall()
    cursor_OntoTerm_ordo.close()
    for value in values:
        dict_OntoTerm_ordo[value[0]] = value[1]

    ## OrphanetテーブルからORDOの全termを取得
    ### OntoTermテーブルはORDOから取得しているが、OrphanetテーブルはOrphanetのXMLから取得している
    ## Orphanetテーブルから各疾患ごとのアノテーションHPO数を取得
    ## Orphanetテーブルから各疾患ごとのアノテーションHPOの合計ICを取得
    dict_AnnotationHPONum   = {}
    dict_AnnotationHPOSumIC = {}
    sql_Orphanet = u"select distinct OntoID, OntoTerm, AnnotationHPONum, AnnotationHPOSumIC from Orphanet"
    cursor_Orphanet = OBJ_MYSQL.cursor()
    cursor_Orphanet.execute(sql_Orphanet)
    values = cursor_Orphanet.fetchall()
    cursor_Orphanet.close()
    for value in values:
        dict_OntoTerm_ordo[value[0]]      = value[1]
        dict_AnnotationHPONum[value[0]]   = value[2]
        dict_AnnotationHPOSumIC[value[0]] = value[3]

        
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

    # OrphanetテーブルからDisease definitionを取得
    dict_disease_definition = {}
    sql_Orphanet_disease_definition = u"select OntoID, DiseaseDefinition from Orphanet group by OntoID"
    cursor_Orphanet_disease_definition = OBJ_MYSQL.cursor()
    cursor_Orphanet_disease_definition.execute(sql_Orphanet_disease_definition)
    values = cursor_Orphanet_disease_definition.fetchall()
    cursor_Orphanet_disease_definition.close()
    for value in values:
        if value[1] is not None:
            #disease_definition = str((value[1]).encode('utf-8'))
            disease_definition = (value[1]).encode('utf-8')
            dict_disease_definition[value[0]] = disease_definition
            #if get_locale() != "en" and type(value[1]) is str:
            #if get_locale() != "en":
                #dict_disease_definition[value[0]] = disease_definition + "<a href='https://translate.google.co.jp/?hl=ja#en/ja/" + disease_definition  + "' target='_blank'><font color='#0431B4'>&nbsp;&nbsp;&gt;&gt;&nbsp;Translate (Google)</font></a>"


    ## DiseaseLinkテーブルから各疾患のReferenceを取得
    dict_DiseaseLink = {}
    sql_DiseaseLink = u"select OntoIDORDO, Reference, Link, Source from DiseaseLink order by OntoIDORDO, Source"
    cursor_DiseaseLink = OBJ_MYSQL.cursor()
    cursor_DiseaseLink.execute(sql_DiseaseLink)
    values = cursor_DiseaseLink.fetchall()
    cursor_DiseaseLink.close()
    for value in values:
        onto_id_ordo = value[0]
        reference    = value[1]
        link         = value[2]
        source       = value[3]

        if source != "OMIM" and source != "ICD-10":
            continue

        if onto_id_ordo in dict_DiseaseLink:
            dict_reference_source = {}
            dict_reference_source['reference'] = reference
            dict_reference_source['link'] = link
            dict_reference_source['source'] = source
            (dict_DiseaseLink[onto_id_ordo]).append(dict_reference_source)
        else:
            dict_DiseaseLink[onto_id_ordo] = []
            dict_reference_source = {}
            dict_reference_source['reference'] = reference
            dict_reference_source['link'] = link
            dict_reference_source['source'] = source
            (dict_DiseaseLink[onto_id_ordo]).append(dict_reference_source)


    ## ICテーブルからHPの全termを取得
    dict_IC = {}
    sql_IC = u"select OntoID, IC from IC where OntoName='HP'"
    cursor_IC = OBJ_MYSQL.cursor()
    cursor_IC.execute(sql_IC)
    values = cursor_IC.fetchall()
    cursor_IC.close()
    for value in values:
        onto_id_ordo = value[0]
        ic = value[1]
        dict_IC[onto_id_ordo] = ic

        
    ## 各疾患とのスコアを算出
    ### インデックステーブルを利用して、各疾患でのICの合計を取得
    ### http://stackoverflow.com/questions/4574609/executing-select-where-in-using-mysqldb
    #sql = u"select a.OntoIDORDO, a.IndexOntoIDHP, a.DiseaseOntoIDHP, a.DiseaseOntoIDHPSource, a.CommonRootHP, b.IC from IndexDiseaseHP as a left join IC as b on a.CommonRootHP=b.OntoID where b.OntoName='HP' and a.OntoIDORDO in (select distinct OntoID from Orphanet where RareDiseaseFlg=1) and a.IndexOntoIDHP in (%s) order by a.OntoIDORDO, a.DiseaseOntoIDHP"
    sql = u"select OntoIDORDO, IndexOntoIDHP, DiseaseOntoIDHP, DiseaseOntoIDHPSource, CommonRootHP, CommonRootHPIC from IndexDiseaseHP where OntoIDORDO in (select distinct OntoID from Orphanet where RareDiseaseFlg=1) and IndexOntoIDHP in (%s) order by OntoIDORDO, DiseaseOntoIDHP"
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
    for value in values:
        onto_id_ordo              = value[0]
        onto_id_hp_index          = value[1]
        onto_id_hp_disease        = value[2]
        onto_id_hp_disease_source = value[3]
        onto_id_hp_common_root    = value[4]
        ic                        = float(value[5])
        #orpha_number = onto_id_ordo.replace('ORDO:', '')

        if onto_id_ordo in dict_similar_diseases:
            onto_term_hp_disease = dict_OntoTerm_hp[onto_id_hp_disease] if onto_id_hp_disease in dict_OntoTerm_hp else ""
            dict_id_term_hp_disease = {}
            dict_id_term_hp_disease['onto_id_hp_disease'] = onto_id_hp_disease
            dict_id_term_hp_disease['onto_term_hp_disease'] = onto_term_hp_disease
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease']).append(onto_id_hp_disease)
            (dict_similar_diseases[onto_id_ordo]['onto_id_term_hp_disease']).append(dict_id_term_hp_disease)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease_source']).append(onto_id_hp_disease_source)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_diseases[onto_id_ordo]['onto_term_hp_disease']).append(onto_term_hp_disease)
            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする                                                                                                              
            if dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_ordo]['sum_ic'] += ic
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'] += dict_IC[onto_id_hp_index]
            else:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_ordo]['sum_ic'] += 0
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'] += 0
        else:
            dict_similar_diseases[onto_id_ordo] = {}
            dict_similar_diseases[onto_id_ordo]['onto_id_hp_index']          = []
            dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease']        = []
            dict_similar_diseases[onto_id_ordo]['onto_id_term_hp_disease']   = []
            dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease_source'] = []
            dict_similar_diseases[onto_id_ordo]['onto_id_hp_common_root']    = []
            dict_similar_diseases[onto_id_ordo]['onto_term_hp_disease']      = []
            dict_similar_diseases[onto_id_ordo]['sum_ic']                    = 0
            dict_similar_diseases[onto_id_ordo]['sum_ic_denominator']        = 0

            onto_term_hp_disease = dict_OntoTerm_hp[onto_id_hp_disease] if onto_id_hp_disease in dict_OntoTerm_hp else ""
            dict_id_term_hp_disease = {}
            dict_id_term_hp_disease['onto_id_hp_disease'] = onto_id_hp_disease
            dict_id_term_hp_disease['onto_term_hp_disease'] = onto_term_hp_disease
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_index']).append(onto_id_hp_index)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease']).append(onto_id_hp_disease)
            (dict_similar_diseases[onto_id_ordo]['onto_id_term_hp_disease']).append(dict_id_term_hp_disease)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease_source']).append(onto_id_hp_disease_source)
            (dict_similar_diseases[onto_id_ordo]['onto_id_hp_common_root']).append(onto_id_hp_common_root)
            (dict_similar_diseases[onto_id_ordo]['onto_term_hp_disease']).append(onto_term_hp_disease)
            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする                                                                                                              
            if dict_IC[onto_id_hp_index] != 0:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_ordo]['sum_ic']         += ic
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'] += dict_IC[onto_id_hp_index]
            else:
                # GeneYenta: 分子
                dict_similar_diseases[onto_id_ordo]['sum_ic']         += 0
                # GeneYenta: 分母
                dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'] += 0

            dict_similar_diseases[onto_id_ordo]['onto_term_ordo'] = dict_OntoTerm_ordo[onto_id_ordo] if onto_id_ordo in dict_OntoTerm_ordo else ""
            #dict_similar_diseases[onto_id_ordo]['orpha_number']   = orpha_number
            dict_similar_diseases[onto_id_ordo]['onto_term_ordo_disease_definition'] = dict_disease_definition[onto_id_ordo] if onto_id_ordo in dict_disease_definition else ""

    # DiseaseGeneテーブルから各疾患に関連するGenes/Variantsを取得
    dict_disease_gene = {}
    sql_DiseaseGene = u"select OntoIDORDO, EntrezID, Symbol, SymbolSynonym from DiseaseGene"
    cursor_DiseaseGene = OBJ_MYSQL.cursor()
    cursor_DiseaseGene.execute(sql_DiseaseGene)
    values = cursor_DiseaseGene.fetchall()
    cursor_DiseaseGene.close()
    for value in values:
        onto_id_ordo   = value[0]
        entrez_id      = value[1]
        symbol         = value[2]
        symbol_synonym = value[3]

        if onto_id_ordo in dict_disease_gene:
            dict_orpha_number_symbol_synonym = {}
            dict_orpha_number_symbol_synonym['entrez_id'] = entrez_id
            dict_orpha_number_symbol_synonym['symbol'] = symbol
            dict_orpha_number_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym']).append(dict_orpha_number_symbol_synonym)
        else:
            dict_disease_gene[onto_id_ordo] = {}
            dict_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym'] = []
            dict_orpha_number_symbol_synonym = {}
            dict_orpha_number_symbol_synonym['entrez_id'] = entrez_id
            dict_orpha_number_symbol_synonym['symbol'] = symbol
            dict_orpha_number_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym']).append(dict_orpha_number_symbol_synonym)

    # ユーザが指定した遺伝子を疾患原因遺伝子に持つ疾患をDiseaseGeneテーブルから取得
    dict_filter_disease_gene = {}
    if str_genes != "":
        #sql_DiseaseGene = u"select OntoIDORDO, OrphaNumber, Symbol, SymbolSynonym from DiseaseGene where OrphaNumber in (%s)"
        sql_DiseaseGene = u"select OntoIDORDO, EntrezID, Symbol, SymbolSynonym from DiseaseGene where EntrezID in (%s)"
        in_p=', '.join(map(lambda x: '%s', list_genes))
        sql_DiseaseGene = sql_DiseaseGene % in_p
        cursor_DiseaseGene = OBJ_MYSQL.cursor()
        cursor_DiseaseGene.execute(sql_DiseaseGene, list_genes)
        values = cursor_DiseaseGene.fetchall()
        cursor_DiseaseGene.close()
        for value in values:
            onto_id_ordo   = value[0]
            entrez_id      = value[1]
            symbol         = value[2]
            symbol_synonym = value[3]

            if onto_id_ordo in dict_filter_disease_gene:
                dict_orpha_number_symbol_synonym = {}
                dict_orpha_number_symbol_synonym['entrez_id'] = entrez_id
                dict_orpha_number_symbol_synonym['symbol'] = symbol
                dict_orpha_number_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym']).append(dict_orpha_number_symbol_synonym)
            else:
                dict_filter_disease_gene[onto_id_ordo] = {}
                dict_filter_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym'] = []
                dict_orpha_number_symbol_synonym = {}
                dict_orpha_number_symbol_synonym['entrez_id'] = entrez_id
                dict_orpha_number_symbol_synonym['symbol'] = symbol
                dict_orpha_number_symbol_synonym['symbol_synonym'] = symbol_synonym
                (dict_filter_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym']).append(dict_orpha_number_symbol_synonym)

    OBJ_MYSQL.close()

    ####
    # 類似疾患検索結果を収納
    for onto_id_ordo in dict_similar_diseases.keys():

        # ユーザが入力したgenesでフィルタリング
        #if str_genes != "" and not dict_disease_gene.has_key(onto_id_ordo):
        if str_genes != "" and not onto_id_ordo in dict_filter_disease_gene:
            continue

        dict_similar_disease = {}
        dict_similar_disease['onto_id_ordo']              = onto_id_ordo
        ## 関連Phenotypes
        dict_similar_disease['sum_ic']                    = dict_similar_diseases[onto_id_ordo]['sum_ic']
        dict_similar_disease['sum_ic_denominator']        = dict_similar_diseases[onto_id_ordo]['sum_ic_denominator']
        if dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'] != 0:
            dict_similar_disease['match_score']           = float(dict_similar_diseases[onto_id_ordo]['sum_ic'] / dict_similar_diseases[onto_id_ordo]['sum_ic_denominator'])
        else:
            dict_similar_disease['match_score']           = 0
        dict_similar_disease['onto_term_ordo']            = dict_similar_diseases[onto_id_ordo]['onto_term_ordo']
        #dict_similar_disease['orpha_number']              = dict_similar_diseases[onto_id_ordo]['orpha_number']
        dict_similar_disease['onto_term_ordo_disease_definition'] = dict_similar_diseases[onto_id_ordo]['onto_term_ordo_disease_definition']
        dict_similar_disease['onto_id_hp_index']          = ",".join(dict_similar_diseases[onto_id_ordo]['onto_id_hp_index'])
        dict_similar_disease['onto_id_hp_disease']        = ",".join(dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease'])
        dict_similar_disease['onto_id_term_hp_disease']   = sorted(dict_similar_diseases[onto_id_ordo]['onto_id_term_hp_disease'], key=lambda x: x['onto_term_hp_disease'])
        dict_similar_disease['onto_id_hp_disease_source'] = ",".join(dict_similar_diseases[onto_id_ordo]['onto_id_hp_disease_source'])
        dict_similar_disease['onto_id_hp_common_root']    = ",".join(dict_similar_diseases[onto_id_ordo]['onto_id_hp_common_root'])
        dict_similar_disease['onto_term_hp_disease']      = ",".join(dict_similar_diseases[onto_id_ordo]['onto_term_hp_disease'])
        ## 関連Genes/Variants
        dict_similar_disease['orpha_number_symbol_synonym'] = sorted(dict_disease_gene[onto_id_ordo]['orpha_number_symbol_synonym'], key=lambda x: x['symbol']) if onto_id_ordo in dict_disease_gene else []
        ## 外部リファレンス
        if onto_id_ordo in dict_DiseaseLink:
            dict_similar_disease['reference_source'] = sorted(dict_DiseaseLink[onto_id_ordo], key=lambda x: x['source'])
        ## HPOアノテーション数とHPOアノテーション合計IC
        dict_similar_disease['annotation_hp_num']        = dict_AnnotationHPONum[onto_id_ordo]
        dict_similar_disease['annotation_hp_sum_ic']     = dict_AnnotationHPOSumIC[onto_id_ordo]

        list_dict_similar_disease.append(dict_similar_disease)

    ####
    # sort
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    list_dict_similar_disease_sorted = []
    rank = 0
    rank_deposit = 0
    #prev_sum_ic = 0
    #for dict_similar_disease in sorted(list_dict_similar_disease, key=lambda x: (-float(x['sum_ic']),x['onto_term_ordo'])):
    #    if dict_similar_disease['sum_ic'] != prev_sum_ic:
    #        rank = rank + 1 + rank_deposit 
    #        dict_similar_disease['rank'] = rank
    #        prev_sum_ic = dict_similar_disease['sum_ic']
    #        rank_deposit = 0
    #    else:
    #        dict_similar_disease['rank'] = rank
    #        prev_sum_ic = dict_similar_disease['sum_ic']
    #        rank_deposit += 1

    ####
    # スコアを基にランキングを作成
    ## スコアが同一の場合は、以下の値でランキング
    ### アノテーションされたHPOの数
    ### アノテーションされたHPOのICの合計値
    prev_match_score = 0
    #for dict_similar_disease in sorted(list_dict_similar_disease, key=lambda x: (-float(x['match_score']),x['onto_term_ordo'])):
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

    return list_dict_similar_disease_sorted

