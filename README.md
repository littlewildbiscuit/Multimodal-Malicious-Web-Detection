# 🛡️ 多模态恶意网页检测系统 (Multimodal Malicious Web Detection)

> **多维特征 | 智能检测 | Web可视化** —— 旨在通过综合研判网页的文本与视觉特征，实现对恶意网页的高效拦截。

随着网络攻击手段的不断升级，传统的单一特征检测已难以应对复杂的恶意网页。本项目创新性地提取了网页的多模态特征，结合机器学习算法进行综合打分，并提供了一个直观友好的 Web 交互界面。

---

## ✨ 核心功能

- **自动化动态抓取**：底层基于 Playwright 无头浏览器，动态渲染并截取网页真实视觉快照。
- **多模态特征融合**：
  - **DOM 结构特征**：使用 BeautifulSoup4 深度解析网页源码标签树。
  - **视觉呈现特征**：结合 Pillow 处理网页截图，提取视觉层面的欺诈特征。
- **智能评估引擎**：集成 Scikit-learn 构建的机器学习分类器，毫秒级输出安全检测报告。
- **零门槛 Web 交互**：基于 Flask 搭建轻量级服务，用户只需输入 URL 即可一键生成全方位体检报告。

---

## 🛠️ 技术栈

*   **核心语言**：Python 3.10
*   **Web 框架**：Flask, Gunicorn (生产级 WSGI 部署)
*   **AI 与数据处理**：Scikit-learn, Pandas, Numpy
*   **爬虫与自动化**：Playwright, BeautifulSoup4
*   **数据持久化**：SQLAlchemy
*   **推荐环境**：Ubuntu 22.04 LTS

---

## 🚀 快速开始

本项目在 Ubuntu 22.04 环境下测试通过。请按以下步骤进行本地部署：

### 1. 克隆与环境隔离

建议使用 Python 虚拟环境以避免全局依赖冲突：

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装 Python 核心依赖

```bash
pip install -r requirements.txt
```

### 3. 安装浏览器内核及系统依赖

由于本项目需要动态渲染网页，**必须**执行以下命令安装 Chromium 内核：

```bash
playwright install chromium
sudo playwright install-deps
```

### 4. 运行服务

```bash
# 启动 Flask 服务
python app.py
```

> **💡 提示**：首次运行程序时，系统会自动在 `instance/` 目录下生成 `database.db` 数据库文件，无需手动配置 SQL 环境。

程序启动后，请在浏览器中访问 `http://127.0.0.1:80` (或服务器的实际 IP)。

---

## 📸 运行截图

<p align="center">
  <p>主模块：</p>
  <img width="600" alt="核心模块" src="https://github.com/user-attachments/assets/9d8df687-379e-4289-9cc7-d40ffd42bffe" />
  <br>
</p>

<p align="center">
  <p>特征分析与详细报告：</p>
  <img width="600" alt="详细报告" src="https://github.com/user-attachments/assets/c4f28e3b-2a1f-44eb-876d-3eb9c894a33c" />
  <br>
</p>

<p align="center">
  <p>历史记录与系统审计：</p>
  <img width="600" alt="历史记录" src="https://github.com/user-attachments/assets/25add7d8-79c8-4ab4-ab4a-efffd6e0214a" />
  <br>
</p>
