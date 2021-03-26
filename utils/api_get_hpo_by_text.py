# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re
import json
import MySQLdb

import Levenshtein

app = Flask(__name__)


#####
# DB設定
app.config.from_pyfile('../config.cfg')
db_sock = app.config['DBSOCK']
db_name = app.config['DBNAME']
db_user = app.config['DBUSER']
db_pw   = app.config['DBPW']


#####
# POST: API for PhenoTouch
# /get_hpo_by_text
# カンマ区切りのHPO IDを返す
# マッチするものがない場合はnoneを返す
#####
def search_hpo_by_text(text):

    dict_match = {}
    OBJ_MYSQL = MySQLdb.connect(unix_socket=db_sock, host="localhost", db=db_name, user=db_user, passwd=db_pw, charset="utf8")
    sql_IndexFormHP = u"select uid, value from IndexFormHP;"
    cursor_IndexFormHP = OBJ_MYSQL.cursor()
    cursor_IndexFormHP.execute(sql_IndexFormHP)
    values = cursor_IndexFormHP.fetchall()
    cursor_IndexFormHP.close()
    for value in values:
        uid   = value[0]
        value = value[1]

        # ジャロ・ウィンクラー距離を計算
        jaro_dist = Levenshtein.jaro_winkler(text, value)

        if jaro_dist in dict_match:
            (dict_match[jaro_dist]).append("\t".join([uid,value]))
        else:
            dict_match[jaro_dist] = []
            (dict_match[jaro_dist]).append("\t".join([uid,value]))

    str_list_hpo = ""
    counter = 0
    for key, list_uid_value in sorted(dict_match.items(), reverse=True):
        #print(key)
        for uid_value in sorted(list_uid_value):
            str_list_hpo = str_list_hpo + "," + (uid_value.split())[0]
            counter += 1
            if counter == 5:
                break
        if counter == 5:
            break

    str_list_hpo = re.sub('^,', '', str_list_hpo)
    return str_list_hpo


def main():
    print(search_hpo_by_text("貧血"))

if __name__ == '__main__':
    main()
