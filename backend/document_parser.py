"""文档解析器 — 支持 txt / docx / pdf"""

import os


def parse_file(filepath):
    """根据扩展名自动选择解析器，返回文本内容"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.txt':
        return _parse_txt(filepath)
    elif ext == '.docx':
        return _parse_docx(filepath)
    elif ext == '.pdf':
        return _parse_pdf(filepath)
    else:
        raise ValueError(f'不支持的文件格式: {ext}。支持的格式: .txt / .docx / .pdf')


def _parse_txt(filepath):
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError('无法识别文件编码，请转为 UTF-8 后重试')


def _parse_docx(filepath):
    from docx import Document
    doc = Document(filepath)
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())
    return '\n\n'.join(paragraphs)


def _parse_pdf(filepath):
    from PyPDF2 import PdfReader

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        msg = str(e)
        if 'PyCryptodome' in msg or 'AES' in msg:
            raise ValueError('此 PDF 文件已加密，无法读取。请使用未加密的 PDF 文件，或将内容复制粘贴录入。')
        raise

    pages = []
    for page in reader.pages:
        try:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        except Exception:
            pass  # 跳过无法提取的页面

    if not pages:
        raise ValueError('PDF 文件无法提取文字内容（可能是扫描件或图片型 PDF）。建议直接粘贴文字录入。')

    return '\n\n'.join(pages)
