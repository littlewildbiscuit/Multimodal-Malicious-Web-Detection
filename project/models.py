from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 用户表
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    # 设置密码时自动哈希
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 检查密码是否正确
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 检测记录表
class DetectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    result = db.Column(db.String(50), nullable=False)
    # ⬇️ 新增这一行：记录检测时间
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Float, default=0.0)
    # ⬇️ 新增这一行：用来存那一大串特征数据 (存成 JSON 文本)
    features_data = db.Column(db.Text, nullable=True)

class BlackWhiteList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    list_type = db.Column(db.String(10), nullable=False) # 存 'white' 或 'black'
    note = db.Column(db.String(200)) # 备注，比如“这是学校官网”

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key' # 随便写个字符串，用于加密 session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # 未登录时跳往的页面

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 注册路由 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# --- 登录路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('用户名或密码错误！')
    return render_template('login.html')

# 在第一次运行前，先创建数据库文件
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)