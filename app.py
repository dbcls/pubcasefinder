# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import os
import re
import MySQLdb
import json
import sys
import datetime
import copy
import mojimoji
from werkzeug import secure_filename
from io import StringIO, BytesIO
import csv
# https://blog.capilano-fw.com/?p=398
from flask_babel import gettext,Babel
from flask_cors import CORS

# Seach core
from utils.pagination import Pagination
from utils.show_search_page import show_search_page
from utils.show_search_omim_page import show_search_omim_page
from utils.show_disease_casereport_page import show_disease_casereport_page
from utils.show_phenotype_context_page import show_phenotype_context_page
from utils.check_input import process_input_phenotype, process_input_gene

# API for MME
from utils.api_mme import make_JSON_MME, make_JSON_IRUD
from utils.api_mme_omim import make_JSON_MME_omim, make_JSON_IRUD_omim

# API for Orphanet
from utils.api_orphanet import make_JSON_annotate


app = Flask(__name__)
CORS(app)


# https://github.com/shibacow/flask_babel_sample/blob/master/srv.py
babel = Babel(app)
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en'])
app.jinja_env.globals.update(get_locale=get_locale)

# debug
app.debug = True

#####
# DB設定
app.config.from_pyfile('config.cfg')
db_sock = app.config['DBSOCK']
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
# url_for_download_results_search_page()
# 類似疾患検索ページの結果をダウンロード（Orphanet）
#####
def url_for_download_results_search_page(phenotypes, genes, page, cs):
    if phenotypes != "" and genes != "":
        return url_for('REST_API_download_results_search_phenotypes_genes', phenotypes=phenotypes, genes=genes, page=page, size=cs)
    elif phenotypes != "":
        return url_for('REST_API_download_results_search_phenotypes', phenotypes=phenotypes, page=page, size=cs)
    elif genes != "":
        return url_for('REST_API_download_results_search_genes', genes=genes, page=page, size=cs)
    else:
        return url_for('REST_API_download_results_search_none', page=page, size=cs)
app.jinja_env.globals['url_for_download_results_search_page'] = url_for_download_results_search_page



#####
# url_for_download_results_search_omim_page()
# 類似疾患検索ページの結果をダウンロード（Orphanet）
#####
def url_for_download_results_search_omim_page(phenotypes, genes, page, cs):
    if phenotypes != "" and genes != "":
        return url_for('REST_API_download_results_search_omim_phenotypes_genes', phenotypes=phenotypes, genes=genes, page=page, size=cs)
    elif phenotypes != "":
        return url_for('REST_API_download_results_search_omim_phenotypes', phenotypes=phenotypes, page=page, size=cs)
    elif genes != "":
        return url_for('REST_API_download_results_search_omim_genes', genes=genes, page=page, size=cs)
    else:
        return url_for('REST_API_download_results_search_omim_none', page=page, size=cs)
app.jinja_env.globals['url_for_download_results_search_omim_page'] = url_for_download_results_search_omim_page



#####
# url_for_download_summary()
# OrphanetおよびOMIMの検索結果のサマリーをダウンロード
# 将来的には症例報告も付加する
#####
def url_for_download_summary(phenotypes, genes, page, cs):
    if phenotypes != "" and genes != "":
        return url_for('REST_API_download_summary_phenotypes_genes', phenotypes=phenotypes, genes=genes, page=page, size=cs)
    elif phenotypes != "":
        return url_for('REST_API_download_summary_phenotypes', phenotypes=phenotypes, page=page, size=cs)
    elif genes != "":
        return url_for('REST_API_download_summary_genes', genes=genes, page=page, size=cs)
    else:
        return url_for('REST_API_download_summary_none', page=page, size=cs)
app.jinja_env.globals['url_for_download_summary'] = url_for_download_summary



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
# PubCaseFinder API in English
## GET: 
@app.route('/pubcasefinder_api_en')
def pubcasefinder_api_en():
    return render_template('pubcasefinder_api_en.html')


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
@app.route('/search_disease/phenotype:<string:phenotypes>/gene:<string:genes>/page:<string:page>/size:<string:size>', methods=['GET'])
def REST_API_search_phenotypes_genes(phenotypes, genes, page, size):
    if request.method == 'GET':
        page_orphanet = "1"
        page_omim     = "1"
        size_orphanet = "10"
        size_omim     = "10"
        active_tab    = "orphanet"
        #active_tab    = "omim"
        
        list_pages = page.split(",")
        if len(list_pages) == 2:
            page_orphanet = list_pages[0]
            page_omim     = list_pages[1]
        elif len(list_pages) == 1:
            page_orphanet = list_pages[0]

        list_sizes = size.split(",")
        if len(list_sizes) == 3:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
            active_tab    = list_sizes[2]
        elif len(list_sizes) == 2:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
        elif len(list_sizes) == 1:
            size_orphanet = list_sizes[0]

        # process query : phenotypes
        list_dict_phenotype, phenotypes_remove_error, phenotypes_remove_error_ja = process_input_phenotype(phenotypes)

        # process query : genes
        list_dict_gene, genes_remove_error, list_query_gene_error = process_input_gene(genes)
        num_list_query_gene_error = len(list_query_gene_error)

        # search
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, int(page_orphanet), size_orphanet)
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, int(page_omim), size_omim)
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_error_ja, genes_remove_error, int(page_orphanet), size_orphanet)
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_error_ja, genes_remove_error, int(page_omim), size_omim)
        
        # PhenoTips登録用のデータを作成
        #phenotypes_phenotips = phenotypes.replace('_ja', '')
        eid = str(datetime.datetime.today())

        return render_template('search.html',
                               str_eid=eid,
                               str_phenotypes=phenotypes_remove_error,
                               str_phenotypes_remove_ja=phenotypes_remove_error_ja,
                               str_genes=genes_remove_error,
                               str_list_query_gene_error = ', '.join(list_query_gene_error),
                               num_list_query_gene_error = num_list_query_gene_error,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               #json_phenotypes_omim=json.dumps(list_dict_phenotype_omim),
                               json_genes=json.dumps(list_dict_gene),
                               #json_genes_omim=json.dumps(list_dict_gene_omim),
                               list_dict_similar_disease=list_dict_similar_disease_pagination,
                               list_dict_similar_disease_omim=list_dict_similar_disease_pagination_omim,
                               pagination=pagination,
                               pagination_omim=pagination_omim,
                               total_hit=total_hit,
                               total_hit_omim=total_hit_omim,
                               cs=size_orphanet,
                               cs_omim=str(size_omim),
                               active_tab=active_tab)
    else:
        return render_template('index.html')

    return


