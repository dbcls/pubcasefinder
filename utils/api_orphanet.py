# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re
import json
import MySQLdb
import subprocess
import tempfile
import logging


app = Flask(__name__)



#####
# POST: API for MME to match rare diseases based on phenotypic similarity
# /mme/search
# a specification of JSON for MME
# {
#   "text" : <text>
# }
#####
def make_JSON_annotate(dict_json, str_onto):

    # parse json
    str_text = ""
    if 'text' in dict_json:
        str_text = dict_json['text']

    dict_results = annotate_hpo(str_text)

    return dict_results


#####
# annotate text with HPO
#####
def annotate_hpo(str_text):
    dict_results = {}
    filename = ""

    with tempfile.NamedTemporaryFile(dir="/opt/services/case/tmp/annotate/hpo/input") as f:
        filename = f.name
        #app.logger.error(filename)
        f.write(str_text)
        f.seek(0)

        try:
            cmd1 = "cp " + filename + " " + filename + ".txt"
            cmd2 = "sh /opt/services/case/app/pubcase/static/sh/annotate_hpo.sh"
            res1 = subprocess.check_call(cmd1.split())
            res2 = subprocess.check_call(cmd2.split())
        except:
            #app.logger.error("fail: ConceptMapper")
            return dict_results



    filename_txt = filename + ".txt"
    filename_a1 = filename + ".a1"
    filename_a1 = filename_a1.replace('input', 'output')
    file_annotate = open(filename_a1, "r")

    # 一行ずつ読み込んでは表示する
    list_results = []
    start = ""
    end = ""
    term = ""
        
    for line in file_annotate:
        line = line.strip()
        #app.logger.error(line)

        pattern_T = r"^T"
        pattern_N = r"^N"
        matchOB_T = re.match(pattern_T , line)
        matchOB_N = re.match(pattern_N , line)

        if matchOB_T:
            list_line_T = line.split("\t")
            start_end = list_line_T[1]
            list_start_end = start_end.split(" ")
            start = list_start_end[1]
            end = list_start_end[2]
            term = list_line_T[2]
            #app.logger.error(start)

        if matchOB_N:
            list_line_N = line.split("\t")
            #app.logger.error(list_line_N[1])
            list_list_line_N1 = list_line_N[1].split(" ")
            dict_each_annotation = {}
            hpo_id = list_list_line_N1[2].replace("http://purl.obolibrary.org/obo/", "")
            hpo_id = hpo_id.replace("_", ":")
            dict_each_annotation['HPO ID'] = hpo_id
            dict_each_annotation['TERM']   = term
            dict_each_annotation['START']  = start
            dict_each_annotation['END']    = end
            list_results.append(dict_each_annotation)
                    
    # ファイルをクローズする
    file_annotate.close()

    os.remove(filename_txt)
    os.remove(filename_a1)

    dict_results['results'] = list_results 

    return dict_results



