import math
import numpy as np
from PIL import Image, ImageFilter
import os
import asyncio
from bs4 import BeautifulSoup
import joblib
import pandas as pd
import json
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, BlackWhiteList, DetectionRecord
from playwright.async_api import async_playwright
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

try:
    model = joblib.load("malicious_web_model.pkl")
except:
    print("❌ 没找到模型文件，请确保已经生成了 malicious_web_model.pkl")

# --- 🎨 核心函数: 提取 26 个视觉特征 (逻辑不变) ---
def get_advanced_visual_features(img_path, bins=8):
    result_list = [0.0] * (2 + bins * 3) # [has_image, complexity, ...24个颜色]
    
    if not os.path.exists(img_path):
        return result_list

    try:
        with Image.open(img_path) as img:
            # 统一缩放
            img = img.convert('RGB').resize((256, 256))
            img_array = np.array(img)
            
            # A. 视觉复杂度
            gray_img = img.convert('L')
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            complexity = np.mean(np.array(edges)) / 255.0

            # B. 颜色直方图
            color_features = []
            for i in range(3): # R, G, B
                hist, _ = np.histogram(img_array[:, :, i], bins=bins, range=(0, 256), density=True)
                color_features.extend(hist.tolist())
            
            # 组装: [Has_Image(1), Complexity, ...Color...]
            result_list = [1.0, complexity] + color_features
            
    except Exception as e:
        print(f"特征提取出错: {e}")
    
    return result_list

# === 核心：Playwright (HTML + 截图) ===
async def extract_features(url):
    """
    使用 Playwright 同时获取 HTML 和 截图，效率翻倍！
    """
    html_content = None
    # 定义临时图片路径
    temp_img_name = f"temp_{int(time.time())}.png"
    # 确保 static 目录存在，否则截图会报错
    if not os.path.exists('static'):
        os.makedirs('static')
    temp_img_path = os.path.join('static', temp_img_name)
    
    screenshot_success = False

    try:
        async with async_playwright() as p:
            # 1. 启动内置浏览器 (Chromium)
            browser = await p.chromium.launch(
                headless=True, 
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # 创建上下文 (1080P 分辨率)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = await context.new_page()

            # 2. 访问网页
            try:
                # 设置超时 15秒
                await page.goto(url, timeout=15000, wait_until='domcontentloaded')
                await asyncio.sleep(1) # 等待渲染
                
                # === 获取 HTML ===
                html_content = await page.content()
                
                # === 直接截图 ===
                # full_page=True 意味着自动滚动截取长图，效果更好
                try:
                    print(f"📸 Playwright 正在截图: {url}")
                    await page.screenshot(path=temp_img_path, full_page=True)
                    screenshot_success = True
                except Exception as shot_err:
                    print(f"截图部分失败: {shot_err}")

            except Exception as e:
                print(f"Playwright 访问或处理失败: {e}")
                return None
            finally:
                await browser.close()

            # 3. === 特征提取逻辑 ===
            if not html_content:
                return None

            soup = BeautifulSoup(html_content, "html.parser")

            # --- 代码特征提取 ---
            html_length = len(html_content)
            scripts = soup.find_all("script")
            script_text = "".join([s.text for s in scripts])
            script_length = len(script_text)
            script_ratio = script_length / html_length if html_length > 0 else 0

            def calculate_entropy(text):
                if not text: return 0
                prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
                return -sum([p * math.log(p, 2) for p in prob])

            js_entropy = calculate_entropy(script_text)
            num_iframe = len(soup.find_all("iframe"))
            num_eval = script_text.count("eval(")
            num_document_write = script_text.count("document.write")

            # --- 视觉特征提取 (使用刚才 Playwright 截的图) ---
            visual_feats = [0.0] * 26 # 默认空特征
            if screenshot_success:
                visual_feats = get_advanced_visual_features(temp_img_path)
                
                # 清理截图 (提取完就删，节省空间)
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)

            # === 最终融合 ===
            code_feats = [html_length, script_length, script_ratio, js_entropy, num_iframe, num_eval, num_document_write]
            final_features = [code_feats + visual_feats] 
        
            return final_features
        
    except Exception as e:
        print(f"全局解析出错: {e}")
        return None


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("用户名已存在！")
            return redirect(url_for("register"))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            flash('登录成功！欢迎回来，' + user.username)
            return redirect(url_for('index'))
        flash('用户名或密码错误！')
    return render_template('login.html')

@app.route('/lists')
@login_required
def lists():
    rules = BlackWhiteList.query.all()
    return render_template('lists.html', rules=rules)