## GET: show search page with phenotype
@app.route('/search_disease/phenotype:<string:phenotypes>/gene:/page:<string:page>/size:<string:size>', methods=['GET'])
def REST_API_search_phenotypes(phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        page_orphanet = 1
        page_omim     = 1
        size_orphanet = 10
        size_omim     = 10
        active_tab    = "orphanet"
        #active_tab    = "omim"

        list_pages = page.split(",")
        if len(list_pages) == 2:
            page_orphanet = int(list_pages[0])
            page_omim     = int(list_pages[1])
        elif len(list_pages) == 1:
            page_orphanet = int(list_pages[0])

        list_sizes = size.split(",")
        if len(list_sizes) == 3:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
            active_tab    = list_sizes[2]
        elif len(list_sizes) == 2:
            size_orphanet = int(list_sizes[0])
            size_omim     = int(list_sizes[1])
        elif len(list_sizes) == 1:
            size_orphanet = int(list_sizes[0])

        # process query : phenotypes
        list_dict_phenotype, phenotypes_remove_error, phenotypes_remove_error_ja = process_input_phenotype(phenotypes)

        # process query : genes
        list_dict_gene, genes_remove_error, list_query_gene_error = process_input_gene(genes)
        num_list_query_gene_error = len(list_query_gene_error)

        # search
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page_orphanet, size_orphanet)
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, page_omim, size_omim)
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_error_ja, genes_remove_error, int(page_orphanet), size_orphanet)
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_error_ja, genes_remove_error, int(page_omim), size_omim)

        # PhenoTips登録用のデータを作成
        #phenotypes_phenotips = phenotypes.replace('_ja', '')
        eid = str(datetime.datetime.today())

        return render_template('search.html',
                               str_eid=eid,
                               str_phenotypes=phenotypes_remove_error,
                               str_phenotypes_remove_ja=phenotypes_remove_error_ja,
                               str_genes=genes_remove_error,
                               str_list_query_gene_error = ', '.join(list_query_gene_error),
                               num_list_query_gene_error = num_list_query_gene_error,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               #json_phenotypes_omim=json.dumps(list_dict_phenotype_omim),
                               json_genes=json.dumps(list_dict_gene),
                               #json_genes_omim=json.dumps(list_dict_gene_omim),
                               list_dict_similar_disease=list_dict_similar_disease_pagination,
                               list_dict_similar_disease_omim=list_dict_similar_disease_pagination_omim,
                               pagination=pagination,
                               pagination_omim=pagination_omim,
                               total_hit=total_hit,
                               total_hit_omim=total_hit_omim,
                               cs=str(size_orphanet),
                               cs_omim=str(size_omim),
                               active_tab=active_tab)
    else:
        return render_template('index.html')

    return


