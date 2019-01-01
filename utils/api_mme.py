# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re
import json
import MySQLdb

# Search core
from utils.show_search_page import show_search_page
from utils.show_disease_casereport_page import show_disease_casereport_page


app = Flask(__name__)

#####
# DB設定
app.config.from_pyfile('../config.cfg')
db_sock = app.config['DBSOCK']
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


#####
# POST: API for MME to match rare diseases based on phenotypic similarity
# /mme/search
# a specification of JSON for MME
# {
#   "patient" : {
#     "features" : [
#       {
#         "id" : <HPO code>
#       },
#       …
#     ],
#     "genomicFeatures" : [
#       {
#         "gene" : {
#           "id" : <gene symbol>
#         }
#       },
#       …
#     ]
#   }
# }
#####
def make_JSON_MME(dict_json):

    list_phenotypes = []
    list_genes = []

    # translate input gene id to entrez gene id
    dict_GeneName2EntrezID  = {}
    dict_EnsemblID2EntrezID = {}
    dict_EntrezID           = {}

    # translate entrez gene id to ensembl gene id
    dict_EntrezID2EnsemblID = {}

    # retrieve all records of GeneName2ID
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    sql_GeneName2ID = u"select GeneName, EntrezID from GeneName2ID;"
    cursor_GeneName2ID = OBJ_MYSQL.cursor()
    cursor_GeneName2ID.execute(sql_GeneName2ID)
    values = cursor_GeneName2ID.fetchall()
    cursor_GeneName2ID.close()
    for value in values:
        gene_name      = value[0]
        entrez_gene_id = value[1]
        dict_GeneName2EntrezID[value[0]] = value[1]
        dict_EntrezID[entrez_gene_id] = 1

    # retrieve all records of EntrezID2EnsemblID
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    sql_EntrezID2EnsemblID = u"select EntrezGeneID, EnsemblGeneID from EntrezID2EnsemblID;"
    cursor_EntrezID2EnsemblID = OBJ_MYSQL.cursor()
    cursor_EntrezID2EnsemblID.execute(sql_EntrezID2EnsemblID)
    values = cursor_EntrezID2EnsemblID.fetchall()
    cursor_EntrezID2EnsemblID.close()
    for value in values:
        entrez_gene_id  = value[0]
        ensembl_gene_id = value[1]
        dict_EnsemblID2EntrezID[ensembl_gene_id] = entrez_gene_id
        dict_EntrezID2EnsemblID[entrez_gene_id]  = ensembl_gene_id
        dict_EntrezID[entrez_gene_id]            = 1

    # parse json
    dict_patient = {}
    if 'patient' in dict_json:
        dict_patient = dict_json['patient']

    # features
    list_features = []
    if 'features' in dict_patient:
        list_features = dict_patient['features']
        for feature in list_features:
            id_hpo   = feature['id']
            list_phenotypes.append(id_hpo)

    # genomicFeatures
    list_genomicFeatures = []
    if 'genomicFeatures' in dict_patient:
        list_genomicFeatures = dict_patient['genomicFeatures']
        for genomicFeature in list_genomicFeatures:
            gene           = genomicFeature['gene']
            gene_id        = gene['id']
            entrez_gene_id = ''
        
            # correspond to <gene symbol>|<ensembl gene ID>|<entrez gene ID>
            ## <gene symbol>
            if gene_id in dict_GeneName2EntrezID:
                entrez_gene_id = dict_GeneName2EntrezID[gene_id]
                list_genes.append("ENT:" + str(entrez_gene_id))
            ## <ensembl gene ID>
            elif gene_id in dict_EnsemblID2EntrezID:
                entrez_gene_id = dict_EnsemblID2EntrezID[gene_id]
                list_genes.append("ENT:" + str(entrez_gene_id))
            ## <entrez gene ID>
            elif gene_id in dict_EntrezID:
                entrez_gene_id = gene_id
                list_genes.append("ENT:" + str(entrez_gene_id))

    # make string
    phenotypes = ",".join(list_phenotypes)
    genes      = ",".join(list_genes)

    # search diseases and case reports
    #dict_results = make_search_results_MME(phenotypes, genes, '100000', '0', dict_EntrezID2EnsemblID)
    ## the request from PhenomeCentral to return top 100
    ## 2018.02.07
    dict_results = make_search_results_MME(phenotypes, genes, '100', '0', dict_EntrezID2EnsemblID)

    return dict_results