@app.route('/add_rule', methods=['POST'])
@login_required
def add_rule():
    url = request.form.get('url')
    list_type = request.form.get('list_type')
    note = request.form.get('note')
    if url and list_type:
        if not BlackWhiteList.query.filter_by(url=url).first():
            new_rule = BlackWhiteList(url=url, list_type=list_type, note=note)
            db.session.add(new_rule)
            db.session.commit()
            flash('添加成功！')
        else:
            flash('该网址已在名单中！')
    return redirect(url_for('lists'))

@app.route('/delete_rule/<int:id>')
@login_required
def delete_rule(id):
    rule = BlackWhiteList.query.get(id)
    if rule:
        db.session.delete(rule)
        db.session.commit()
        flash('删除成功')
    return redirect(url_for('lists'))

@app.route('/records')
@login_required
def records():
    user_records = DetectionRecord.query.filter_by(user_id=current_user.id).order_by(DetectionRecord.timestamp.desc()).all()
    return render_template('records.html', records=user_records)

@app.route('/delete_record/<int:id>')
@login_required
def delete_record(id):
    record = DetectionRecord.query.get(id)
    if record and record.user_id == current_user.id:
        db.session.delete(record)
        db.session.commit()
        flash('记录已删除')
    else:
        flash('删除失败：权限不足或记录不存在')
    return redirect(url_for('records'))

@app.route('/delete_all_records')
@login_required
def delete_all_records():
    DetectionRecord.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('历史记录已清空')
    return redirect(url_for('records'))

@app.route('/detail/<int:id>')
@login_required
def detail(id):
    record = DetectionRecord.query.get_or_404(id)
    try:
        features = json.loads(record.features_data) if record.features_data else {}
    except:
        features = {"错误": "数据解析失败"}
    return render_template('detail.html', record=record, features=features)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    text_data = request.form.get('urls')
    if not text_data:
        return redirect(url_for('index'))
        
    url_list = text_data.strip().split('\n')
    results_data = [] 

    # 特征名称列表
    names = ['HTML长度', '脚本长度', '脚本占比', 'JS信息熵', 'iFrame数量', 'eval函数', 'DocWrite调用']
    names += ['包含截图', '视觉复杂度']
    for c in ['R', 'G', 'B']:
        for i in range(8):
            names.append(f'颜色_{c}_区间{i+1}')
    feature_names = names

    for raw_url in url_list:
        url = raw_url.strip()
        if not url: continue
        
        if not url.startswith('http'): 
            process_url = 'http://' + url
        else:
            process_url = url

        record_id = None 
        status = "未知"
        score = 0
        color = "gray"
        source = "未知"
        features_json = None
        should_save_to_db = False

        # 1. 黑白名单
        rule = BlackWhiteList.query.filter_by(url=process_url).first()
        
        if rule:
            if rule.list_type == 'white':
                status = "良性"
                score = 0
                color = "#28a745"
                source = "🛡️ 白名单 (人工)"
            else:
                status = "恶意"
                score = 100
                color = "#dc3545"
                source = "🛡️ 黑名单 (人工)"
            features_json = json.dumps({"提示": f"命中{source}，跳过特征提取"})
            should_save_to_db = False 

        else:
            # 2. 查缓存
            history = DetectionRecord.query.filter_by(url=process_url).order_by(DetectionRecord.timestamp.desc()).first()

            if history:
                status = history.result
                score = history.score if history.score is not None else 0
                color = "#dc3545" if status == "恶意" else "#28a745"
                source = "💾 历史记录库 (已缓存)"
                record_id = history.id 
                should_save_to_db = False
            
            else:
                # 3. AI 计算 (Playwright 同时抓取代码和截图)
                try:
                    features = asyncio.run(extract_features(process_url))
                except Exception as e:
                    print(f"特征提取运行错误: {e}")
                    features = None
                
                if features:
                    prob = model.predict_proba(features)[0]
                    malicious_prob = prob[1] * 100
                    prediction = model.predict(features)
                    
                    status = "恶意" if prediction[0] == 1 else "良性"
                    score = round(malicious_prob, 2)
                    color = "#dc3545" if status == "恶意" else "#28a745"
                    source = "🧠 AI 模型计算"
                    
                    raw_features_dict = dict(zip(feature_names, features[0]))
                    features_json = json.dumps(raw_features_dict)
                    
                    should_save_to_db = True
                else:
                    status = "未知"
                    score = 0
                    color = "gray"
                    source = "⚠️ 抓取失败"
                    should_save_to_db = False

        if should_save_to_db:
            new_record = DetectionRecord(
                url=process_url, 
                result=status, 
                score=score, 
                features_data=features_json,
                user_id=current_user.id
            )
            db.session.add(new_record)
            db.session.flush() 
            record_id = new_record.id

        results_data.append({
            'id': record_id,
            'url': process_url,
            'status': status,
            'score': score,
            'color': color,
            'source': source
        })

    db.session.commit()
    
    return render_template('index.html', results=results_data)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # 允许任何IP访问
    app.run(host='0.0.0.0', port=5000, debug=False)
