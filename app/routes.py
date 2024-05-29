from datetime import datetime, timezone

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit

from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from app.models import User

import sqlalchemy as sa

@app.route('/')
@app.route('/index')
@login_required
def index():
    title = 'Home'
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in San Fransico, California!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]

    return render_template('index.html', title=title, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Sign In'
    # Check if User is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    # Validate user input on login form
    if form.validate_on_submit():
        # Compare user username input to database username values
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        # Check username does not exist or check if password does not match
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password.")
            return redirect(url_for('login'))

        # Check if remember_me value was checked and then set to user login
        login_user(user, remember=form.remember_me.data)

        # If login required to access page, redirect to login but save
        # page that the user redirected from so that they can be redirected
        # back once they login
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=title, form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/Register', methods=['GET', 'POST'])
def register():
    title = 'Register'
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration completed!')
        return redirect(url_for('login'))
    return render_template('register.html', title=title, form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': "Test post #1"},
        {'author': user, 'body': "Test post #2"}
    ]
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    title = 'Edit Profile'
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=title, form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))

        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))

        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))

        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))

        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))