## GET: show search page with gene
@app.route('/search_disease/phenotype:/gene:<string:genes>/page:<string:page>/size:<string:size>', methods=['GET'])
def REST_API_search_genes(genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        page_orphanet = "1"
        page_omim     = "1"
        size_orphanet = "10"
        size_omim     = "10"
        active_tab    = "orphanet"
        #active_tab    = "omim"

        list_pages = page.split(",")
        if len(list_pages) == 2:
            page_orphanet = list_pages[0]
            page_omim     = list_pages[1]
        elif len(list_pages) == 1:
            page_orphanet = list_pages[0]

        list_sizes = size.split(",")
        if len(list_sizes) == 3:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
            active_tab    = list_sizes[2]
        elif len(list_sizes) == 2:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
        elif len(list_sizes) == 1:
            size_orphanet = list_sizes[0]

        # process query : phenotypes
        list_dict_phenotype, phenotypes_remove_error, phenotypes_remove_error_ja = process_input_phenotype(phenotypes)

        # process query : genes
        list_dict_gene, genes_remove_error, list_query_gene_error = process_input_gene(genes)
        num_list_query_gene_error = len(list_query_gene_error)

        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, int(page_orphanet), size_orphanet)
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, int(page_omim), size_omim)
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_error_ja, genes_remove_error, int(page_orphanet), size_orphanet)
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_error_ja, genes_remove_error, int(page_omim), size_omim)

        # PhenoTips登録用のデータを作成
        #phenotypes_phenotips = phenotypes.replace('_ja', '')
        eid = str(datetime.datetime.today())

        return render_template('search.html',
                               str_eid=eid,
                               str_phenotypes=phenotypes_remove_error,
                               str_phenotypes_remove_ja=phenotypes_remove_error_ja,
                               str_genes=genes_remove_error,
                               str_list_query_gene_error = ', '.join(list_query_gene_error),
                               num_list_query_gene_error = num_list_query_gene_error,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               #json_phenotypes_omim=json.dumps(list_dict_phenotype_omim),
                               json_genes=json.dumps(list_dict_gene),
                               #json_genes_omim=json.dumps(list_dict_gene_omim),
                               list_dict_similar_disease=list_dict_similar_disease_pagination,
                               list_dict_similar_disease_omim=list_dict_similar_disease_pagination_omim,
                               pagination=pagination,
                               pagination_omim=pagination_omim,
                               total_hit=total_hit,
                               total_hit_omim=total_hit_omim,
                               cs=size_orphanet,
                               cs_omim=str(size_omim),
                               active_tab=active_tab)
    else:
        return render_template('index.html')

    return


## GET: show search page without phenotype and gene
@app.route('/search_disease/phenotype:/gene:/page:<string:page>/size:<string:size>', methods=['GET'])
def REST_API_search_none(page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        page_orphanet = "1"
        page_omim     = "1"
        size_orphanet = "10"
        size_omim     = "10"
        active_tab    = "orphanet"
        #active_tab    = "omim"

        list_pages = page.split(",")
        if len(list_pages) == 2:
            page_orphanet = list_pages[0]
            page_omim     = list_pages[1]
        elif len(list_pages) == 1:
            page_orphanet = list_pages[0]

        list_sizes = size.split(",")
        if len(list_sizes) == 3:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
            active_tab    = list_sizes[2]
        elif len(list_sizes) == 2:
            size_orphanet = list_sizes[0]
            size_omim     = list_sizes[1]
        elif len(list_sizes) == 1:
            size_orphanet = list_sizes[0]

        # process query : phenotypes
        list_dict_phenotype, phenotypes_remove_error, phenotypes_remove_error_ja = process_input_phenotype(phenotypes)

        # process query : genes
        list_dict_gene, genes_remove_error, list_query_gene_error = process_input_gene(genes)
        num_list_query_gene_error = len(list_query_gene_error)

        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, int(page_orphanet), size_orphanet)
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, int(page_omim), size_omim)
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_error_ja, genes_remove_error, int(page_orphanet), size_orphanet)
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_error_ja, genes_remove_error, int(page_omim), size_omim)

        # PhenoTips登録用のデータを作成
        #phenotypes_phenotips = phenotypes.replace('_ja', '')
        eid = str(datetime.datetime.today())

        return render_template('search.html',
                               str_eid=eid,
                               str_phenotypes=phenotypes_remove_error,
                               str_phenotypes_remove_ja=phenotypes_remove_error_ja,
                               str_genes=genes_remove_error,
                               str_list_query_gene_error = ', '.join(list_query_gene_error),
                               num_list_query_gene_error = num_list_query_gene_error,
                               json_phenotypes=json.dumps(list_dict_phenotype),
                               #json_phenotypes_omim=json.dumps(list_dict_phenotype_omim),
                               json_genes=json.dumps(list_dict_gene),
                               #json_genes_omim=json.dumps(list_dict_gene_omim),
                               list_dict_similar_disease=list_dict_similar_disease_pagination,
                               list_dict_similar_disease_omim=list_dict_similar_disease_pagination_omim,
                               pagination=pagination,
                               pagination_omim=pagination_omim,
                               total_hit=total_hit,
                               total_hit_omim=total_hit_omim,
                               cs=size_orphanet,
                               cs_omim=str(size_omim),
                               active_tab=active_tab)
    else:
        return render_template('index.html')

    return


