# Essay Grader — 作文批改助手

## 领域定位
教育辅助工具，面向家庭场景。接收中英文作文输入，产出 HTML/DOCX 结构化批改报告（语法纠错、结构分析、评分）。

## 功能概述
Web 应用，上传或输入作文（中文/英文），通过 DeepSeek API 进行语法纠错、结构分析和评分，支持作文高亮对照查看和 HTML/DOCX 报告导出。

## 架构

```
浏览器 (Streamlit) → DeepSeek Chat API
```

## 常用命令

### 启动
```bash
source venv/bin/activate
streamlit run app.py --server.port 8505
```

浏览器打开 **http://localhost:8505**。

### 安装/初始化
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY
```

## 技术栈
- Web 框架: Streamlit
- 文档解析: python-docx (.docx), pdfplumber (.pdf), 内置 (.txt)
- 图片OCR: DeepSeek Vision API (Pillow)
- URL抓取: httpx
- AI: DeepSeek Chat API (openai SDK)
- 导出: HTML / python-docx

## 模块
- `app.py` — Streamlit 应用入口
- `ui/sidebar.py` — 侧边栏参数面板
- `ui/results.py` — 批改结果展示（双栏对照、维度筛选、导出）
- `doc_parser.py` — 文件格式解析 (txt/docx/pdf)
- `context_collector.py` — 背景信息收集 (文字/URL/文件/图片OCR)
- `grading.py` — DeepSeek API 调用，生成批改结果
- `exporter.py` — HTML/DOCX 报告导出

## 依赖服务
- DeepSeek API (platform.deepseek.com)

## 线上地址

任何设备浏览器打开：部署后在 Streamlit Cloud 获取 URL

## 部署与同步

代码推送后 Streamlit Cloud 自动重新部署，无需手动操作。

```bash
cd ~/agents/home/essay-grader

# 1. 修改代码
# 2. 本地测试
streamlit run app.py --server.port 8505

# 3. 提交
git add -A && git commit -m "描述改动内容"

# 4. 推送 GitHub（自动触发 Streamlit Cloud 更新）
git push
```

推送后等待 1-2 分钟，刷新线上网址即可看到最新版。
