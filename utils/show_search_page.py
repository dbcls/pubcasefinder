# -*- coding: utf-8 -*-

import os
import re
import MySQLdb

from flask import Flask, render_template, request, redirect, url_for, jsonify
from utils.pagination import Pagination

app = Flask(__name__)

#####
# DB設定
app.config.from_pyfile('../config.cfg')
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


####
# 類似疾患検索画面を表示
def show_search_page(phenotypes, genes, page, size):

    limit = int(size)

    # 類似疾患検索
    list_dict_similar_disease = search_similar_disease(phenotypes, genes)
        
    # クエリ表示用に取得したphenotypesをJSON形式に変換
    list_dict_phenotype = []
    list_dict_gene = []

    if phenotypes != "":
        for phenotype in phenotypes.split(","):
            OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
            sql_OntoTerm = u"select OntoIDTerm from OntoTermHP where OntoType='label' and OntoID=%s"
            cursor_OntoTerm = OBJ_MYSQL.cursor()
            cursor_OntoTerm.execute(sql_OntoTerm, (phenotype,))
            values = cursor_OntoTerm.fetchall()
            cursor_OntoTerm.close()
            onto_id_term = values[0][0] if values else ''
            OBJ_MYSQL.close()

            dict_phenotype = {}
            dict_phenotype['id'] = phenotype
            dict_phenotype['name'] = onto_id_term
            list_dict_phenotype.append(dict_phenotype)

    if genes != "":
        for gene in genes.split(","):
            OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
            sql_IndexFormSearch = u"select uid_value from IndexFormSearch where uid=%s"
            cursor_IndexFormSearch = OBJ_MYSQL.cursor()
            cursor_IndexFormSearch.execute(sql_IndexFormSearch, (gene,))
            values = cursor_IndexFormSearch.fetchall()
            cursor_IndexFormSearch.close()
            uid_value = values[0][0] if values else ''
            OBJ_MYSQL.close()

            dict_gene = {}
            dict_gene['id'] = gene
            dict_gene['name'] = uid_value
            list_dict_gene.append(dict_gene)

    # total件数を取得
    total_hit = len(list_dict_similar_disease)
    pagination = Pagination(int(page), limit, total_hit)

    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_similar_disease_pagination = list_dict_similar_disease[start:end]

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
    OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")

    ## OntoTermテーブル及びOrphanetテーブルからORDOの全termを取得
    dict_OntoTerm_ordo = {}
    sql_OntoTerm_ordo = u"select distinct OntoID, OntoTerm from OntoTermORDO where OntoType='label'"
    cursor_OntoTerm_ordo = OBJ_MYSQL.cursor()
    cursor_OntoTerm_ordo.execute(sql_OntoTerm_ordo)
    values = cursor_OntoTerm_ordo.fetchall()
    cursor_OntoTerm_ordo.close()
    for value in values:
        dict_OntoTerm_ordo[value[0]] = value[1]
    sql_Orphanet = u"select distinct OntoID, OntoTerm from Orphanet"
    cursor_Orphanet = OBJ_MYSQL.cursor()
    cursor_Orphanet.execute(sql_Orphanet)
    values = cursor_Orphanet.fetchall()
    cursor_Orphanet.close()
    for value in values:
        dict_OntoTerm_ordo[value[0]] = value[1]

    ## OntoTermHPテーブルからHPの全termを取得
    dict_OntoTerm_hp = {}
    sql_OntoTerm_hp = u"select distinct OntoID, OntoTerm from OntoTermHP where OntoType='label'"
    cursor_OntoTerm_hp = OBJ_MYSQL.cursor()
    cursor_OntoTerm_hp.execute(sql_OntoTerm_hp)
    values = cursor_OntoTerm_hp.fetchall()
    cursor_OntoTerm_hp.close()
    for value in values:
        dict_OntoTerm_hp[value[0]] = value[1]

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

        
    ## 各疾患でのICの合計を取得
    ## http://stackoverflow.com/questions/4574609/executing-select-where-in-using-mysqldb
    #sql = u"select a.OntoIDORDO, a.IndexOntoIDHP, a.DiseaseOntoIDHP, a.DiseaseOntoIDHPSource, a.CommonRootHP, b.IC from IndexDiseaseHP as a left join IC as b on a.CommonRootHP=b.OntoID where b.OntoName='HP' and a.OntoIDORDO in (select distinct OntoID from Orphanet where RareDiseaseFlg=1) and a.IndexOntoIDHP in (%s) order by a.OntoIDORDO, a.DiseaseOntoIDHP"
    sql = u"select OntoIDORDO, IndexOntoIDHP, DiseaseOntoIDHP, DiseaseOntoIDHPSource, CommonRootHP, CommonRootHPIC from IndexDiseaseHP where OntoIDORDO in (select distinct OntoID from Orphanet where RareDiseaseFlg=1) and IndexOntoIDHP in (%s) order by OntoIDORDO, DiseaseOntoIDHP"
    in_p=', '.join(map(lambda x: '%s', list_phenotypes))
    sql = sql % in_p
    cursor = OBJ_MYSQL.cursor()
    cursor.execute(sql, list_phenotypes)
    values = cursor.fetchall()
    cursor.close()

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

    prev_match_score = 0
    for dict_similar_disease in sorted(list_dict_similar_disease, key=lambda x: (-float(x['match_score']),x['onto_term_ordo'])):
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

