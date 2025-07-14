from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
import requests
import os
from flask_wtf.csrf import CSRFProtect
from urllib.parse import urlparse
from dotenv import load_dotenv
from functools import wraps
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize Flask-WTF with enforce SSL disabled for development
csrf = CSRFProtect()
csrf.init_app(app)

# Configure CSRF and Session with more secure defaults
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = int(os.getenv('WTF_CSRF_TIME_LIMIT', 3600))
app.config['WTF_CSRF_SSL_STRICT'] = False  # Set to True in production with HTTPS
app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['CSRF_COOKIE_SECURE'] = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
app.config['CSRF_COOKIE_HTTPONLY'] = os.getenv('CSRF_COOKIE_HTTPONLY', 'True').lower() == 'true'

# Configure trusted origins for CSRF
csrf_trusted_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
csrf_trusted_origins = [origin.strip() for origin in csrf_trusted_origins if origin.strip()]
if csrf_trusted_origins:
    app.config['WTF_CSRF_TRUSTED_ORIGINS'] = csrf_trusted_origins

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def get_db():
    db = sqlite3.connect(os.getenv('DATABASE_PATH', 'database.db'))
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    # Create users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create api_keys table
    db.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            medium_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    db.commit()

# Initialize database on startup
with app.app_context():
    init_db()

# User model
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        return None
    return User(user['id'], user['username'], user['password'])

def is_valid_host(host):
    allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if ':' in host:
        host = host.split(':')[0]
    return host in allowed_hosts

@app.before_request
def validate_host():
    if request.method == 'OPTIONS':
        return

    host = request.headers.get('Host', '')
    if not is_valid_host(host):
        return jsonify({'error': 'Invalid host'}), 400

def has_users():
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
    return result['count'] > 0

@app.route('/')
def index():
    if not has_users():
        return redirect(url_for('register'))
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    api_keys = db.execute(
        'SELECT * FROM api_keys WHERE user_id = ?',
        (current_user.id,)
    ).fetchall()
    
    # Get user's name from database
    user = db.execute(
        'SELECT username FROM users WHERE id = ?',
        (current_user.id,)
    ).fetchone()
    
    return render_template('dashboard.html', 
                         api_keys=api_keys,
                         admin_username=user['username'] if user else 'User')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect to register if no users exist
    if not has_users():
        return redirect(url_for('register'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Please fill in all fields')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['password'])
            login_user(user_obj)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If users exist and current user is not authenticated, redirect to login
    if has_users() and not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()

        if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            return redirect(url_for('register'))

        db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, generate_password_hash(password)))
        db.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/generate-api', methods=['POST'])
@login_required
def generate_api():
    medium_username = request.form.get('medium_username', '').strip()
    if not medium_username:
        return jsonify({'error': 'Medium username is required'}), 400

    api_key = secrets.token_urlsafe(32)
    db = get_db()
    
    try:
        db.execute('INSERT INTO api_keys (key, user_id, medium_username) VALUES (?, ?, ?)',
                  (api_key, current_user.id, medium_username))
        db.commit()
        return redirect(url_for('dashboard', success_message='api_generated'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate-username', methods=['POST'])
@login_required
def validate_username():
    medium_username = request.form.get('medium_username', '').strip()
    if not medium_username:
        return jsonify({'valid': False, 'error': 'Username is required'}), 400
        
    try:
        url = f'https://medium.com/@{medium_username}/feed'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return jsonify({'valid': False, 'error': 'Medium username not found'}), 404
        elif response.status_code != 200:
            print(f"Error fetching Medium feed: {response.status_code}")
            return jsonify({'valid': False, 'error': 'Failed to validate username'}), 400
            
        return jsonify({'valid': True}), 200
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@app.route('/delete-api/<api_key>', methods=['POST'])
@login_required
def delete_api(api_key):
    try:
        db = get_db()
        db.execute('DELETE FROM api_keys WHERE key = ? AND user_id = ?', (api_key, current_user.id))
        db.commit()
        db.close()
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.close()
        return redirect(url_for('dashboard'))

@app.route('/api/medium/<username>')
def get_medium_feed(username):
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key is required'}), 401

    db = get_db()
    result = db.execute('SELECT medium_username FROM api_keys WHERE key = ?', (api_key,)).fetchone()
    
    if not result:
        return jsonify({'error': 'Invalid API key'}), 401

    try:
        url = f'https://medium.com/@{username}/feed'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return jsonify({'error': 'Medium username not found'}), 404
        elif response.status_code != 200:
            return jsonify({'error': 'Failed to fetch Medium feed'}), response.status_code

        # Parse the XML feed and return JSON
        return jsonify(parse_medium_feed(response.text))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_medium_feed(xml_content):
    import xml.etree.ElementTree as ET
    from datetime import datetime
    import html
    import re

    try:
        root = ET.fromstring(xml_content)
        channel = root.find('channel')
        items = channel.findall('item')
        
        articles = []
        for item in items:
            content_html = html.unescape(item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text)
            
            # Extract images and filter out tracking pixels
            all_images = re.findall(r'<img[^>]+src="([^">]+)"', content_html)
            images = [img for img in all_images if not img.startswith('https://medium.com/_/stat')]

            # Remove image tags from content, including the figure wrapper
            clean_content_html = re.sub(r'<figure>.*?</figure>', '', content_html, flags=re.DOTALL)
            # Also remove the tracking pixel
            clean_content_html = re.sub(r'<img src="https://medium.com/_/stat.*?"[^>]*>', '', clean_content_html).strip()

            # Create a plain text version by removing all HTML tags
            plain_text_content = re.sub(r'<[^>]+>', '', clean_content_html).strip()

            # Parse publication date
            pub_date = item.find('pubDate').text
            pub_timestamp = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').timestamp() * 1000
            
            # Get categories
            categories = [cat.text for cat in item.findall('category')]
            
            # Create article object
            article = {
                'title': html.unescape(item.find('title').text),
                'link': item.find('link').text,
                'author': html.unescape(item.find('{http://purl.org/dc/elements/1.1/}creator').text),
                'published': int(pub_timestamp),
                'created': int(pub_timestamp),
                'content': plain_text_content,
                'content_encoded': clean_content_html,
                'category': categories[0] if len(categories) == 1 else categories,
                'enclosures': [],
                'media': { "images": images }
            }
            articles.append(article)
        
        return articles
    except ET.ParseError as e:
        raise Exception(f"Failed to parse XML feed: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing feed: {str(e)}")

@app.route('/test-api/<username>')
def test_api(username):
    try:
        # Get the user's API key
        db = get_db()
        api_key = db.execute(
            'SELECT key FROM api_keys WHERE medium_username = ?', 
            (username,)
        ).fetchone()

        if not api_key:
            return jsonify({'error': 'API key not found'}), 404

        # Test the Medium RSS feed
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(f'https://medium.com/feed/@{username}', headers=headers)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch Medium feed'}), response.status_code

        # Parse feed and return formatted JSON
        posts = parse_medium_feed(response.text)
        return jsonify(posts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-api/<username>')
@login_required
def test_api_endpoint(username):
    try:
        url = f'https://medium.com/@{username}/feed'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return jsonify({'error': 'Medium username not found'}), 404
        elif response.status_code != 200:
            return jsonify({'error': 'Failed to fetch Medium feed'}), response.status_code
            
        return response.text, 200, {'Content-Type': 'application/xml'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True)
