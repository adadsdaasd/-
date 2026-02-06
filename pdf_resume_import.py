"""
PDF 简历导入工具
================
DeepSeek 无法直接识别图片型 PDF 的内容，因此采用两段式方案：
1) 若 PDF 是文本型：直接提取 PDF 文本
2) 若 PDF 是扫描件/图片型：本地 OCR（可选）后得到文本，再交给 LLM 做结构化解析

本模块只负责“把 PDF 变成文本”，不负责调用 LLM。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class PdfExtractResult:
    text: str
    method: str  # "text" | "ocr" | "none"
    page_count: int


def extract_pdf_text(
    pdf_bytes: bytes,
    *,
    ocr_enabled: bool = False,
    ocr_max_pages: int = 3,
    min_text_chars: int = 200,
) -> PdfExtractResult:
    """
    从 PDF 中提取文本。

    - 优先走 PDF 内嵌文本提取
    - 如果文本太少且允许 OCR，则对前 N 页执行 OCR
    """
    text, page_count = _extract_text_via_pymupdf(pdf_bytes)
    cleaned = _normalize_text(text)

    if len(cleaned) >= min_text_chars:
        return PdfExtractResult(text=cleaned, method="text", page_count=page_count)

    if not ocr_enabled:
        return PdfExtractResult(text=cleaned, method="none", page_count=page_count)

    ocr_text = _extract_text_via_ocr(pdf_bytes, max_pages=ocr_max_pages)
    ocr_cleaned = _normalize_text(ocr_text)
    if ocr_cleaned:
        return PdfExtractResult(text=ocr_cleaned, method="ocr", page_count=page_count)

    return PdfExtractResult(text=cleaned, method="none", page_count=page_count)


def _extract_text_via_pymupdf(pdf_bytes: bytes) -> Tuple[str, int]:
    """使用 PyMuPDF 提取 PDF 文本"""
    # 检查依赖
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        error_msg = (
            "缺少依赖：PyMuPDF。\n\n"
            "请运行以下命令安装：\n"
            "  pip install pymupdf\n\n"
            "或者安装完整依赖：\n"
            "  pip install -r requirements.txt\n\n"
            f"原始错误：{str(e)}"
        )
        raise RuntimeError(error_msg) from e
    except Exception as e:  # pragma: no cover
        error_msg = (
            f"PyMuPDF 导入失败：{str(e)}\n\n"
            "请确保已正确安装 pymupdf：\n"
            "  pip install pymupdf"
        )
        raise RuntimeError(error_msg) from e

    # 验证 PDF 文件
    if not pdf_bytes:
        raise RuntimeError("PDF 文件为空")
    
    if len(pdf_bytes) < 4 or pdf_bytes[:4] != b'%PDF':
        raise RuntimeError("不是有效的 PDF 文件（文件头不匹配）")
    
    # 提取文本
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise RuntimeError(f"无法打开 PDF 文件：{str(e)}") from e
    
    try:
        page_count = doc.page_count
        if page_count == 0:
            doc.close()
            raise RuntimeError("PDF 文件没有页面")
        
        chunks: List[str] = []
        for i in range(page_count):
            try:
                page = doc.load_page(i)
                text = page.get_text("text") or ""
                chunks.append(text)
            except Exception as e:
                # 如果某页提取失败，记录但继续
                chunks.append(f"[第 {i+1} 页提取失败: {str(e)}]")
        
        doc.close()
        return "\n".join(chunks), page_count
    except Exception as e:
        doc.close()
        raise RuntimeError(f"PDF 文本提取失败：{str(e)}") from e


def _extract_text_via_ocr(pdf_bytes: bytes, *, max_pages: int = 3) -> str:
    """
    使用 EasyOCR 对 PDF 前 max_pages 页做 OCR。

    注意：EasyOCR 首次运行可能需要下载模型（需要网络）。
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        error_msg = (
            "缺少依赖：PyMuPDF（OCR 功能需要）。\n\n"
            "请运行：pip install pymupdf\n\n"
            f"原始错误：{str(e)}"
        )
        raise RuntimeError(error_msg) from e
    
    try:
        import numpy as np
        from PIL import Image
        import easyocr
    except ImportError as e:
        error_msg = (
            "OCR 依赖缺失。\n\n"
            "请运行以下命令安装：\n"
            "  pip install easyocr pillow numpy\n\n"
            "或者安装完整依赖：\n"
            "  pip install -r requirements.txt\n\n"
            f"原始错误：{str(e)}"
        )
        raise RuntimeError(error_msg) from e
    except Exception as e:  # pragma: no cover
        error_msg = (
            f"OCR 依赖导入失败：{str(e)}\n\n"
            "请确保已正确安装：easyocr, pillow, numpy"
        )
        raise RuntimeError(error_msg) from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count
    pages = min(max_pages, page_count)

    # 中英混合简历常见；可按需增减语言
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False)

    chunks: List[str] = []
    for i in range(pages):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        result = reader.readtext(np.array(img), detail=0, paragraph=True)
        if result:
            chunks.append("\n".join([r.strip() for r in result if isinstance(r, str)]))

    doc.close()
    return "\n".join(chunks)


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    # 合并多余空白，保留段落结构
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


