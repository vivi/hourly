import sqlite3


from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing


#config
DATABASE = '/tmp/picy.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

#create app
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# *** FOOD ENTRIES ***
@app.route('/')
def show_entries():
    cur = g.db.execute('select title, description from food order by id desc')
    entries = [dict(title=row[0], description = row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    #check for login
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into food (title, description) values (?, ?)',
        [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New food entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login_register', methods=['GET', 'POST'])
def login():
    error1 = None
    if request.method == 'POST':
        cur = g.db.execute('select username, password from users')
        usernames_passwords_dict = {row[0]: row[1] for row in cur.fetchall()}
        attemptedusername = request.form['username']
        attemptedpassword = request.form['password']

        if not attemptedusername:
            error1 = "Please enter username."
        elif not attemptedpassword:
            error1 = "Please enter password."
        else:
            if (attemptedusername not in usernames_passwords_dict):
                error1 = 'Invalid username'
            elif request.form['password'] != usernames_passwords_dict[attemptedusername]:
                error1 = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('show_entries'))
    return render_template('login_register.html', error1=error1, new=True)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash ('You were logged out')
    return redirect(url_for('show_entries'))

# *** USERS ***

def check_form(f):
    error = []
    good = True
    if f['username'] == "":
        error.append("You need to enter a username.")
        good = False
    if f['password'] == "":
        error.append("You need to enter a password.")
        good = False
    if f['favfood'] == "":
        error.append("You need to enter a favorite food.")
        good = False
    if f['firstname'] == "":
        error.append("You need to enter a first name.")
        good = False
    if f['lastname'] == "":
        error.append("You need to enter a last name.")
        good = False
    return {'error': error, 'good': good}

@app.route('/register', methods=['POST'])
def add_user():
    good_form = check_form(request.form)
    if good_form['good']: #if true that everything is good
            g.db.execute('insert into users (username, password, favfood, firstname, lastname) values (?, ?, ?, ?, ?)',
        [request.form['username'], request.form['password'], request.form['favfood'], request.form['firstname'], request.form['lastname']])
            g.db.commit()
            return render_template('login_register.html', info=request.form, good=good_form['good'], new=False)
    else:
        return render_template('login_register.html', error=good_form['error'], good=False, new=False)


if __name__=='__main__':
    app.debug = True
    app.run()





















