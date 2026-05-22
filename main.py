"""Essay Grader — FastAPI web application."""
import os
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from doc_parser import extract_text
from grading import grade_essay
from exporter import export_html, export_docx

app = FastAPI(title="作文批改助手")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Read the single-page HTML template at startup
_INDEX_HTML = open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8").read()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main page (submission form + results)."""
    return HTMLResponse(content=_INDEX_HTML)


@app.post("/api/grade")
async def grade(request: Request):
    """Grade an essay submitted as text or file upload."""
    form = await request.form()
    essay_text = (form.get("essay_text") or "").strip()
    essay_file = form.get("essay_file")

    if essay_file and hasattr(essay_file, "filename") and essay_file.filename:
        content = await essay_file.read()
        if content:
            try:
                essay_text = extract_text(essay_file.filename, content)
            except ValueError as e:
                return {"error": str(e)}

    if not essay_text:
        return {"error": "请输入作文内容或上传文件。"}

    if len(essay_text) < 20:
        return {"error": "作文太短，至少需要 20 个字。请检查后重试。"}

    if len(essay_text) > 10000:
        return {"error": "作文过长（超过 10000 字），请分段提交或精简内容。"}

    try:
        result = grade_essay(essay_text)
        result["original_text"] = essay_text
        return result
    except RuntimeError as e:
        return {"error": str(e)}


@app.get("/api/export/html")
async def export_html_endpoint(text: str = "", language: str = "zh",
                                word_count: int = 0, overall_comment: str = "",
                                annotations_json: str = ""):
    """Export grading result as HTML file download."""
    import json
    try:
        annotations = json.loads(annotations_json) if annotations_json else []
        result = {
            "language": language,
            "word_count": word_count,
            "overall_comment": overall_comment,
            "annotations": annotations,
        }
        html = export_html(text, result)
        return Response(
            content=html,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=essay_report.html"}
        )
    except Exception as e:
        return {"error": f"导出失败：{e}"}


@app.get("/api/export/docx")
async def export_docx_endpoint(text: str = "", language: str = "zh",
                                word_count: int = 0, overall_comment: str = "",
                                annotations_json: str = ""):
    """Export grading result as DOCX file download."""
    import json
    try:
        annotations = json.loads(annotations_json) if annotations_json else []
        result = {
            "language": language,
            "word_count": word_count,
            "overall_comment": overall_comment,
            "annotations": annotations,
        }
        docx_bytes = export_docx(text, result)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=essay_report.docx"}
        )
    except Exception as e:
        return {"error": f"导出失败：{e}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