# ==================== 简历文本清洗 ====================

# 段落识别关键词映射
SECTION_KEYWORDS = {
    "【个人信息】": ["姓名", "性别", "出生", "籍贯", "联系", "电话", "邮箱", "手机", "地址", "民族", "政治面貌", "婚姻"],
    "【教育背景】": ["教育", "学历", "毕业", "学校", "专业", "学位", "本科", "硕士", "博士", "研究生", "大学", "学院"],
    "【工作经历】": ["工作", "经历", "任职", "公司", "职位", "职责", "就职", "在职", "离职"],
    "【项目经验】": ["项目", "参与", "负责", "主导", "开发", "实施"],
    "【技能特长】": ["技能", "技术", "擅长", "熟练", "掌握", "精通", "了解", "能力"],
    "【自我评价】": ["评价", "优势", "特点", "自述", "简介", "总结", "自我"],
    "【获奖荣誉】": ["获奖", "荣誉", "奖项", "证书", "资质"],
    "【论文著作】": ["论文", "发表", "期刊", "出版", "著作", "专利"],
}

# 噪音模式（页眉页脚、页码等）
import re

NOISE_PATTERNS = [
    r"^第?\s*\d+\s*页?[/／共]?\s*\d*\s*页?$",  # 页码: 第1页、1/5、Page 1
    r"^Page\s*\d+\s*(of\s*\d+)?$",  # Page 1 of 5
    r"^[-—–]+$",  # 纯分隔线
    r"^\d{1,3}$",  # 单独的数字（可能是页码）
    r"^[·•●○◆◇■□▪▫]+$",  # 纯符号行
]


def clean_resume_text(raw_text: str) -> str:
    """
    清洗简历文本，识别段落结构
    
    功能：
    1. 移除噪音（页码、页眉页脚）
    2. 识别段落标题（教育背景、工作经历...）
    3. 合并跨页段落
    4. 返回结构化文本
    
    Args:
        raw_text: 原始提取的文本
        
    Returns:
        清洗后的结构化文本
    """
    if not raw_text:
        return ""
    
    lines = raw_text.splitlines()
    cleaned_lines: List[str] = []
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行
        if not line:
            continue
        
        # 检查是否是噪音
        if _is_noise_line(line):
            continue
        
        # 统一标点符号
        line = _normalize_punctuation(line)
        
        cleaned_lines.append(line)
    
    # 合并跨页打断的段落
    merged_lines = _merge_broken_paragraphs(cleaned_lines)
    
    # 识别并标注段落
    structured_lines = _identify_sections(merged_lines)
    
    return "\n".join(structured_lines)


def _is_noise_line(line: str) -> bool:
    """检查是否是噪音行（页码、页眉页脚等）"""
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    
    # 太短且不包含有意义内容的行
    if len(line) <= 2 and not any('\u4e00' <= c <= '\u9fff' for c in line):
        return True
    
    return False


