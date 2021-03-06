from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User
from src.foodbank import parse_from_json
import subprocess
from src.Database import Database
import json


@app.route('/')
@app.route('/index')
# @login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.submit.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # new food supplier
        user = User(username=form.username.data, email=form.email.data, food_supplier=form.food_supplier.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/user.<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {"author": user, "body": "Test post #1"},
        {"author": user, "body": "Test post #2"}
    ]
    return render_template("user.html", user=user, posts=posts)



@app.route("/truck_path")
def truck_path():
    subprocess.call("./update_cache.sh")
    data = parse_from_json()
    return render_template("trucker.html", data = data)

@app.route("/send", methods=['POST'])
def donation():
    interface = Database()
    interface.connectToDatabase()
    food_data = json.loads(interface.getRestaurantFood("Cafe Mexicali"))

    name = request.form['foodname']
    amount = request.form['amount']
    
    if interface.inFoodAmountTable(name) == False:
        interface.addDonation(name, "Harvest of Hope", amount, "12/12/2019")
        interface.addFoodAmount(name, "Harvest of Hope", amount)
    else:
        interface.updateAmount(name, amount)
    return render_template("donation.html", data=food_data)

@app.route("/donation")
def send():
    interface = Database()
    interface.connectToDatabase()
    food_data = json.loads(interface.getRestaurantFood("Cafe Mexicali"))
    return render_template("donation.html", data=food_data)
