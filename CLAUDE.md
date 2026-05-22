# Essay Grader — 作文批改助手

## 领域定位
教育辅助工具，面向家庭场景。接收中英文作文输入，产出 HTML/DOCX 结构化批改报告（语法纠错、结构分析、评分）。

## 功能概述
Web 应用，上传或输入作文（中文/英文），通过 DeepSeek API 进行语法纠错、结构分析和评分，支持 Word 式批注查看和 HTML/DOCX 报告导出。

## 架构

```
浏览器前端 (Alpine.js) → FastAPI 后端 → DeepSeek Chat API
```

## 常用命令

### 启动
```bash
source venv/bin/activate
python main.py
```

浏览器打开 **http://localhost:8001**。

### 安装/初始化
```bash
bash setup.sh
```

## 技术栈
- 后端: Python FastAPI, uvicorn
- 前端: Jinja2 模板, Alpine.js (CDN)
- 文档解析: python-docx (.docx), 内置 (.txt)
- AI: DeepSeek Chat API (openai SDK)
- 导出: HTML / python-docx

## 模块
- `main.py` — FastAPI 路由 (GET /, POST /api/grade, GET /api/export/*)
- `doc_parser.py` — 文件格式解析 (txt/docx)
- `grading.py` — DeepSeek API 调用，生成批改结果
- `exporter.py` — HTML/DOCX 报告导出

## 依赖服务
- DeepSeek API (platform.deepseek.com)
