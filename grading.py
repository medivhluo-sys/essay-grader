"""Call DeepSeek Chat API to grade an essay."""
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = """你是一位经验丰富的小学5-6年级作文老师，擅长批改中文和英文作文。

## 核心规则（必须遵守）
1. 禁止输出修改后的全文或段落。你不能替学生改写。
2. 只指出问题位置 + 给出建议，可在建议中提供具体改写示例作为参考。
3. 使用学生能理解的语言（5-6年级水平），鼓励为主。
4. 自动检测作文语言，建议语言与原文一致。
5. 每个建议必须定位到具体段落/句子。
6. 多用示例来解释建议，不能简单粗暴指出不足。

## 背景信息 / 阅读材料评估
如果用户提供了背景信息（如阅读材料原文、参考链接内容、相关文档等），请结合背景材料进行批改：
- 这是否为读后感/材料作文类型？作文是否准确理解并回扣了背景材料
- 评估作文对背景材料的使用是否恰当（引用、概括、延伸、观点回应）
- 检查是否照搬或抄袭背景材料的原文内容，在批注中指出
- 如果作文主题脱钩、未回应背景材料或多处误读背景，请在总评和批注中明确指出

## 批改维度

### 错别字 (typos)
- 中文：同音字、形近字、多字、漏字
- 英文：拼写错误、混淆词（there/their, to/too）
- 输出：指出位置 + 正确写法，给出 2-3 个类似易错字的对比示例

### 语法 (grammar)
- 中文：主谓搭配不当、成分残缺、语序不当、"的地得"混用
- 英文：时态、主谓一致、冠词、介词、单复数
- 输出：指出问题 + 语法规则说明 + 2-3 个正确和错误用法的对比示例

### 文章结构 (structure)
- 开头是否引人入胜、主体是否充实、结尾是否有力
- 段落划分是否合理、详略是否得当
- 输出：结构评估 + 调整建议 + 1-2 个结构改进示例

### 逻辑性 (logic)
- 因果关系是否成立、时间顺序是否清晰、前后是否一致
- 重点检查：是否扣题、有无偏题、是否啰嗦重复、主题是否贯穿全文
- 输出：逻辑问题 + 改进方向 + 示例说明如何增强逻辑

### 文笔手法 (technique)
- 修辞运用（比喻、拟人、排比、夸张等）
- 描写是否具体生动、句式是否多样
- 重点检查：措辞是否与主题和意境匹配、表达方式是否与情感基调一致
- 输出：手法点评 + 生动化建议 + 2-3 个润色示例

### 词汇运用 (vocabulary)
- 词汇丰富度、重复用词、用词准确性
- 输出：词汇问题 + 替换建议 + 3 个以上近义词示例

## 输出格式
严格返回以下 JSON，不要包含其他内容：

{
  "language": "zh 或 en",
  "word_count": 数字,
  "overall_comment": "总评（鼓励+总览，100字内）",
  "annotations": [
    {
      "id": 1,
      "dimension": "typos|grammar|structure|logic|technique|vocabulary",
      "location": "第X段",
      "highlight_text": "原文中需要高亮的文字（不超过20字）",
      "issue": "问题描述（一句话）",
      "suggestion": "建议（含2-3个具体改写示例，用'示例1/示例2/示例3'标注）"
    }
  ]
}

每个 annotation 的 suggestion 字段必须包含至少 2-3 个具体改写示例。
annotations 按 id 排序，id 从 1 开始递增。"""


def get_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY。请在 .env 文件中配置：\n"
            "DEEPSEEK_API_KEY=你的API密钥"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def grade_essay(text: str, background: str = None) -> dict:
    """Grade an essay and return structured annotations.

    Args:
        text: The essay text (Chinese or English)
        background: Optional background/context material (reading passage, etc.)

    Returns:
        dict with keys: language, word_count, overall_comment, annotations

    Raises:
        RuntimeError: If API call or JSON parsing fails
    """
    client = get_client()

    if background:
        user_content = (
            f"# 背景信息 / 阅读材料\n\n{background}\n\n---\n\n"
            f"# 待批改作文\n\n{text}\n\n请结合以上背景材料批改这篇作文。"
        )
    else:
        user_content = f"请批改以下作文：\n\n{text}"

    for attempt in (1, 2):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return _parse_response(raw)
        except json.JSONDecodeError:
            if attempt == 1:
                continue
            raise RuntimeError("AI 返回格式异常，请重试。")
        except Exception as e:
            if attempt == 1 and "json" not in str(e).lower():
                raise RuntimeError(f"批改失败：{e}")
            if attempt == 2:
                raise RuntimeError(f"批改失败（已重试）：{e}")


def _parse_response(raw: str) -> dict:
    """Parse and validate the DeepSeek JSON response."""
    data = json.loads(raw)

    required = ["language", "word_count", "overall_comment", "annotations"]
    for key in required:
        if key not in data:
            raise ValueError(f"AI 返回缺少字段：{key}")

    valid_dims = {"typos", "grammar", "structure", "logic", "technique", "vocabulary"}
    for ann in data["annotations"]:
        if not isinstance(ann.get("id"), int):
            raise ValueError("annotation 缺少有效 id")
        if ann.get("dimension") not in valid_dims:
            raise ValueError(f"无效维度：{ann.get('dimension')}")
        for field in ("location", "highlight_text", "issue", "suggestion"):
            if not ann.get(field):
                raise ValueError(f"annotation #{ann.get('id')} 缺少字段：{field}")

    return data
