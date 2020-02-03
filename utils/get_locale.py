# -*- coding: utf-8 -*-

import os
import re
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
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

