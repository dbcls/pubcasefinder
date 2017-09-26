# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re
import MySQLdb
import json
import sys
from werkzeug import secure_filename

# Seach core
from utils.pagination import Pagination
from utils.show_search_page import show_search_page
from utils.show_disease_casereport_page import show_disease_casereport_page
from utils.show_phenotype_context_page import show_phenotype_context_page

# API for MME
from utils.api_mme import make_JSON_MME, make_JSON_IRUD


app = Flask(__name__)

#####
# DB設定
app.config.from_pyfile('config.cfg')
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


#####
# url_for_search_page()
# Jinja2からこのメソッドを経由して、類似疾患検索ページの各APIへアクセス
#####
def url_for_search_page(phenotypes, genes, page, cs):
    if phenotypes != "" and genes != "":
        return url_for('REST_API_search_phenotypes_genes', phenotypes=phenotypes, genes=genes, page=page, size=cs)
    elif phenotypes != "":
        return url_for('REST_API_search_phenotypes', phenotypes=phenotypes, page=page, size=cs)
    elif genes != "":
        return url_for('REST_API_search_genes', genes=genes, page=page, size=cs)
    else:
        return url_for('REST_API_search_none', page=page, size=cs)
app.jinja_env.globals['url_for_search_page'] = url_for_search_page



#####
# url_for_disease_casereport_page()
# Jinja2からこのメソッドを経由して、疾患別類似症例報告検索画面の各APIへアクセス
#####
def url_for_disease_casereport_page(disease, phenotypes, genes, page, cs):
    if phenotypes != "" and genes != "":
        return url_for('REST_API_disease_casereport_phenotypes_genes', disease=disease, phenotypes=phenotypes, genes=genes, page=page, size=cs)
    elif phenotypes != "":
        return url_for('REST_API_disease_casereport_phenotypes', disease=disease, phenotypes=phenotypes, page=page, size=cs)
    elif genes != "":
        return url_for('REST_API_disease_casereport_genes', disease=disease, genes=genes, page=page, size=cs)
    else:
        return url_for('REST_API_disease_casereport_none', disease=disease, page=page, size=cs)
app.jinja_env.globals['url_for_disease_casereport_page'] = url_for_disease_casereport_page



#####
# url_for_show_phenotype_context_page()
# Jinja2からこのメソッドを経由して、フェノタイプコンテキスト表示ページの各APIへアクセス
#####
def url_for_show_phenotype_context_page(disease, phenotype, page, size):
    return url_for('REST_API_show_phenotype_context', disease=disease, phenotype=phenotype, page=page, size=size)
app.jinja_env.globals['url_for_show_phenotype_context_page'] = url_for_show_phenotype_context_page



#####
# Routing
# http://qiita.com/Morinikki/items/c2af4ffa180856d1bf30
# http://flask.pocoo.org/docs/0.12/quickstart/
#####

#####
# index page
## GET: display top page
@app.route('/')
def index():
    return render_template('index.html')


#####
# terms of service in English
## GET: 
@app.route('/termsofservice_en')
def termsofservice_en():
    return render_template('termsofservice_en.html')


#####
# terms of service in Japanese
## GET:
@app.route('/termsofservice_ja')
def termsofservice_ja():
    return render_template('termsofservice_ja.html')


#####
# search page
## GET: show search page with phenotype and gene
@app.route('/search_disease/phenotype:<string:phenotypes>/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_search_phenotypes_genes(phenotypes, genes, page, size):
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, size)
        return render_template('search.html',
                               str_phenotypes=phenotypes,
                               str_genes=genes,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               json_genes=json.dumps(list_dict_gene),
                               list_dict_similar_disease=list_dict_similar_disease_pagination,
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size)
    else:
        return render_template('index.html')