## POST: show search page
@app.route('/search_disease', methods=['POST'])
def search_POST():

    if request.method == 'POST':
        # changesize_selector
        #size_orphanet = request.form['changesize_selector_orphanet']
        #size_omim = request.form['changesize_selector_omim']
        #size = size_orphanet + ',' + size_omim
        #size = '10,10'
        size = '10,10,omim'

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
                phenotypes_file = str(file.stream.read())
                phenotypes_file = phenotypes_file.replace('\\n',',')
                phenotypes_file = phenotypes_file.replace('\\r',',')
                phenotypes_file = re.sub(r',+', ',', phenotypes_file)
                phenotypes_file = re.sub(r'^,+', '', phenotypes_file)
                phenotypes_file = re.sub(r',+$', '', phenotypes_file)
                phenotypes_file = re.sub(r'^b\'', '', phenotypes_file)
                phenotypes_file = re.sub(r'\'$', '', phenotypes_file)

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

        ## 症状リスト内の重複を削除
        list_phenotypes_uniq = []
        for phenotype in list_phenotypes:
            if phenotype not in list_phenotypes_uniq and phenotype.replace('_ja', '') not in list_phenotypes_uniq and phenotype + '_ja' not in list_phenotypes_uniq:
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
                OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")

                gene_file = str(file.stream.read())
                gene_file = gene_file.replace('\\n',',')
                gene_file = gene_file.replace('\\r',',')
                gene_file = re.sub(r',+', ',', gene_file)
                gene_file = re.sub(r'^,+', '', gene_file)
                gene_file = re.sub(r',+$', '', gene_file)
                gene_file = re.sub(r'^b\'', '', gene_file)
                gene_file = re.sub(r'\'$', '', gene_file)
                #gene_file = "ENT:" + gene_file.replace(',',',ENT:')

                ## Entrez Gene ID, Ensembl Gene, Gene Symbol に場合分け
                list_genes_file = gene_file.split(',')
                list_genes_file_removed = []
                for gene in list_genes_file:
                    ## pattern : Entrez Gene ID
                    pattern_Entrez = r"^\d+$"
                    ## pattern : Ensembl Gene ID
                    pattern_Ensembl = r"^ENSG\d+$"

                    if re.search(pattern_Entrez, gene):
                        list_genes_file_removed.append("ENT:" + gene)
                    elif re.search(pattern_Ensembl, gene):
                        sql_EntrezID2EnsemblID = u"select EntrezGeneID from EntrezID2EnsemblID where EnsemblGeneID=%s"
                        cursor_EntrezID2EnsemblID = OBJ_MYSQL.cursor()
                        cursor_EntrezID2EnsemblID.execute(sql_EntrezID2EnsemblID, (gene,))
                        values = cursor_EntrezID2EnsemblID.fetchall()
                        cursor_EntrezID2EnsemblID.close()
                        for value in values:
                            EntrezGeneID = value[0]
                            list_genes_file_removed.append("ENT:" + str(EntrezGeneID))
                    else:
                        sql_GeneName2ID = u"select EntrezID from GeneName2ID where GeneName=%s"
                        cursor_GeneName2ID = OBJ_MYSQL.cursor()
                        cursor_GeneName2ID.execute(sql_GeneName2ID, (gene,))
                        values = cursor_GeneName2ID.fetchall()
                        cursor_GeneName2ID.close()
                        for value in values:
                            EntrezGeneID = value[0]
                            list_genes_file_removed.append("ENT:" + str(EntrezGeneID))
                        #app.logger.debug(gene)

                    ## ENT:\d+ に沿わないエントリーは削除
                    #pattern = r"^ENT\:\d+$"
                    #match = re.search(pattern, gene)
                    #if match:
                    #    list_genes_file_removed.append(gene)
                    #else:
                    #    app.logger.debug(gene)

                ## テキストボックスの遺伝子リストとファイル内の遺伝子リストを結合
                list_genes.extend(list_genes_file_removed)

        ## 遺伝子リスト内の重複を削除
        list_genes_uniq = []
        for gene in list_genes:
            if gene not in list_genes_uniq:
                list_genes_uniq.append(gene)

        genes = ','.join(list_genes_uniq)
        genes = re.sub(r'^,+', '', genes)
        genes = re.sub(r',+$', '', genes)


        # ページ初期値
        #page_orphanet = request.form['page_orphanet']
        #page_omim = request.form['page_omim']
        #page=page_orphanet + ',' + page_omim
        page='1,1'

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
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene = show_disease_casereport_page(disease, phenotypes, genes, page, size)
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
                               str_disease_definition=disease_definition,
                               list_dict_Disease_phenotype_Orphanet=list_dict_Disease_phenotype_Orphanet,
                               list_dict_Disease_phenotype_CaseReport=list_dict_Disease_phenotype_CaseReport,
                               list_dict_DiseaseGene_gene=list_dict_DiseaseGene_gene
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
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene = show_disease_casereport_page(disease, phenotypes, genes, page, size)
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
                               str_disease_definition=disease_definition,
                               list_dict_Disease_phenotype_Orphanet=list_dict_Disease_phenotype_Orphanet,
                               list_dict_Disease_phenotype_CaseReport=list_dict_Disease_phenotype_CaseReport,
                               list_dict_DiseaseGene_gene=list_dict_DiseaseGene_gene
        )
    else:
        return render_template('index.html')

    return


