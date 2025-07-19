from flask import Flask, request, render_template, redirect, url_for, Response
from functools import wraps
import os

DAGS_FOLDER = "/home/admin/airflow/dags"  # Change this if your DAGs folder is different


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = DAGS_FOLDER

# --- BASIC AUTH ---
USERNAME = "admin"
PASSWORD = "IAMSP"  # Change this to a secure password!

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Access Denied.\n'
        'Please login with proper credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- ROUTES ---

@app.route('/')
@requires_auth
def index():
    files = os.listdir(DAGS_FOLDER)
    py_files = [f for f in files if f.endswith(".py")]
    return render_template('index.html', files=py_files)

@app.route('/upload', methods=['POST'])
@requires_auth
def upload():
    file = request.files['file']
    if file and file.filename.endswith(".py"):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
    return redirect(url_for('index'))

@app.route('/edit/<filename>', methods=['GET', 'POST'])
@requires_auth
def edit(filename):
    filepath = os.path.join(DAGS_FOLDER, filename)
    if request.method == 'POST':
        content = request.form['code']
        with open(filepath, 'w') as f:
            f.write(content)
        return redirect(url_for('index'))
    else:
        with open(filepath, 'r') as f:
            content = f.read()
        return f'''
        <h2>Editing: {filename}</h2>
        <form method="POST">
            <textarea name="code" rows="25" cols="100">{content}</textarea><br>
            <input type="submit" value="Save">
        </form>
        '''

@app.route('/delete/<filename>', methods=['POST'])
@requires_auth
def delete(filename):
    filepath = os.path.join(DAGS_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