#####
# make list of search results of rare disease for MME API
#####
def make_search_results_MME(phenotypes, genes, size_disease, size_casereport, dict_EntrezID2EnsemblID):
    dict_results = {}
    flg_casereport = 0

    # caluculate phenotypic similarity between a patient and rare diseases.
    #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, '1', size_disease)
    list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, '1', size_disease)

    list_results = []
    for dict_similar_disease_pagination in list_dict_similar_disease_pagination:
        rank                   = dict_similar_disease_pagination['rank']
        score                  = dict_similar_disease_pagination['match_score']
        disease_id             = dict_similar_disease_pagination['onto_id_ordo']
        disease_label          = dict_similar_disease_pagination['onto_term_ordo']
        list_matchedPhenotypes = dict_similar_disease_pagination['onto_id_term_hp_disease']
        list_causativeGenes    = dict_similar_disease_pagination['orpha_number_symbol_synonym']

        dict_result = {}

        dict_score = {}
        dict_score['patient'] = score
        dict_result['score'] = dict_score

        dict_patient = {}
        dict_patient['id'] = disease_id
        dict_patient['label'] = disease_label

        dict_contact = {}
        dict_contact['name'] = 'PubCaseFinder'
        # URL for Disease Page
        #dict_contact['href'] = "https://pubcasefinder.dbcls.jp/disease_casereport/disease:" + disease_id  + "/phenotype:" + phenotypes + "/gene:" + genes + "/page:1/size:20"
        # URL for CaseReport Page
        dict_contact['href'] = "https://pubcasefinder.dbcls.jp/disease_casereport/disease:" + disease_id  + "/phenotype:" + phenotypes + "/gene:/page:1/size:20"
        dict_patient['contact'] = dict_contact

        # disorders
        dict_patient['disorders'] = []
        dict_disorders = {}
        dict_disorders['id'] = disease_id.replace('ORDO', 'Orphanet')
        dict_patient['disorders'].append(dict_disorders)

        # features
        dict_patient['features'] = []
        dict_exist_hp_id = {}
        for matchedPhenotypes in list_matchedPhenotypes:
            if 'onto_id_hp_disease' in matchedPhenotypes and not matchedPhenotypes['onto_id_hp_disease'] in dict_exist_hp_id:
                dict_matchedPhenotypes = {}
                dict_matchedPhenotypes['id'] = matchedPhenotypes['onto_id_hp_disease']
                #dict_matchedPhenotypes['label'] = matchedPhenotypes['onto_term_hp_disease']
                dict_patient['features'].append(dict_matchedPhenotypes)
                dict_exist_hp_id[matchedPhenotypes['onto_id_hp_disease']] = 1

        # genomicFeatures
        dict_patient['genomicFeatures'] = []
        for causativeGenes in list_causativeGenes:
            if 'entrez_id' in causativeGenes:
                entrez_gene_id = causativeGenes['entrez_id']
                entrez_gene_id = entrez_gene_id.replace('ENT:', '')
                if entrez_gene_id in dict_EntrezID2EnsemblID:
                    dict_causativeGenes = {}
                    dict_gene = {}
                    # Entrez Gene ID を Ensembl Gene ID に変換して挿入（1 : 1 ?）
                    dict_gene['id'] = dict_EntrezID2EnsemblID[entrez_gene_id]
                    dict_gene['label'] = causativeGenes['symbol'] if 'symbol' in causativeGenes else ''
                    dict_causativeGenes['gene'] = dict_gene
                    dict_patient['genomicFeatures'].append(dict_causativeGenes)

        dict_result['patient'] = dict_patient

        list_results.append(dict_result)

    dict_results['results'] = list_results 

    return dict_results