## GET: show disease_casereport page with gene
@app.route('/disease_casereport/disease:<string:disease>/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_disease_casereport_genes(disease, genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene = show_disease_casereport_page(disease, phenotypes, genes, page, size)
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
                               str_disease_definition=disease_definition,
                               list_dict_Disease_phenotype_Orphanet=list_dict_Disease_phenotype_Orphanet,
                               list_dict_Disease_phenotype_CaseReport=list_dict_Disease_phenotype_CaseReport,
                               list_dict_DiseaseGene_gene=list_dict_DiseaseGene_gene
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
        list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene = show_disease_casereport_page(disease, phenotypes, genes, page, size)
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
                               str_disease_definition=disease_definition,
                               list_dict_Disease_phenotype_Orphanet=list_dict_Disease_phenotype_Orphanet,
                               list_dict_Disease_phenotype_CaseReport=list_dict_Disease_phenotype_CaseReport,
                               list_dict_DiseaseGene_gene=list_dict_DiseaseGene_gene
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
        list_phenotypes = phenotypes.split(',')

        # requestオブジェクトからクエリのgenesを取得
        genes = request.form['str_genes']
        list_genes = genes.split(',')

        page=1

        ## 症状リスト内の重複を削除
        list_phenotypes_uniq = []
        for phenotype in list_phenotypes:
            if phenotype not in list_phenotypes_uniq and phenotype.replace('_ja', '') not in list_phenotypes_uniq and phenotype + '_ja' not in list_phenotypes_uniq:
                list_phenotypes_uniq.append(phenotype)

        phenotypes = ','.join(list_phenotypes_uniq)
        phenotypes = re.sub(r'^,+', '', phenotypes)
        phenotypes = re.sub(r',+$', '', phenotypes)

        ## 遺伝子リスト内の重複を削除
        list_genes_uniq = []
        for gene in list_genes:
            if gene not in list_genes_uniq:
                list_genes_uniq.append(gene)

        genes = ','.join(list_genes_uniq)
        genes = re.sub(r'^,+', '', genes)
        genes = re.sub(r',+$', '', genes)

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
    term_disease, term_phenotype, list_dict_phenotype_context, pagination, total_hit, disease_definition, phenotype_definition = show_phenotype_context_page(disease, phenotype, page, size)
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
                           size=size,
                           disease_definition=disease_definition,
                           phenotype_definition=phenotype_definition)



#####
# download results search page
## GET: dwonload results search page with phenotype and gene
@app.route('/download_results_search_disease/phenotype:<string:phenotypes>/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_phenotypes_genes(phenotypes, genes, page, size):
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_orpha_number_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_orpha_number_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_orpha_number_symbol_synonym['symbol'])
                    prev_id_entrez = dict_orpha_number_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: download results search page with phenotype
