# 🛡️ 多模态恶意网页检测程序 (Multimodal Malicious Web Detection)

> 本项目是我的课程设计作品。基于多模态特征（如网页文本内容与网页截图视觉特征），实现对恶意网页的高效检测与拦截。

## 🌟 项目简介
随着网络攻击手段的升级，传统的单一特征检测已经难以应对复杂的恶意网页。本项目通过提取网页的**多模态特征**（结合了文本、结构以及视觉表现），利用机器学习/深度学习算法进行综合研判，并提供了一个直观的 Web 可视化界面供用户交互。

## 🚀 核心功能
- **自动化网页抓取**：使用 Playwright 动态渲染并截取网页快照，获取最真实的网页状态。
- **多模态特征提取**：结合 BeautifulSoup 解析 DOM 结构特征，同时处理图像视觉特征。
- **智能检测引擎**：基于 Scikit-learn 等构建的检测模型，快速输出安全评估结果。
- **Web 可视化交互**：提供友好的浏览器界面，用户输入 URL 即可一键生成检测报告。

## 🛠️ 技术栈
- **核心语言**：Python 3.10    


- **Web 框架**：Flask, Gunicorn
- **数据与模型**：Scikit-learn, Pandas, Numpy
- **爬虫与自动化**：Playwright, BeautifulSoup4
- **数据库**：SQLAlchemy
- **运行环境**：Ubuntu 22.04.5 LTS (推荐)

---

## ⚙️ 部署与运行指南

本项目在 Ubuntu 22.04 环境下测试通过。请按以下步骤进行本地部署：

### 1. 克隆项目与准备环境
建议使用虚拟环境（Virtual Environment）以避免依赖冲突：
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

### 2. 安装 Python 依赖
pip install -r requirements.txt

### 3. 安装 Playwright 浏览器内核及系统依赖
由于本项目依赖 Playwright 进行网页动态渲染与截图，必须执行以下命令安装 Chromium 内核及相关系统依赖：
playwright install chromium
sudo playwright install-deps

### 4. 运行程序
python project/app.py


📸 运行截图

    主界面

    ![alt text](【这里换成你的图片链接】)

    检测结果页

    ![alt text](【这里换成你的图片链接】)
