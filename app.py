from flask import Flask, render_template, request, redirect, url_for, flash ,session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'RAFIYA'
mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@app.route('/')
def home():
    return redirect(url_for('register'))

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user[0], user[2], user[3])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[3], password_input):
            session['user_id'] = user[0]      # ID
            session['email'] = user[2]        # Email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cur.fetchall()
    cur.close()

    return render_template('dashboard.html', tasks=tasks)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        user_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks (user_id, title, description, due_date) VALUES (%s, %s, %s, %s)",
                    (user_id, title, description, due_date))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard'))

    return render_template('add_task.html')

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE tasks SET is_completed = TRUE WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=10000)
    # app.run(debug=True)