@app.route('/download_results_search_disease/phenotype:<string:phenotypes>/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_phenotypes(phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_orpha_number_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_orpha_number_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_orpha_number_symbol_synonym['symbol'])
                    prev_id_entrez = dict_orpha_number_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: downloads results search page with gene
@app.route('/download_results_search_disease/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_genes(genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_orpha_number_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_orpha_number_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_orpha_number_symbol_synonym['symbol'])
                    prev_id_entrez = dict_orpha_number_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: download results search page without phenotype and gene
@app.route('/download_results_search_disease/phenotype:/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_none(page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_orpha_number_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_orpha_number_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_orpha_number_symbol_synonym['symbol'])
                    prev_id_entrez = dict_orpha_number_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return



#####
# download results search omim page
## GET: dwonload results search omim page with phenotype and gene
@app.route('/download_results_search_omim_disease/phenotype:<string:phenotypes>/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_omim_phenotypes_genes(phenotypes, genes, page, size):
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: download results search omim page with phenotype
@app.route('/download_results_search_omim_disease/phenotype:<string:phenotypes>/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_omim_phenotypes(phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: downloads results search omim page with gene
@app.route('/download_results_search_omim_disease/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_omim_genes(genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: download results search omim page without phenotype and gene
@app.route('/download_results_search_omim_disease/phenotype:/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_results_search_omim_none(page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes, genes, page, '1000000')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_omim_page(phenotypes_remove_ja, genes, page, '1000000')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        writer.writerow(['# Query(Phenotypes): ' + phenotypes])
        writer.writerow(['# Query(Genes): ' + genes])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])

        rank = 1
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return



#####
# download summary
## GET: dwonload summary with phenotype and gene
@app.route('/download_summary/phenotype:<string:phenotypes>/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_summary_phenotypes_genes(phenotypes, genes, page, size):
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '10')
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, page, '10')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '10')
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_ja, genes, page, '10')
        
        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        list_phenotypes_remove_ja = []
        for phenotype in phenotypes.split(","):
            list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
        phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)
        writer.writerow(['# Query (Phenotypes): ' + phenotypes_remove_ja])
        writer.writerow(['# Query (Genes): ' + genes])

        # 共有リンクを出力
        writer.writerow(['# Share Link: https://pubcasefinder.dbcls.jp/search_disease/phenotype:' + phenotypes + '/gene:' + genes + '/page:1,1/size:10,10'])

        # Orphanetの結果を出力
        writer.writerow(['# Results (Orphanet):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        # OMIMの結果を出力
        writer.writerow(['# Results (OMIM):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination_omim:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: dwonload summary with phenotype
@app.route('/download_summary/phenotype:<string:phenotypes>/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_summary_phenotypes(phenotypes, page, size):
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '10')
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, page, '10')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '10')
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_ja, genes, page, '10')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        list_phenotypes_remove_ja = []
        for phenotype in phenotypes.split(","):
            list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
        phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)
        writer.writerow(['# Query (Phenotypes): ' + phenotypes_remove_ja])
        writer.writerow(['# Query (Genes): ' + genes])

        # 共有リンクを出力
        writer.writerow(['# Share Link: https://pubcasefinder.dbcls.jp/search_disease/phenotype:' + phenotypes + '/gene:' + genes + '/page:1,1/size:10,10'])

        # Orphanetの結果を出力
        writer.writerow(['# Results (Orphanet):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            #writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'].encode('utf-8'), u','.join(list_matched_phenotype).encode('utf-8'), u','.join(list_causative_gene).encode('utf-8')])
            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        # OMIMの結果を出力
        writer.writerow(['# Results (OMIM):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination_omim:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: dwonload summary with gene
@app.route('/download_summary/phenotype:/gene:<string:genes>/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_summary_genes(genes, page, size):
    phenotypes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '10')
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, page, '10')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '10')
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_ja, genes, page, '10')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        list_phenotypes_remove_ja = []
        for phenotype in phenotypes.split(","):
            list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
        phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)
        writer.writerow(['# Query (Phenotypes): ' + phenotypes_remove_ja])
        writer.writerow(['# Query (Genes): ' + genes])

        # 共有リンクを出力
        writer.writerow(['# Share Link: https://pubcasefinder.dbcls.jp/search_disease/phenotype:' + phenotypes + '/gene:' + genes + '/page:1,1/size:10,10'])

        # Orphanetの結果を出力
        writer.writerow(['# Results (Orphanet):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        # OMIMの結果を出力
        writer.writerow(['# Results (OMIM):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination_omim:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return


## GET: dwonload summary without phenotype and gene
@app.route('/download_summary/phenotype:/gene:/page:<int:page>/size:<string:size>', methods=['GET'])
def REST_API_download_summary_none(genes, page, size):
    phenotypes = ""
    genes = ""
    if request.method == 'GET':
        phenotypes_remove_ja = phenotypes.replace('_ja', '')
        #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, page, '10')
        #list_dict_phenotype_omim,list_dict_gene_omim,list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes, genes, page, '10')
        list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes_remove_ja, genes, page, '10')
        list_dict_similar_disease_pagination_omim, pagination_omim, total_hit_omim = show_search_omim_page(phenotypes_remove_ja, genes, page, '10')

        # Python 3系 https://stackoverflow.com/questions/13120127/how-can-i-use-io-stringio-with-the-csv-module/13120279
        f = StringIO()
        # Python 2系
        #f = BytesIO()
        writer = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        ## out header
        list_phenotypes_remove_ja = []
        for phenotype in phenotypes.split(","):
            list_phenotypes_remove_ja.append(phenotype.replace('_ja', ''))
        phenotypes_remove_ja = ','.join(list_phenotypes_remove_ja)
        writer.writerow(['# Query (Phenotypes): ' + phenotypes_remove_ja])
        writer.writerow(['# Query (Genes): ' + genes])

        # 共有リンクを出力
        writer.writerow(['# Share Link: https://pubcasefinder.dbcls.jp/search_disease/phenotype:' + phenotypes + '/gene:' + genes + '/page:1,1/size:10,10'])

        # Orphanetの結果を出力
        writer.writerow(['# Results (Orphanet):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['orpha_number_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_ordo'], dict_similar_disease['onto_term_ordo'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        # OMIMの結果を出力
        writer.writerow(['# Results (OMIM):'])
        writer.writerow(['Rank','Score','Disease-Id','Disease-Name','Matched-Phenotype','Causative-Gene'])
        rank = 1;
        for dict_similar_disease in list_dict_similar_disease_pagination_omim:
            prev_id_hp = ""
            list_matched_phenotype = []
            for dict_onto_id_term_hp_disease in dict_similar_disease['onto_id_term_hp_disease']:
                if prev_id_hp != dict_onto_id_term_hp_disease['onto_id_hp_disease']:
                    list_matched_phenotype.append(dict_onto_id_term_hp_disease['onto_id_hp_disease'])
                    prev_id_hp = dict_onto_id_term_hp_disease['onto_id_hp_disease']


            prev_id_entrez = ""
            list_causative_gene = []
            for dict_omim_symbol_synonym in dict_similar_disease['omim_symbol_synonym']:
                if prev_id_entrez != dict_omim_symbol_synonym['entrez_id']:
                    list_causative_gene.append(dict_omim_symbol_synonym['symbol'])
                    prev_id_entrez = dict_omim_symbol_synonym['entrez_id']

            writer.writerow([rank, round(dict_similar_disease['match_score'],4), dict_similar_disease['onto_id_omim'], dict_similar_disease['onto_term_omim'], u','.join(list_matched_phenotype), u','.join(list_causative_gene)])
            rank += 1

        res = make_response()
        res.data = f.getvalue()
        res.headers['Content-Type'] = 'text/tsv'
        res.headers['Content-Disposition'] = 'attachment; filename=results.tsv'
        return res
    else:
        return render_template('index.html')

    return



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
        #tokeninput = request.args.get("q")
        tokeninputs = request.args.get("q").replace(u'　', u' ').split()
        sql_params = []
        in_tokeninputs = []
        for v in tokeninputs:
            sql_params.append("%"+v+"%")
            in_tokeninputs.append(mojimoji.zen_to_han(v, kana=False).lower())
        for v in tokeninputs:
            sql_params.append("%"+v+"%")

        # OntoTermテーブルからHPのtermを検索
        ## SQLのLIKEを使うときのTips
        ### http://d.hatena.ne.jp/heavenshell/20111027/1319712031
        OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
        # ICテーブルに存在する各termの頻度で、表示するtermをソート
        #sql_OntoTerm = u"select distinct a.uid, a.uid_value, b.FreqSelf from IndexFormHP as a left join IC as b on replace(a.uid, '_ja', '')=b.OntoID where a.uid_value like %s order by b.FreqSelf desc, value"
        sql_OntoTerm = u"select distinct a.uid, a.value, c.OntoSynonym, b.FreqSelf from IndexFormHP as a left join IC as b on replace(a.uid, '_ja', '')=b.OntoID LEFT JOIN OntoTermHPInformation AS c ON a.uid=c.OntoID where {0} OR (LENGTH(a.value)=CHARACTER_LENGTH(a.value) AND a.uid IN (SELECT OntoID FROM OntoTermHPSynonym WHERE OntoVersion='20170630' AND {1})) order by b.FreqSelf desc, value".format(' AND '.join(map(lambda x: "a.uid_value collate utf8_unicode_ci like %s", tokeninputs)),' AND '.join(map(lambda x: "OntoSynonym collate utf8_unicode_ci like %s", tokeninputs)))
        cursor_OntoTerm = OBJ_MYSQL.cursor()
        cursor_OntoTerm.execute(sql_OntoTerm, tuple(sql_params))
        values = cursor_OntoTerm.fetchall()
        cursor_OntoTerm.close()
        for value in values:
            dict_json = {}
            onto_id = mojimoji.zen_to_han(value[0], kana=False).lower()
            onto_id_term = mojimoji.zen_to_han(value[1], kana=False).lower()
            onto_id_synonym = []

            for in_tokeninput in in_tokeninputs:
                if type(onto_id) is str and len(onto_id) and in_tokeninput not in onto_id:
                    onto_id = None
                if type(onto_id_term) is str and len(onto_id_term) and in_tokeninput not in onto_id_term:
                    onto_id_term = None
                if onto_id is None and onto_id_term is None:
                    break

            if onto_id is None and onto_id_term is None and type(value[2]) is str and len(value[2]):
                list_synonym = value[2].split('|')
                for synonym in list_synonym:
                    temp_synonym = mojimoji.zen_to_han(synonym, kana=False).lower()
                    for in_tokeninput in in_tokeninputs:
                        if type(temp_synonym) is str and len(temp_synonym) and in_tokeninput not in temp_synonym:
                            temp_synonym = None
                            break
                    if temp_synonym is not None:
                        onto_id_synonym.append(synonym)

            dict_json['id'] = value[0]
            dict_json['name'] = value[1]
            if len(onto_id_synonym)>0:
                dict_json['synonym'] = onto_id_synonym
            else:
                dict_json['synonym'] = None
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
        OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
        # IndexFormSearchOrphanetOMIMテーブルからクエリにマッチするレコードを取得
        sql_IndexFormSearch = u"select distinct uid, uid_value from IndexFormSearchOrphanetOMIM where uid_value like %s order by uid_value"
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
        OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
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
# popup_hierarchy_hpo()
# オントロジーのバージョンをSQL内で"20170630"に固定しているので、要修正
#####
@app.route('/popup_hierarchy_hpo', methods=['GET', 'POST'])
def popup_hierarchy_hpo():

    list_json = []

    # GETメソッドの値を取得
    if request.method == 'GET':

        # requestから値を取得
        #onto_id = request.args.get("q")
        onto_id_pre = request.args.get("q")
        onto_id = onto_id_pre.replace('_ja', '')

        # MySQLへ接続
        OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")

        # JSONデータ
        dict_json = {}

        # OntoTermHPInformationテーブルから情報取得
        sql_information = u"select OntoName, OntoSynonym, OntoDefinition, OntoComment, OntoParentNum, OntoChildNum, OntoNameJa from OntoTermHPInformation where OntoVersion='20170630' and OntoID=%s"
        sql_informations_fmt = u"select OntoID, OntoName, OntoSynonym, OntoDefinition, OntoComment, OntoChildNum, OntoNameJa from OntoTermHPInformation where OntoVersion='20170630' and OntoID in (%s)"

        sql_hierarchy_parent = u"select OntoParentID from OntoTermHPHierarchy where OntoVersion='20170630' and OntoID=%s"
        sql_hierarchy_child  = u"select OntoID from OntoTermHPHierarchy where OntoVersion='20170630' and OntoParentID=%s"

        # OntoTermHPInformationテーブルからクエリにマッチするレコードを取得
        cursor_information = OBJ_MYSQL.cursor()
        cursor_information.execute(sql_information, (onto_id,))
        values_information = cursor_information.fetchall()
        cursor_information.close()

        for value_information in values_information:
            dict_self_class = {}
            onto_name       = value_information[0]
            onto_synonym    = value_information[1]
            onto_definition = value_information[2]
            onto_comment    = value_information[3]
            onto_parent_num = value_information[4]
            onto_child_num  = value_information[5]
            onto_name_ja    = value_information[6]
            dict_self_class['id']         = onto_id
            dict_self_class['name']       = onto_name
            dict_self_class['name_ja']    = onto_name_ja if onto_name_ja != "" else onto_name
            dict_self_class['synonym']    = onto_synonym
            dict_self_class['definition'] = onto_definition
            dict_self_class['comment']    = onto_comment

            list_parent_child_onto_id = []
            # OntoTermHPHierarchyから親クラスの情報取得
            list_parent_onto_id = []
            if onto_parent_num > 0:
                cursor_hierarchy_parent = OBJ_MYSQL.cursor()
                cursor_hierarchy_parent.execute(sql_hierarchy_parent, (onto_id,))
                values_hierarchy_parent = cursor_hierarchy_parent.fetchall()
                cursor_hierarchy_parent.close()

                for value_hierarchy_parent in values_hierarchy_parent:
                    parent_onto_id = value_hierarchy_parent[0]
                    list_parent_onto_id.append(parent_onto_id)
                    list_parent_child_onto_id.append(parent_onto_id)

            # OntoTermHPHierarchyから子クラスの情報取得
            list_child_onto_id = []
            if onto_child_num > 0:
                cursor_hierarchy_child = OBJ_MYSQL.cursor()
                cursor_hierarchy_child.execute(sql_hierarchy_child, (onto_id,))
                values_hierarchy_child = cursor_hierarchy_child.fetchall()
                cursor_hierarchy_child.close()

                for value_hierarchy_child in values_hierarchy_child:
                    child_onto_id = value_hierarchy_child[0]
                    list_child_onto_id.append(child_onto_id)
                    list_parent_child_onto_id.append(child_onto_id)

            # OntoTermHPInformations_fmtテーブルからクエリにマッチするレコードを取得
            in_onto_id=', '.join(map(lambda x: '%s', list_parent_child_onto_id))
            sql_informations_fmt = sql_informations_fmt % in_onto_id
            cursor_informations_fmt = OBJ_MYSQL.cursor()
            cursor_informations_fmt.execute(sql_informations_fmt, list_parent_child_onto_id)
            values_informations_fmt = cursor_informations_fmt.fetchall()
            cursor_informations_fmt.close()

            dict_all_class = {}
            for value_informations_fmt in values_informations_fmt:
                onto_id         = value_informations_fmt[0]
                onto_name       = value_informations_fmt[1]
                onto_synonym    = value_informations_fmt[2]
                onto_comment    = value_informations_fmt[3]
                onto_definition = value_informations_fmt[4]
                onto_child_num  = value_informations_fmt[5]
                onto_name_ja    = value_informations_fmt[6]
                dict_all_class[onto_id] = {}
                dict_all_class[onto_id]['id']      = onto_id
                dict_all_class[onto_id]['name']    = onto_name
                dict_all_class[onto_id]['name_ja'] = onto_name_ja if onto_name_ja != "" else onto_name
                dict_all_class[onto_id]['count']   = onto_child_num

            # JSON作成
            ## self class リスト
            list_self_class = []
            list_self_class.append(dict_self_class)

            ## parent class リスト
            list_super_class = []
            if len(list_parent_onto_id) > 0:
                for parent_onto_id in list_parent_onto_id:
                    list_super_class.append(dict_all_class[parent_onto_id])

            ## child class リスト
            list_sub_class = []
            if len(list_child_onto_id) > 0:
                for child_onto_id in list_child_onto_id:
                    list_sub_class.append(dict_all_class[child_onto_id])
            
            ## dict_json に収納
            dict_json['selfclass']  = list_self_class
            dict_json['superclass'] = list_super_class
            dict_json['subclass']   = list_sub_class

    OBJ_MYSQL.close()

    return jsonify(dict_json)


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
# GET: API for IRUD Exchange (OMIM)
#      show search page with phenotype and gene
#      /search_omim/phenotype:HPO:Id,HPO:id/gene:gene1,gene2/size_disease:N/size_casereport:N
#####
@app.route('/search_omim/phenotype:<string:phenotypes>/gene:<string:genes>/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_omim_phenotypes_genes(phenotypes, genes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD_omim(phenotypes, genes, size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange (OMIM)
#      show search page with phenotype
#      /search_omim/phenotype:HPO:Id,HPO:id/gene:/size_disease:N/size_casereport:N
#####
@app.route('/search_omim/phenotype:<string:phenotypes>/gene:/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_omim_phenotypes(phenotypes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD_omim(phenotypes, '', size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange (OMIM)
#      show search page with gene
#      /search_omim/phenotype:/gene:gene1,gene2/size_disease:N/size_casereport:N
#####
@app.route('/search_omim/phenotype:/gene:<string:genes>/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_omim_genes(genes, size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD_omim(genes, size_disease, size_casereport)

        return jsonify(dict_results)
    else:
        return render_template('index.html')


#####
# GET: API for IRUD Exchange (OMIM)
#      show search page without phenotype and gene
#      /search_omim/phenotype:/gene:/size_disease:N/size_casereport:N
#####
@app.route('/search_omim/phenotype:/gene:/size_disease:<string:size_disease>/size_casereport:<string:size_casereport>', methods=['GET'])
def REST_API_JSON_search_omim(size_disease, size_casereport):
    if request.method == 'GET':
        dict_results = make_JSON_IRUD_omim(size_disease, size_casereport)

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
    return render_template('pubcasefinder_api_en.html')


#####
# POST: API for Orphanet
#       annotate HPO term in a text
#       /annotate/hpo
#####
@app.route('/annotate/hpo', methods=['POST'])
def REST_API_ANNOTATE_HPO_POST():
    pattern_content_type_json = r'application\/json*'
    if not re.search(pattern_content_type_json , request.headers['Content-Type']):
        print(request.headers['Content-Type'])
        return jsonify(res='Error: Content-Type'), 400

    # utils/api_annotate.py
    dict_results = make_JSON_annotate(request.json, "HPO")

    return jsonify(dict_results)


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