## GET: show search page with phenotype
@app.route('/search_disease/phenotype:<string:phenotypes>/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_search_phenotypes(phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, size)
        return render_template('search.html',
                               str_phenotypes=phenotypes, 
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_disease=list_dict_similar_disease_pagination, 
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size)
    else:
        return render_template('index.html')

    return


## GET: show search page with gene
@app.route('/search_disease/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_search_genes(genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, size)
        return render_template('search.html',
                               str_phenotypes=phenotypes, 
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_disease=list_dict_similar_disease_pagination, 
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size)
    else:
        return render_template('index.html')

    return


## GET: show search page without phenotype and gene
@app.route('/search_disease/phenotype:/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_search_none(page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, size)
        return render_template('search.html',
                               str_phenotypes=phenotypes, 
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_disease=list_dict_similar_disease_pagination, 
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size)
    else:
        return render_template('index.html')

    return


## POST: show search page
@app.route('/search_disease', methods=['POST'])
def search_POST():

    if request.method == 'POST':
        # changesize_selector
        size = request.form['changesize_selector']

        # requestオブジェクトからクエリのphenotypesを取得
        phenotypes = request.form['str_phenotypes']
        list_phenotypes = phenotypes.split(',')

        # requestオブジェクトからクエリのgenesを取得
        genes = request.form['str_genes']
        list_genes = genes.split(',')

        ##### 
        # HPO リストを含むファイルを処理
        # requestオブジェクトからfileを取得
        if 'file_hpo_list' in request.files:
            file = request.files['file_hpo_list']
            if file:
            #if file and validateFileSize(file):
                phenotypes_file = file.stream.read()
                phenotypes_file = phenotypes_file.replace('\n',',')
                phenotypes_file = phenotypes_file.replace('\r',',')
                phenotypes_file = re.sub(r',+', ',', phenotypes_file)
                phenotypes_file = re.sub(r'^,+', '', phenotypes_file)
                phenotypes_file = re.sub(r',+$', '', phenotypes_file)

                ## 入力チェック
                list_phenotypes_file = phenotypes_file.split(',')
                list_phenotypes_file_removed = []
                for phenotype in list_phenotypes_file:
                    ## HP:\d+ に沿わないエントリーは削除
                    pattern = r"^HP\:\d+$"
                    match = re.search(pattern, phenotype)
                    if match:
                        list_phenotypes_file_removed.append(phenotype)

                ## テキストボックスの遺伝子リストとファイル内の遺伝子リストを結合
                list_phenotypes.extend(list_phenotypes_file_removed)

        ## リスト内の重複を削除
        list_phenotypes_uniq = []
        for phenotype in list_phenotypes:
            if phenotype not in list_phenotypes_uniq:
                list_phenotypes_uniq.append(phenotype)

        phenotypes = ','.join(list_phenotypes_uniq)
        phenotypes = re.sub(r'^,+', '', phenotypes)
        phenotypes = re.sub(r',+$', '', phenotypes)

        ##### 
        # Entrez Gene ID リストを含むファイルを処理
        # requestオブジェクトからfileを取得
        if 'file_gene_list' in request.files:
            file = request.files['file_gene_list']
            if file:
            #if file and validateFileSize(file):
                genes_file = file.stream.read()
                genes_file = genes_file.replace('\n',',')
                genes_file = genes_file.replace('\r',',')
                genes_file = re.sub(r',+', ',', genes_file)
                genes_file = re.sub(r'^,+', '', genes_file)
                genes_file = re.sub(r',+$', '', genes_file)
                genes_file = "ENT:" + genes_file.replace(',',',ENT:')

                ## 入力チェック
                list_genes_file = genes_file.split(',')
                list_genes_file_removed = []
                for gene in list_genes_file:
                    ## ENT:\d+ に沿わないエントリーは削除
                    pattern = r"^ENT\:\d+$"
                    match = re.search(pattern, gene)
                    if match:
                        list_genes_file_removed.append(gene)

                ## テキストボックスの遺伝子リストとファイル内の遺伝子リストを結合
                list_genes.extend(list_genes_file_removed)

        ## リスト内の重複を削除
        list_genes_uniq = []
        for gene in list_genes:
            if gene not in list_genes_uniq:
                list_genes_uniq.append(gene)

        genes = ','.join(list_genes_uniq)
        genes = re.sub(r'^,+', '', genes)
        genes = re.sub(r',+$', '', genes)


        # ページ初期値
        page=1

        # POSTメソッドをRESTのURLにredirect
        if phenotypes != "" and genes != "":
            # httpsに対応するためにurl_forのオプション（_external, _scheme）を設定
            # https://stackoverflow.com/questions/14810795/flask-url-for-generating-http-url-instead-of-https
            return redirect(url_for('REST_API_search_phenotypes_genes', _external=True, _scheme='https', phenotypes=phenotypes, genes=genes, page=page, size=size))
        elif phenotypes != "":
            return redirect(url_for('REST_API_search_phenotypes', _external=True, _scheme='https', phenotypes=phenotypes, page=page, size=size))
        elif genes != "":
            return redirect(url_for('REST_API_search_genes', _external=True, _scheme='https', genes=genes, page=page, size=size))
        else:
            return redirect(url_for('REST_API_search_none', _external=True, _scheme='https', page=page, size=size))
    else:
        return render_template('index.html')


#####
# disease_casereport page
# GET: show disease_casereport page with phenotype and gene
#####
@app.route('/disease_casereport/disease:<string:disease>/phenotype:<string:phenotypes>/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_disease_casereport_phenotypes_genes(disease, phenotypes, genes, page, size):
    if request.method == 'GET' or request.method == 'POST':
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition = show_disease_casereport_page(disease, phenotypes, genes, page, size)
        return render_template('disease_casereport.html',
                               str_disease=disease,
                               str_phenotypes=phenotypes,
                               str_genes=genes,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               json_genes=json.dumps(list_dict_gene),
                               list_dict_similar_casereport=list_dict_similar_casereport_pagination,
                               dict_onto_id_term_ordo=dict_onto_id_term_ordo,
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size,
                               str_disease_definition=disease_definition
                           )
    else:
        return render_template('index.html')


#####
## GET: show disease_casereport page with phenotype
#####
@app.route('/disease_casereport/disease:<string:disease>/phenotype:<string:phenotypes>/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_disease_casereport_phenotypes(disease, phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition = show_disease_casereport_page(disease, phenotypes, genes, page, size)
        return render_template('disease_casereport.html',
                               str_disease=disease,
                               str_phenotypes=phenotypes, 
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_casereport=list_dict_similar_casereport_pagination, 
                               dict_onto_id_term_ordo=dict_onto_id_term_ordo,
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size,
                               str_disease_definition=disease_definition
        )
    else:
        return render_template('index.html')

    return


## GET: show disease_casereport page with gene
@app.route('/disease_casereport/disease:<string:disease>/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_disease_casereport_genes(disease, genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition = show_disease_casereport_page(disease, phenotypes, genes, page, size)
        return render_template('disease_casereport.html',
                               str_disease=disease,
                               str_phenotypes=phenotypes, 
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_casereport=list_dict_similar_casereport_pagination, 
                               dict_onto_id_term_ordo=dict_onto_id_term_ordo,
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size,
                               str_disease_definition=disease_definition
        )
    else:
        return render_template('index.html')

    return


## GET: show disease_casereport page without phenotype and gene
@app.route('/disease_casereport/disease:<string:disease>/phenotype:/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_disease_casereport_none(disease, page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition = show_disease_casereport_page(disease, phenotypes, genes, page, size)
        return render_template('disease_casereport.html',
                               str_disease=disease,
                               str_phenotypes=phenotypes,
                               str_genes=genes, 
                               json_phenotypes=json.dumps(list_dict_phenotype), 
                               json_genes=json.dumps(list_dict_gene), 
                               list_dict_similar_casereport=list_dict_similar_casereport_pagination, 
                               dict_onto_id_term_ordo=dict_onto_id_term_ordo,
                               pagination=pagination,
                               total_hit=total_hit,
                               cs=size,
                               str_disease_definition=disease_definition
        )
    else:
        return render_template('index.html')

    return


## POST: show disease_casereport page via REST API
@app.route('/disease_casereport', methods=['POST'])
def disease_casereport_POST():

    if request.method == 'POST':
        # changesize_selector
        size = request.form['changesize_selector']

        # requestオブジェクトからクエリのphenotypesを取得
        disease = request.form['str_disease']

        # requestオブジェクトからクエリのphenotypesを取得
        phenotypes = request.form['str_phenotypes']

        # requestオブジェクトからクエリのgenesを取得
        genes = request.form['str_genes']

        page=1

        # POSTメソッドをRESTのURLにredirect
        if phenotypes != "" and genes != "":
            # httpsに対応するためにurl_forのオプション（_external, _scheme）を設定
            # https://stackoverflow.com/questions/14810795/flask-url-for-generating-http-url-instead-of-https
            return redirect(url_for('REST_API_disease_casereport_phenotypes_genes', _external=True, _scheme='https', disease=disease, phenotypes=phenotypes, genes=genes, page=page, size=size))
        elif phenotypes != "":
            return redirect(url_for('REST_API_disease_casereport_phenotypes', _external=True, _scheme='https', disease=disease, phenotypes=phenotypes, page=page, size=size))
        elif genes != "":
            return redirect(url_for('REST_API_disease_casereport_genes', _external=True, _scheme='https', disease=disease, genes=genes, page=page, size=size))
        else:
            return redirect(url_for('REST_API_disease_casereport_none', _external=True, _scheme='https', disease=disease, page=page, size=size))
    else:
        return render_template('index.html')



#####
# phenotype_context page
## GET: display phenotype_context page
@app.route('/phenotype_context/disease:<string:disease>/phenotype:<string:phenotype>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_show_phenotype_context(disease, phenotype, page, size):
    term_disease, term_phenotype, list_dict_phenotype_context, pagination, total_hit = show_phenotype_context_page(disease, phenotype, page, size)
    nonprefix_disease = disease.replace('ORDO:', '')
    return render_template('phenotype_context.html',
                           id_disease=disease,
                           id_nonprefix_disease=nonprefix_disease,
                           id_phenotype=phenotype,
                           term_disease=term_disease,
                           term_phenotype=term_phenotype,
                           list_dict_phenotype_context=list_dict_phenotype_context,
                           pagination=pagination,
                           total_hit=total_hit,
                           size=size)



#####
# tokeninput_hpo()
# complement input for phenotypes
#####
@app.route('/tokeninput_hpo', methods=['GET', 'POST'])
def tokeninput_hpo():

    list_json = []

    # GETメソッドの値を取得
    if request.method == 'GET':

        # requestから値を取得
        tokeninput = request.args.get("q")
        #hpo_list = request.args.get("hpo_list")

        # OntoTermテーブルからHPのtermを検索
        ## SQLのLIKEを使うときのTips
        ### http://d.hatena.ne.jp/heavenshell/20111027/1319712031
        OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
        sql_OntoTerm = u"select OntoID, OntoIDTerm from OntoTermHP where OntoType='label' and ObsoleteFlg=0 and PhenotypicAbnormalityFlg=1 and OntoIDTerm like %s order by OntoTerm"
        cursor_OntoTerm = OBJ_MYSQL.cursor()
        cursor_OntoTerm.execute(sql_OntoTerm, ("%" + tokeninput +"%",))
        values = cursor_OntoTerm.fetchall()
        cursor_OntoTerm.close()

        for value in values:
            dict_json = {}
            onto_id = value[0]
            onto_id_term = value[1]
            dict_json['id'] = onto_id
            dict_json['name'] = onto_id_term
            list_json.append(dict_json)

    OBJ_MYSQL.close()

    return jsonify(list_json)



#####
# tokeninput_genes()
# complement input for genes/variants
#####
@app.route('/tokeninput_genes', methods=['GET', 'POST'])
def tokeninput_genes():

    list_json = []

    # GETメソッドの値を取得
    if request.method == 'GET':

        # requestから値を取得
        tokeninput = request.args.get("q")

        # DiseaseGeneテーブルからSymbol及びSynonymを検索
        ## SQLのLIKEを使うときのTips
        ### http://d.hatena.ne.jp/heavenshell/20111027/1319712031
        OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
        # IndexFormSearchテーブルからクエリにマッチするレコードを取得
        sql_IndexFormSearch = u"select distinct uid, uid_value from IndexFormSearch where uid_value like %s order by uid_value"
        cursor_IndexFormSearch = OBJ_MYSQL.cursor()
        cursor_IndexFormSearch.execute(sql_IndexFormSearch, ("%" + tokeninput +"%",))
        values = cursor_IndexFormSearch.fetchall()
        cursor_IndexFormSearch.close()

        for value in values:
            dict_json = {}
            uid               = value[0]
            uid_value         = value[1]
            dict_json['id']   = uid
            dict_json['name'] = uid_value
            list_json.append(dict_json)

    OBJ_MYSQL.close()

    return jsonify(list_json)



#####
# tokeninput_filter_casereport()
# complement input for filter in Case Reports
#####
@app.route('/tokeninput_filter_casereport', methods=['GET', 'POST'])
def tokeninput_filter_casereport():

    list_json = []

    # GETメソッドの値を取得
    if request.method == 'GET':

        # requestから値を取得
        tokeninput = request.args.get("q")

        # DiseaseGeneテーブルからSymbol及びSynonymを検索
        ## SQLのLIKEを使うときのTips
        ### http://d.hatena.ne.jp/heavenshell/20111027/1319712031
        OBJ_MYSQL = MySQLdb.connect(unix_socket="/opt/services/case/local/mysql-5.7.13/mysql.sock", host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
        # IndexFormDiseaseCaseReportテーブルからクエリにマッチするレコードを取得
        sql_IndexFormDiseaseCaseReport = u"select distinct uid, uid_value from IndexFormDiseaseCaseReport where uid_value like %s order by uid_value"
        cursor_IndexFormDiseaseCaseReport = OBJ_MYSQL.cursor()
        cursor_IndexFormDiseaseCaseReport.execute(sql_IndexFormDiseaseCaseReport, ("%" + tokeninput +"%",))
        values = cursor_IndexFormDiseaseCaseReport.fetchall()
        cursor_IndexFormDiseaseCaseReport.close()

        for value in values:
            dict_json = {}
            uid       = value[0]
            uid_value = value[1]
            dict_json['id']   = uid
            dict_json['name'] = uid_value
            list_json.append(dict_json)

    OBJ_MYSQL.close()

    return jsonify(list_json)


#####
# GET: API for IRUD Exchange
#      show search page with phenotype and gene
#      /search/phenotype:HPO:Id,HPO:id/gene:gene1,gene2/size_disease:N/size_casereport:N
#####
@app.route('/search/phenotype:<string:phenotypes>/gene:<string:genes>/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_phenotypes_genes(phenotypes, genes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD(phenotypes, genes, size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange
#      show search page with phenotype
#      /search/phenotype:HPO:Id,HPO:id/gene:/size_disease:N/size_casereport:N
#####
@app.route('/search/phenotype:<string:phenotypes>/gene:/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_phenotypes(phenotypes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD(phenotypes, '', size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange
#      show search page with gene
#      /search/phenotype:/gene:gene1,gene2/size_disease:N/size_casereport:N
#####
@app.route('/search/phenotype:/gene:<string:genes>/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_genes(genes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD(genes, size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange
#      show search page without phenotype and gene
#      /search/phenotype:/gene:/size_disease:N/size_casereport:N
#####
@app.route('/search/phenotype:/gene:/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search(size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD(size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# POST: API for MME
#       search rare diseases based on phenotypic similarity
#       /mme/match
#####
@app.route('/mme/match', methods=['POST'])
def REST_API_JSON_MME_POST():
    pattern_content_type_json = r'application\/json*'
    pattern_content_type_matchmaker = r'application\/vnd.ga4gh.matchmaker.v\d+.\d+\+json*'
    if not re.search(pattern_content_type_json , request.headers['Content-Type']) and not re.search(pattern_content_type_matchmaker , request.headers['Content-Type']):
        print(request.headers['Content-Type'])
        return jsonify(res='Error: Content-Type'), 400

    # utils/api_mme.py
    dict_results = make_JSON_MME(request.json)

    return jsonify(dict_results)


#####
# GET: API for MME
#       redirect to top page
#       /mme
#####
@app.route('/mme', methods=['GET'])
def REST_API_JSON_MME_GET():
    return render_template('index.html')


#####
# Validate file size by parsing the entire file or up to MAX_FILE_SIZE, whichever comes first.
# This is done to prevent DoS attacks by forcing the system to parse the entirety of very large
# files to get the total size.
# This will force the file to be parsed twice, however; once for file size check, once to save
# the file data. Combine both to improve efficiency.
#####
def validateFileSize(file):
    chunk = 10 #chunk size to read per loop iteration; 10 bytes
    data = None
    size = 0

    #keep reading until out of data
    while data != b'':
        data = file.read(chunk)
        size += len(data)
        #return false if the total size of data parsed so far exceeds MAX_FILE_SIZE
        #if size >  app.config['MAX_FILE_SIZE']:
        if size >  1000000: # 1MB limit
            return False

    return True