#####
# make list of search results of rare disease for IRUD API
#####
def make_JSON_IRUD(phenotypes, genes, size_disease, size_casereport):
    dict_results = {}
    flg_casereport = 0

    # caluculate phenotypic similarity between a patient and rare diseases.
    #list_dict_phenotype,list_dict_gene,list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, '1', size_disease)
    list_dict_similar_disease_pagination, pagination, total_hit = show_search_page(phenotypes, genes, '1', size_disease)

    list_results = []
    for dict_similar_disease_pagination in list_dict_similar_disease_pagination:
        rank                   = dict_similar_disease_pagination['rank']
        score                  = dict_similar_disease_pagination['match_score']
        disease_id             = dict_similar_disease_pagination['onto_id_ordo']
        disease_label          = dict_similar_disease_pagination['onto_term_ordo']
        list_matchedPhenotypes = dict_similar_disease_pagination['onto_id_term_hp_disease']
        list_causativeGenes    = dict_similar_disease_pagination['orpha_number_symbol_synonym']

        dict_result = {}
        dict_result['rank'] = rank
        dict_result['score'] = score

        dict_disease = {}
        dict_disease['id'] = disease_id
        dict_disease['label'] = disease_label

        list_casereports = []
        # search case reports for top hit
        # not assignig genes
        if rank == 1 and flg_casereport == 0:
            dict_result['flgCaseReports'] = 1
            # flag for record top hit
            flg_casereport = 1
            # caluculate phenotypic similarity between a patient and case reports.
            list_dict_phenotype,list_dict_gene,list_dict_similar_casereport_pagination, dict_onto_id_term_ordo, pagination, total_hit, disease_definition, list_dict_Disease_phenotype_Orphanet, list_dict_Disease_phenotype_CaseReport, list_dict_DiseaseGene_gene = show_disease_casereport_page(disease_id, phenotypes, '', '1', size_casereport)
            for dict_similar_casereport_pagination in list_dict_similar_casereport_pagination:
                rank_cs                   = dict_similar_casereport_pagination['rank']
                pmid_cs                   = dict_similar_casereport_pagination['pmid']
                score_cs                  = dict_similar_casereport_pagination['match_score']
                title_cs                  = dict_similar_casereport_pagination['title']
                authors_cs                = dict_similar_casereport_pagination['authors']
                reference_cs              = dict_similar_casereport_pagination['so']
                list_matchedPhenotypes_cs = dict_similar_casereport_pagination['list_dict_casereport_bestmatch_onto_id_term_hp']
                list_genes_cs             = dict_similar_casereport_pagination['list_dict_entrezid_symbol_synonym']
                list_mutations_cs         = dict_similar_casereport_pagination['list_dict_id_component_mention']

                dict_casereport = {}
                dict_casereport['rank'] = rank_cs
                dict_casereport['pmid'] = pmid_cs
                dict_casereport['score'] = score_cs
                dict_casereport['title'] = title_cs
                dict_casereport['authors'] = authors_cs
                dict_casereport['reference'] = reference_cs

                dict_casereport['matchedPhenotypes'] = []
                dict_exist_hp_id = {}
                for matchedPhenotype in list_matchedPhenotypes_cs:
                    if 'onto_id_hp' in matchedPhenotype and not matchedPhenotype['onto_id_hp'] in dict_exist_hp_id:
                        dict_matchedPhenotype = {}
                        dict_matchedPhenotype['id'] = matchedPhenotype['onto_id_hp']
                        dict_matchedPhenotype['label'] = matchedPhenotype['onto_term_hp']
                        dict_casereport['matchedPhenotypes'].append(dict_matchedPhenotype)
                        dict_exist_hp_id[matchedPhenotype['onto_id_hp']] = 1

                dict_casereport['genes'] = []
                for gene in list_genes_cs:
                    dict_gene = {}
                    dict_gene['id'] = gene['entrezid'] if 'entrezid' in gene else ''
                    dict_gene['label'] = gene['symbol'] if 'symbol' in gene else ''
                    dict_casereport['genes'].append(dict_gene)
                dict_casereport['mutations'] = []

                for mutation in list_mutations_cs:
                    mutation = mutation['component'] if 'component' in mutation else ''
                    dict_casereport['mutations'].append(mutation)

                list_casereports.append(dict_casereport)
        else:
            dict_result['flgCaseReports'] = 0

        # setting Case Reports
        dict_disease['caseReports'] = list_casereports

        dict_disease['matchedPhenotypes'] = []
        dict_exist_hp_id = {}
        for matchedPhenotypes in list_matchedPhenotypes:
            if 'onto_id_hp_disease' in matchedPhenotypes and not matchedPhenotypes['onto_id_hp_disease'] in dict_exist_hp_id:
                dict_matchedPhenotypes = {}
                dict_matchedPhenotypes['id'] = matchedPhenotypes['onto_id_hp_disease']
                dict_matchedPhenotypes['label'] = matchedPhenotypes['onto_term_hp_disease']
                dict_disease['matchedPhenotypes'].append(dict_matchedPhenotypes)
                dict_exist_hp_id[matchedPhenotypes['onto_id_hp_disease']] = 1

        dict_disease['causativeGenes'] = []
        for causativeGenes in list_causativeGenes:
            dict_causativeGenes = {}
            dict_causativeGenes['id'] = causativeGenes['entrez_id'] if 'entrez_id' in causativeGenes else ''
            dict_causativeGenes['label'] = causativeGenes['symbol'] if 'symbol' in causativeGenes else ''
            dict_disease['causativeGenes'].append(dict_causativeGenes)

        dict_result['disease'] = dict_disease

        list_results.append(dict_result)

    dict_results['results'] = list_results 

    return dict_results



