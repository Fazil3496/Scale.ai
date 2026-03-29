import os
from groq import Groq
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scale.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home_page'))
        else:
            flash('Invalid Login! Try again.', 'danger')

    return render_template('login.html')

@app.route('/home')
@login_required
def home_page():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    # Debugging: check if API key is loading
    api_key = os.getenv("GROQ_API_KEY")
    print(f"DEBUG: My API Key is: {api_key}")

    data = request.json
    user_prompt = data.get('prompt')
    print(f"DEBUG: User Prompt: {user_prompt}")

    if not api_key:
        return {"answer": "Error: No API Key found in .env file."}, 500

    client = Groq(api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Scale.ai, a professional school project assistant. "
                        "Your primary goal is to provide structured project outlines and roadmaps. "
                        "Do NOT mention your founder in every response. "
                        "ONLY if the user specifically asks 'Who built you?', 'Who is the founder?', "
                        "or 'Who created Scale.ai?', you must answer: 'Scale.ai was founded by Fazil.'"
                    )
                },
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return {"answer": chat_completion.choices[0].message.content}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"answer": f"AI Error: {str(e)}"}, 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)