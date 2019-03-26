from flask import Flask, render_template, session, flash, redirect, url_for, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'ajborbz'
app.config['MYSQL_PASSWORD'] = 'Strongpassword@123'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize MYSQL
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1,max=50)])
    username = StringField('Username', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=4, max=50)])
    password = PasswordField('Password', [
         validators.DataRequired(),
         validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email =form.email.data
        username=form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name,username,email,password) VALUES (%s,%s,%s,%s)",
        (name,username,email,password))

        # commit to db
        mysql.connection.commit()

        cur.close()
        flash('You are now registered and can now login','success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

#Article single
@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id=id)

# articles
@app.route('/articles')
def articles():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    #Close connection
    cur.close()


#User loggin
@app.route('/login', methods =['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')

                return redirect(url_for('dashboard'))
            else:
                error = 'Username not valid'
                return render_template('login.html', error=error)
            #Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap

#  Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    #Close connection
    cur.close()

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1,max=100)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Articles
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body,session['username']))

        # commit
        mysql.connection.commit()

        #Close
        cur.close()
        flash('Article created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
