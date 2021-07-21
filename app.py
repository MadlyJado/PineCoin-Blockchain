#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from sqlhelpers import *
from forms import *
from functools import wraps

import time

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '53422310Jado#'
app.config['MYSQL_DB'] = 'pinecoin'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login!", 'danger')
            return redirect(url_for('login'))
    return wrap

def log_in_user(username):
    users = Table("users", "name", "email", "username", "password")
    user = users.getone('username', username)

    session['logged_in'] = True
    session['username'] = username
    session['name'] = user.get('name')
    session['email'] = user.get('email')

@app.route("/register", methods= ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    users = Table("users", "name", "email", "username", "password")

    if(request.method == 'POST' and form.validate()):
        username = form.username.data
        email = form.email.data
        name = form.name.data

        if isnewuser(username=username): #Check if new user
            password = sha256_crypt.encrypt(form.password.data)
            users.insert(name,email,username,password)
            log_in_user(username)
            return redirect(url_for('dashboard'))
        else:
            flash('User Already Exists', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

@app.route("/dashboard")
@is_logged_in
def dashboard():
    blockchain = get_blockchain().chain
    ct = time.strftime("%I:%M %p")
    balance = get_balance(session.get('username'))
    return render_template("dashboard.html", session=session, balance=balance,ct=ct, blockchain=blockchain, page='dashboard')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if(request.method == 'POST'):
        username = request.form['username']
        candidate = request.form['password']
        

        users = Table("users", "name", "email", "username", "password")
        user = users.getone("username", username)
        actpass = user.get('password')

        if actpass is None:
            flash("Username is not found!", 'danger')
            return redirect(url_for('login'))
        else:
            if sha256_crypt.verify(candidate, actpass):
                log_in_user(username=username)
                flash("You are now logged in!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid Password!", 'danger')
                return redirect(url_for('login'))
    
    return render_template("login.html")

@app.route("/transaction", methods = ['GET', 'POST'])
@is_logged_in
def transaction():
    form = SendMoneyForm(request.form)
    balance = get_balance(session.get('username'))

    if request.method == 'POST':
        try:
            send_money(session.get('username'), form.username.data, form.amount.data)
            flash("Money Sent!", 'success')
        except Exception as e:
            flash(str(e), 'danger')
        
        return redirect(url_for('transaction'))

    return render_template("transaction.html", balance=balance, form=form, page='transaction')

@app.route("/buy", methods = ['GET', 'POST'])
@is_logged_in
def buy():
    form = BuyForm(request.form)
    balance = get_balance(session.get('username'))

    if request.method == 'POST':
        try:
            send_money("BANK", session.get('username'), form.amount.data, page='buy')
            flash("Purchase Successful!", 'success')
        except Exception as e:
            flash(str(e), 'danger')
        
        return redirect(url_for('dashboard'))
    
    return render_template("buy.html", balance=balance, form=form)


@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('Logout Success!' 'success')
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.secret_key = '5342Jado#'
    app.run(debug= True)