def _normalize_punctuation(text: str) -> str:
    """统一标点符号"""
    replacements = {
        "，": ", ",
        "。": ". ",
        "：": ": ",
        "；": "; ",
        "（": " (",
        "）": ") ",
        "【": "[",
        "】": "]",
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _merge_broken_paragraphs(lines: List[str]) -> List[str]:
    """合并被分页打断的段落"""
    if not lines:
        return []
    
    merged: List[str] = []
    buffer = ""
    
    for line in lines:
        # 检查是否是段落标题（通常较短且可能包含特定关键词）
        is_section_header = _is_section_header(line)
        
        if is_section_header:
            # 保存之前的缓冲区
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append(line)
        elif buffer and _should_merge_with_previous(buffer, line):
            # 合并到前一行
            buffer = buffer + " " + line
        else:
            if buffer:
                merged.append(buffer)
            buffer = line
    
    if buffer:
        merged.append(buffer)
    
    return merged


def _is_section_header(line: str) -> bool:
    """判断是否是段落标题"""
    # 已经被标记的段落
    if line.startswith("【") and "】" in line:
        return True
    
    # 检查是否包含段落关键词
    for section, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            # 标题通常较短且包含关键词
            if keyword in line and len(line) < 30:
                return True
    
    return False


def _should_merge_with_previous(prev: str, curr: str) -> bool:
    """判断当前行是否应该合并到前一行"""
    # 如果前一行以不完整的句子结束（没有句号等）
    if prev and not prev[-1] in '.。!！?？;；':
        # 且当前行不是新段落的开始
        if not _is_section_header(curr):
            # 且当前行以小写字母或中文开头（续接上文）
            if curr and (curr[0].islower() or '\u4e00' <= curr[0] <= '\u9fff'):
                return True
    return False


def _identify_sections(lines: List[str]) -> List[str]:
    """识别并标注段落"""
    result: List[str] = []
    current_section = None
    
    for line in lines:
        # 检查是否应该标注为某个段落
        detected_section = _detect_section(line)
        
        if detected_section and detected_section != current_section:
            current_section = detected_section
            # 如果行本身不是标题，添加段落标签
            if not line.startswith("【"):
                result.append(f"\n{detected_section}")
        
        result.append(line)
    
    return result


def _detect_section(line: str) -> Optional[str]:
    """检测行属于哪个段落"""
    for section, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in line:
                return section
    return None


# ==================== 文本合并去重 ====================

def merge_text_sources(text_extracted: str, ocr_text: str, similarity_threshold: float = 0.7) -> str:
    """
    合并文本抽取和 OCR 的结果，去除重复内容
    
    Args:
        text_extracted: PDF 文本抽取的结果
        ocr_text: OCR 识别的结果
        similarity_threshold: 相似度阈值，超过此值视为重复
        
    Returns:
        合并去重后的文本
    """
    if not text_extracted and not ocr_text:
        return ""
    
    if not text_extracted:
        return ocr_text
    
    if not ocr_text:
        return text_extracted
    
    # 将两个文本分段
    text_paragraphs = _split_to_paragraphs(text_extracted)
    ocr_paragraphs = _split_to_paragraphs(ocr_text)
    
    # 使用文本抽取作为基础，补充 OCR 中的新内容
    result_paragraphs = list(text_paragraphs)
    
    for ocr_para in ocr_paragraphs:
        if not ocr_para.strip():
            continue
        
        # 检查是否与已有段落重复
        is_duplicate = False
        for existing_para in result_paragraphs:
            if _calculate_similarity(ocr_para, existing_para) >= similarity_threshold:
                is_duplicate = True
                # 如果 OCR 版本更长（可能更完整），替换
                if len(ocr_para) > len(existing_para) * 1.2:
                    idx = result_paragraphs.index(existing_para)
                    result_paragraphs[idx] = ocr_para
                break
        
        if not is_duplicate:
            result_paragraphs.append(ocr_para)
    
    return "\n\n".join(result_paragraphs)


def _split_to_paragraphs(text: str) -> List[str]:
    """将文本分割为段落"""
    # 按空行分割
    paragraphs = re.split(r'\n\s*\n', text)
    # 清理每个段落
    return [p.strip() for p in paragraphs if p.strip()]


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（简单实现：基于字符重叠）
    
    Returns:
        0.0 到 1.0 之间的相似度值
    """
    if not text1 or not text2:
        return 0.0
    
    # 移除空白，转为字符集合
    set1 = set(text1.replace(" ", "").replace("\n", ""))
    set2 = set(text2.replace(" ", "").replace("\n", ""))
    
    if not set1 or not set2:
        return 0.0
    
    # Jaccard 相似度
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0

