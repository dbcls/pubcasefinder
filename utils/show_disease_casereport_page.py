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
# show_disease_casereport_page()
# 類似症例報告検索画面を表示
#####
def show_disease_casereport_page(disease, phenotypes, genes, page, size):
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    limit = int(size)

    # 日本語HP IDに対応（HP:xxxxx_ja）
    list_phenotypes_remove_ja = []
    for phenotype in phenotypes.split(","):
        list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
    phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)


    #####
    # 類似症例報告検索
    #list_dict_similar_casereport = search_similar_casereport(disease, phenotypes, genes)
    list_dict_similar_casereport = search_similar_casereport(disease, phenotypes_remove_ja, genes)
        

    #####
    # クエリ表示用に取得したphenotypesをJSON形式に変換
    list_dict_phenotype = []
    list_dict_gene = []

    if phenotypes != "":
        for phenotype in phenotypes.split(","):
            #sql_OntoTerm = u"select OntoIDTerm from OntoTermHP where OntoType='label' and OntoID=%s"
            #sql_OntoTerm = u"select uid_value from IndexFormHP where uid=%s"
            sql_OntoTerm = u"select value from IndexFormHP where uid=%s"
            cursor_OntoTerm = OBJ_MYSQL.cursor()
            cursor_OntoTerm.execute(sql_OntoTerm, (phenotype,))
            values = cursor_OntoTerm.fetchall()
            cursor_OntoTerm.close()
            #onto_id_term = values[0][0]
            onto_id_term = values[0][0] if values else ''

            dict_phenotype = {}
            dict_phenotype['id'] = phenotype
            dict_phenotype['name'] = onto_id_term
            list_dict_phenotype.append(dict_phenotype)

    if genes != "":
        for gene in genes.split(","):
            sql = u"select uid_value from IndexFormDiseaseCaseReport where uid=%s"
            cursor = OBJ_MYSQL.cursor()
            cursor.execute(sql, (gene,))
            values = cursor.fetchall()
            cursor.close()
            uid_value = values[0][0]

            dict_gene = {}
            dict_gene['id'] = gene
            dict_gene['name'] = uid_value
            list_dict_gene.append(dict_gene)

    #####
    # OntoTermテーブルからORDOの全termを取得
    dict_OntoTerm_ordo = {}
    sql_OntoTerm_ordo = u"select distinct OntoID, OntoTerm from OntoTermORDO where OntoType='label'"
    cursor_OntoTerm_ordo = OBJ_MYSQL.cursor()
    cursor_OntoTerm_ordo.execute(sql_OntoTerm_ordo)
    values = cursor_OntoTerm_ordo.fetchall()
    cursor_OntoTerm_ordo.close()
    for value in values:
        dict_OntoTerm_ordo[value[0]] = value[1]

    ## 疾患名のOrpha Number（ORDO IDからプレフィックスのORDO:を除去したNumber）と用語を収納
    dict_onto_id_term_ordo = {}
    id_nonprefix_ordo = disease.replace('ORDO:', '')
    dict_onto_id_term_ordo['onto_id_nonprefix_ordo']  = id_nonprefix_ordo
    dict_onto_id_term_ordo['onto_term_ordo']  = dict_OntoTerm_ordo[disease]


    #####
    # OrphanetテーブルからDisease definitionを取得
    disease_definition = ""
    sql_Orphanet = u"select DiseaseDefinition from Orphanet where OntoID=%s group by OntoID"
    cursor_Orphanet = OBJ_MYSQL.cursor()
    cursor_Orphanet.execute(sql_Orphanet, (disease,))
    values = cursor_Orphanet.fetchall()
    cursor_Orphanet.close()
    disease_definition = values[0][0] if values else ''


    #####
    # Diseaseテーブルから対象疾患の全てのフェノタイプを取得（Orphanetから取得したフェノタイプのみ）
    ## HPOFrequencyのOrphaNumberとNameの対応
    ## 453310 : Obligate (100%)
    ## 453311 : Very frequent (99-80%)
    ## 453312 : Frequent (79-30%)
    ## 453313 : Occasional (29-5%)
    ## 453314 : Very rare (&lt;4-1%)
    ## 453315 : Excluded (0%)
    list_dict_Disease_phenotype_Orphanet = []
    #sql_Disease_phenotype_Orphanet = u"select a.OntoIDHP, b.OntoTerm, a.Frequency from Disease as a left join OntoTermHP as b on a.OntoIDHP=b.OntoID where b.OntoType='label' and a.Source='Orphanet' and a.OntoIDORDO=%s order by cast(a.Frequency as SIGNED), a.OntoIDHP"
    sql_Disease_phenotype_Orphanet = u"select a.OntoIDHP, b.OntoName, a.Frequency, b.OntoNameJa from Disease as a left join OntoTermHPInformation as b on a.OntoIDHP=b.OntoID where a.Source='Orphanet' and a.OntoIDORDO=%s order by cast(a.Frequency as SIGNED), a.OntoIDHP"
    cursor_Disease_phenotype_Orphanet = OBJ_MYSQL.cursor()
    cursor_Disease_phenotype_Orphanet.execute(sql_Disease_phenotype_Orphanet, (disease,))
    values = cursor_Disease_phenotype_Orphanet.fetchall()
    cursor_Disease_phenotype_Orphanet.close()
    for value in values:
        id_onto_hp = value[0]
        term       = value[1]
        freq       = value[2]
        term_ja    = value[3]
        if freq == "453310":
            freq = "Obligate (100%)"
        elif freq == "453311":
            freq = "Very frequent (99-80%)"
        elif freq == "453312":
            freq = "Frequent (79-30%)"
        elif freq == "453313":
            freq = "Occasional (29-5%)"
        elif freq == "453314":
            freq = "Very rare (4-1%)"
        elif freq == "453315":
            freq = "Excluded (0%)"

        dict_Disease_phenotype_Orphanet = {}
        dict_Disease_phenotype_Orphanet['id_onto_hp']    = id_onto_hp
        #dict_Disease_phenotype_Orphanet['term']          = term if get_locale() == "en" or term_ja == "" else term_ja
        dict_Disease_phenotype_Orphanet['term']          = term_ja if (get_locale() == "ja" or get_locale() == "ja_JP") and term_ja != "" else term
        dict_Disease_phenotype_Orphanet['freq']          = freq
        list_dict_Disease_phenotype_Orphanet.append(dict_Disease_phenotype_Orphanet)


    #####
    # Diseaseテーブルから対象疾患の全てのフェノタイプを取得（症例報告から取得したフェノタイプのみ）
    list_dict_Disease_phenotype_CaseReport = []
    #sql_Disease_phenotype_CaseReport = u"select a.OntoIDHP, b.OntoTerm, a.Frequency from Disease as a left join OntoTermHP as b on a.OntoIDHP=b.OntoID where b.OntoType='label' and a.Source='CaseReport' and a.OntoIDORDO=%s order by cast(a.Frequency as SIGNED) desc, a.OntoIDHP"
    sql_Disease_phenotype_CaseReport = u"select a.OntoIDHP, b.OntoName, a.Frequency, b.OntoNameJa from Disease as a left join OntoTermHPInformation as b on a.OntoIDHP=b.OntoID where a.Source='CaseReport' and a.OntoIDORDO=%s order by cast(a.Frequency as SIGNED) desc, a.OntoIDHP"
    cursor_Disease_phenotype_CaseReport = OBJ_MYSQL.cursor()
    cursor_Disease_phenotype_CaseReport.execute(sql_Disease_phenotype_CaseReport, (disease,))
    values = cursor_Disease_phenotype_CaseReport.fetchall()
    cursor_Disease_phenotype_CaseReport.close()
    for value in values:
        id_onto_hp = value[0]
        term       = value[1]
        freq       = value[2]
        term_ja    = value[3]

        dict_Disease_phenotype_CaseReport = {}
        dict_Disease_phenotype_CaseReport['id_onto_hp']    = id_onto_hp
        #dict_Disease_phenotype_CaseReport['term']          = term if get_locale() == "en" or term_ja == "" else term_ja
        dict_Disease_phenotype_CaseReport['term']          = term_ja if (get_locale() == "ja" or get_locale() == "ja_JP") and term_ja != "" else term
        dict_Disease_phenotype_CaseReport['freq']          = freq
        list_dict_Disease_phenotype_CaseReport.append(dict_Disease_phenotype_CaseReport)


    #####
    # DiseaseGeneテーブルから対象疾患の全ての疾患原因遺伝子を取得
    list_dict_DiseaseGene_gene = []
    sql_DiseaseGene_gene = u"select OrphaNumber, Name, Symbol, Source, EntrezID from DiseaseGene where OntoIDORDO=%s"
    cursor_DiseaseGene_gene = OBJ_MYSQL.cursor()
    cursor_DiseaseGene_gene.execute(sql_DiseaseGene_gene, (disease,))
    values = cursor_DiseaseGene_gene.fetchall()
    cursor_DiseaseGene_gene.close()
    for value in values:
        orpha_number = value[0]
        name         = value[1]
        symbol       = value[2]
        source       = value[3]
        entrez_id    = value[4]
        dict_DiseaseGene_gene = {}
        dict_DiseaseGene_gene['orpha_number'] = orpha_number
        dict_DiseaseGene_gene['name']         = name
        dict_DiseaseGene_gene['symbol']       = symbol
        dict_DiseaseGene_gene['source']       = source
        dict_DiseaseGene_gene['entrez_id']    = entrez_id.replace('ENT:', '')
        list_dict_DiseaseGene_gene.append(dict_DiseaseGene_gene)


    #####
    # total件数を取得
    total_hit = len(list_dict_similar_casereport)
    pagination = Pagination(int(page), limit, total_hit)


    #####
    # データをpaginationの設定に合わせて切り出す
    start = (int(page) - 1) * limit
    end = start + limit
    list_dict_similar_casereport_pagination = list_dict_similar_casereport[start:end]

    OBJ_MYSQL.close()

    return list_dict_phenotype, list_dict_gene, list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene


#####
# search similar case report
# 患者の症状と症例報告との類似性検索
#####
def search_similar_casereport(str_disease, str_phenotypes, str_genes):
    # クエリの症状（HP ID）を収納
    list_phenotypes              = str_phenotypes.split(",")
    # クエリのフィルタリングID（HP,ENT,MT,MSH）を収納
    list_genes                   = str_genes.split(",")
    dict_filter_id               = {}
    for filter_id in list_genes:
        dict_filter_id[filter_id] = 1
    # フィルタリング対象となるPMIDを収納
    dict_filter_pmid             = {}
    # 類似症例報告検索結果を収納
    dict_similar_casereports     = {}
    list_dict_similar_casereport = []



    #####
    # MySQL接続　初期設定
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")


    #####
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


    #####
    # CommonRootHPテーブルから、患者の症状と全症状に対する共通ルートを取得
    dict_common_root_hp_ic = {}
    sql_CommonRootHP = u"select OntoIDHP1, OntoIDHP2, CommonRootOntoIDHP, CommonRootOntoIDHPIC from CommonRootHP where OntoIDHP1 in (%s)"
    in_p=', '.join(map(lambda x: '%s', list_phenotypes))
    sql_CommonRootHP = sql_CommonRootHP % in_p
    cursor_CommonRootHP = OBJ_MYSQL.cursor()
    cursor_CommonRootHP.execute(sql_CommonRootHP, list_phenotypes)
    values = cursor_CommonRootHP.fetchall()
    cursor_CommonRootHP.close()
    for value in values:
        onto_id_hp_1              = value[0]
        onto_id_hp_2              = value[1]
        common_root_onto_id_hp    = value[2]
        common_root_onto_id_hp_ic = value[3]
        if not onto_id_hp_1 in dict_common_root_hp_ic:
            dict_common_root_hp_ic[onto_id_hp_1] = {}
        dict_common_root_hp_ic[onto_id_hp_1][onto_id_hp_2] = float(common_root_onto_id_hp_ic)


    #####
    # AnnotOntoORDOHPテーブルから指定された疾患に関する症例報告と、それら症例報告に含まれる症状を取得
    dict_similar_casereports = {}
    sql_AnnotOntoORDOHP = u"select distinct OntoIDHP, PMID from AnnotOntoORDOHP where OntoIDORDO=%s order by PMID, OntoIDHP"
    cursor_AnnotOntoORDOHP = OBJ_MYSQL.cursor()
    cursor_AnnotOntoORDOHP.execute(sql_AnnotOntoORDOHP, (str_disease,))
    values = cursor_AnnotOntoORDOHP.fetchall()
    cursor_AnnotOntoORDOHP.close()
    for value in values:
        onto_id_hp = value[0]
        pmid       = value[1]

        # フィルタリング用のデータ収納
        if onto_id_hp in dict_filter_id:
            dict_filter_pmid[pmid] = 1
        
        # 対象疾患の症例報告とその症状を収納
        if pmid in dict_similar_casereports:
            (dict_similar_casereports[pmid]['list_casereport_onto_id_hp']).append(onto_id_hp)
        else:
            dict_similar_casereports[pmid] = {}
            dict_similar_casereports[pmid]['list_casereport_onto_id_hp'] = []
            (dict_similar_casereports[pmid]['list_casereport_onto_id_hp']).append(onto_id_hp)


    #####
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


    #####
    # 患者の症状セットをクエリとし、各症例報告との類似度を計算
    ## 疾患との類似性はMySQLのインデックスを利用しているが、症例報告はデータ数が多いためインデックを作成できない
    ## そのため、ここで一つずつmaxのicを求める
    ## この部分で時間がかかっている
    for pmid in dict_similar_casereports.keys():
        list_casereport_onto_id_hp = dict_similar_casereports[pmid]['list_casereport_onto_id_hp']
        sum_max_ic = 0
        sum_ic_denominator = 0
        list_dict_casereport_bestmatch_onto_id_term_hp = []
        # 患者の症状セット
        for patient_onto_id_hp in list_phenotypes:
            max_ic = 0
            max_ic_casereport_onto_id_hp = ""
            # 文献の症状セット
            for casereport_onto_id_hp in list_casereport_onto_id_hp:
                # BUGFIX: 2017/10/07
                ## keyが空の場合あり
                if patient_onto_id_hp in dict_common_root_hp_ic:
                    ic = dict_common_root_hp_ic[patient_onto_id_hp][casereport_onto_id_hp]
                if ic > max_ic:
                    max_ic = ic
                    max_ic_casereport_onto_id_hp = casereport_onto_id_hp

            # ICが0のエントリーが指定されると、分母の方が小さくなるため、分母のICが0の場合は分子のICも0にする
            if patient_onto_id_hp in dict_IC and  dict_IC[patient_onto_id_hp] != 0:
                # 分母
                sum_ic_denominator += dict_IC[patient_onto_id_hp]
                # 最も高いICを足し合わせ、そのIDおよびTermを収納
                sum_max_ic += max_ic
            else:
                # 分母
                sum_ic_denominator += 0
                # 最も高いICを足し合わせ、そのIDおよびTermを収納
                sum_max_ic += 0
                
            dict_casereport_bestmatch_onto_id_term_hp = {}
            dict_casereport_bestmatch_onto_id_term_hp['onto_id_hp'] = max_ic_casereport_onto_id_hp
            dict_casereport_bestmatch_onto_id_term_hp['onto_term_hp'] = dict_OntoTerm_hp[max_ic_casereport_onto_id_hp]
            list_dict_casereport_bestmatch_onto_id_term_hp.append(dict_casereport_bestmatch_onto_id_term_hp)

        # マッチスコアとベストマッチ症状を収納
        dict_similar_casereports[pmid]['sum_ic']                                         = sum_max_ic
        dict_similar_casereports[pmid]['sum_ic_denominator']                             = sum_ic_denominator
        dict_similar_casereports[pmid]['list_dict_casereport_bestmatch_onto_id_term_hp'] = list_dict_casereport_bestmatch_onto_id_term_hp


    #####
    # CaseReportGeneテーブルから各症例報告にアノテーションされた遺伝子名セットを取得
    dict_casereport_gene = {}
    sql_CaseReportGene = u"select PMID, EntrezID, SymbolSynonym, Symbol from CaseReportGene"
    cursor_CaseReportGene = OBJ_MYSQL.cursor()
    cursor_CaseReportGene.execute(sql_CaseReportGene)
    values = cursor_CaseReportGene.fetchall()
    cursor_CaseReportGene.close()
    for value in values:
        pmid           = value[0]
        entrezid       = value[1]
        symbol_synonym = value[2]
        symbol         = value[3]

        # フィルタリング用のデータ収納
        if "ENT:" + str(entrezid) in dict_filter_id:
            dict_filter_pmid[pmid] = 1

        # アノテーションんされた遺伝子名セットを収納
        if pmid in dict_casereport_gene:
            dict_entrezid_symbol_synonym = {}
            dict_entrezid_symbol_synonym['entrezid'] = entrezid
            dict_entrezid_symbol_synonym['symbol'] = symbol
            dict_entrezid_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_casereport_gene[pmid]['list_dict_entrezid_symbol_synonym']).append(dict_entrezid_symbol_synonym)
        else:
            dict_casereport_gene[pmid] = {}
            dict_casereport_gene[pmid]['list_dict_entrezid_symbol_synonym'] = []
            dict_entrezid_symbol_synonym = {}
            dict_entrezid_symbol_synonym['entrezid'] = entrezid
            dict_entrezid_symbol_synonym['symbol'] = symbol
            dict_entrezid_symbol_synonym['symbol_synonym'] = symbol_synonym
            (dict_casereport_gene[pmid]['list_dict_entrezid_symbol_synonym']).append(dict_entrezid_symbol_synonym)


    #####
    # CaseReportMutationテーブルから各症例報告にアノテーションされた変異セットを取得
    dict_casereport_mutation = {}
    sql_CaseReportMutation = u"select id, PMID, UID, ComponentMention, Component, Mention from CaseReportMutation"
    cursor_CaseReportMutation = OBJ_MYSQL.cursor()
    cursor_CaseReportMutation.execute(sql_CaseReportMutation)
    values = cursor_CaseReportMutation.fetchall()
    cursor_CaseReportMutation.close()
    for value in values:
        id                = value[0]
        pmid              = value[1]
        uid               = value[2]
        component_mention = value[3]
        component         = value[4]
        mention           = value[5]

        # フィルタリング用のデータ収納
        if uid in dict_filter_id:
            dict_filter_pmid[pmid] = 1

        # アノテーションされた変異情報セットを収納
        if pmid in dict_casereport_mutation:
            dict_id_component_mention = {}
            dict_id_component_mention['id'] = id
            dict_id_component_mention['component'] = component
            dict_id_component_mention['mention'] = mention
            dict_id_component_mention['component_mention'] = component_mention
            (dict_casereport_mutation[pmid]['list_dict_id_component_mention']).append(dict_id_component_mention)
        else:
            dict_casereport_mutation[pmid] = {}
            dict_casereport_mutation[pmid]['list_dict_id_component_mention'] = []
            dict_id_component_mention = {}
            dict_id_component_mention['id'] = id
            dict_id_component_mention['component'] = component
            dict_id_component_mention['mention'] = mention
            dict_id_component_mention['component_mention'] = component_mention
            (dict_casereport_mutation[pmid]['list_dict_id_component_mention']).append(dict_id_component_mention)


    #####
    # MESHInformationテーブルからMeSHの日本語ラベルを取得
    dict_mesh_ja = {}
    sql_MESHInformation = u"select MESHID, LabelJa from MESHInformation"
    cursor_MESHInformation = OBJ_MYSQL.cursor()
    cursor_MESHInformation.execute(sql_MESHInformation)
    values = cursor_MESHInformation.fetchall()
    cursor_MESHInformation.close()
    for value in values:
        id_mesh = value[0]
        label_ja = value[1]
        dict_mesh_ja[id_mesh] = label_ja


    #####
    # PMID_MESHテーブルから各症例報告にアノテーションされたMeSHセットを取得
    dict_casereport_mesh = {}
    for pmid in dict_similar_casereports.keys():
        # PMIDのクエリを数値にするとすごく遅いので、シングルクオーテーションで囲み文字列とする
        sql_PMID_MESH = u"select SDUI, STR from PMID_MESH where crFlg='1' and PMID='%s'"
        cursor_PMID_MESH = OBJ_MYSQL.cursor()
        cursor_PMID_MESH.execute(sql_PMID_MESH, (pmid,))
        values = cursor_PMID_MESH.fetchall()
        cursor_PMID_MESH.close()
        for value in values:
            sdui_mesh = value[0]
            str_mesh = value[1]

            # 日本語のラベルが存在する場合は、日本語のラベルに変換
            if get_locale() == "ja" or get_locale() == "ja_JP":
                str_mesh = dict_mesh_ja[sdui_mesh] if sdui_mesh in dict_mesh_ja else str_mesh

            if len(str_mesh) > 50:
                str_mesh = str_mesh[:50] + "..."
            if sdui_mesh == "":
                continue

            # フィルタリング用のデータ収納
            if "MSH:" + sdui_mesh in dict_filter_id:
                dict_filter_pmid[pmid] = 1

            # アノテーションされたMeSHセットを収納
            if pmid in dict_casereport_mesh:
                dict_sdui_str_mesh = {}
                dict_sdui_str_mesh['sdui'] = sdui_mesh
                dict_sdui_str_mesh['str'] = str_mesh
                (dict_casereport_mesh[pmid]['list_dict_sdui_str_mesh']).append(dict_sdui_str_mesh)
            else:
                dict_casereport_mesh[pmid] = {}
                dict_casereport_mesh[pmid]['list_dict_sdui_str_mesh'] = []
                dict_sdui_str_mesh = {}
                dict_sdui_str_mesh['sdui'] = sdui_mesh
                dict_sdui_str_mesh['str'] = str_mesh
                (dict_casereport_mesh[pmid]['list_dict_sdui_str_mesh']).append(dict_sdui_str_mesh)


    #####
    # 各症例報告の書誌情報を取得
    for pmid in dict_similar_casereports.keys():
        sql_CaseReports = u"select PMCID, title, authors, so, pyear, journal, country, sex, age, inheritanceMode from CaseReports where PMID=%s"
        cursor_CaseReports = OBJ_MYSQL.cursor()
        cursor_CaseReports.execute(sql_CaseReports, (pmid,))
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

        dict_similar_casereports[pmid]['PMCID']   = PMCID
        dict_similar_casereports[pmid]['title']   = title
        dict_similar_casereports[pmid]['authors'] = authors
        dict_similar_casereports[pmid]['so']      = so
        dict_similar_casereports[pmid]['pyear']   = pyear
        dict_similar_casereports[pmid]['journal'] = journal
        dict_similar_casereports[pmid]['sex']     = sex
        dict_similar_casereports[pmid]['age']     = age


    OBJ_MYSQL.close()



    #####
    # 類似症例報告検索結果を収納
    for pmid in dict_similar_casereports.keys():

        # ユーザが入力したgenesでフィルタリング
        #if str_genes != "" and not dict_filter_casereport_gene.has_key(pmid):
        if str_genes != "" and not pmid in dict_filter_pmid:
            continue

        dict_similar_casereport = {}
        # PMID
        dict_similar_casereport['pmid']                                           = pmid
        # Score
        dict_similar_casereport['sum_ic']                                         = dict_similar_casereports[pmid]['sum_ic']
        dict_similar_casereport['sum_ic_denominator']                             = dict_similar_casereports[pmid]['sum_ic_denominator']
        if dict_similar_casereport['sum_ic_denominator'] != 0:
            dict_similar_casereport['match_score']                                = float(dict_similar_casereports[pmid]['sum_ic'] / dict_similar_casereports[pmid]['sum_ic_denominator'])
        else:
            dict_similar_casereport['match_score']                                = 0
        # 症例報告の全ての症状セット(HP ID)
        dict_similar_casereport['list_casereport_onto_id_hp']                     = dict_similar_casereports[pmid]['list_casereport_onto_id_hp']
        # 症例報告のベストマッチ症状セット(HP ID + HP Term)
        dict_similar_casereport['list_dict_casereport_bestmatch_onto_id_term_hp'] = sorted(dict_similar_casereports[pmid]['list_dict_casereport_bestmatch_onto_id_term_hp'], key=lambda x: x['onto_id_hp'])
        # Gene
        dict_similar_casereport['list_dict_entrezid_symbol_synonym']              = sorted(dict_casereport_gene[pmid]['list_dict_entrezid_symbol_synonym'], key=lambda x: x['symbol']) if pmid in dict_casereport_gene else []
        # Mutation
        dict_similar_casereport['list_dict_id_component_mention']                 = sorted(dict_casereport_mutation[pmid]['list_dict_id_component_mention'], key=lambda x: x['component']) if pmid in dict_casereport_mutation else []
        # MeSH
        dict_similar_casereport['list_dict_sdui_str_mesh']                         = sorted(dict_casereport_mesh[pmid]['list_dict_sdui_str_mesh'], key=lambda x: x['str']) if pmid in dict_casereport_mesh else []
        # PMCID
        dict_similar_casereport['PMCID']   = dict_similar_casereports[pmid]['PMCID']
        # title
        dict_similar_casereport['title']   = dict_similar_casereports[pmid]['title']
        # authors
        dict_similar_casereport['authors'] = dict_similar_casereports[pmid]['authors']
        # so
        dict_similar_casereport['so']      = dict_similar_casereports[pmid]['so']
        # pyear
        dict_similar_casereport['pyear']   = dict_similar_casereports[pmid]['pyear']
        # journal
        dict_similar_casereport['journal'] = dict_similar_casereports[pmid]['journal']
        # sex
        dict_similar_casereport['sex']     = dict_similar_casereports[pmid]['sex']
        # age
        dict_similar_casereport['age']     = dict_similar_casereports[pmid]['age']


        list_dict_similar_casereport.append(dict_similar_casereport)


    #####
    # sort
    ## jinja2側でソートするとエラーになるので、予めソートする
    ### 数値のソート方法　http://d.hatena.ne.jp/yumimue/20071218/1197985024
    list_dict_similar_casereport_sorted = []
    rank = 0
    rank_deposit = 0
    #prev_sum_ic = 0
    #for dict_similar_casereport in sorted(list_dict_similar_casereport, key=lambda x: (-float(x['sum_ic']),-x['pmid'])):
    #    if dict_similar_casereport['sum_ic'] != prev_sum_ic:
    #        rank = rank + 1 + rank_deposit 
    #        dict_similar_casereport['rank'] = rank
    #        prev_sum_ic = dict_similar_casereport['sum_ic']
    #        rank_deposit = 0
    #    else:
    #        dict_similar_casereport['rank'] = rank
    #        prev_sum_ic = dict_similar_casereport['sum_ic']
    #        rank_deposit += 1

    prev_match_score = 0
    for dict_similar_casereport in sorted(list_dict_similar_casereport, key=lambda x: (-float(x['match_score']),-x['pmid'])):
        if dict_similar_casereport['match_score'] != prev_match_score:
            rank = rank + 1 + rank_deposit 
            dict_similar_casereport['rank'] = rank
            prev_match_score = dict_similar_casereport['match_score']
            rank_deposit = 0
        else:
            dict_similar_casereport['rank'] = rank
            prev_match_score = dict_similar_casereport['match_score']
            rank_deposit += 1


        list_dict_similar_casereport_sorted.append(dict_similar_casereport)

    return list_dict_similar_casereport_sorted

