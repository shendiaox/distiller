"""知识库核心 — SQLite 文本存储 + TF-IDF 检索（纯本地，零下载）"""

import os
import re
import eel

from backend.database import get_connection, dict_from_row
from backend.embedding import search_tfidf

# ---------- 文本分块 ----------

def _split_text(text, chunk_size=500, overlap=50):
    """按段落和句子边界切分文本"""
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    current = ''
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) <= chunk_size:
            current = (current + '\n\n' + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                sentences = re.split(r'(?<=[。！？.!?])\s*', para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current) + len(sent) <= chunk_size:
                        current = (current + sent).strip()
                    else:
                        if current:
                            chunks.append(current)
                        if len(sent) > chunk_size:
                            for i in range(0, len(sent), chunk_size - overlap):
                                chunks.append(sent[i:i + chunk_size - overlap])
                            current = ''
                        else:
                            current = sent
    if current:
        chunks.append(current)
    return chunks


# ---------- @eel.expose 接口 ----------

@eel.expose
def rename_knowledge_base(kb_id, new_name):
    conn = get_connection()
    with conn:
        conn.execute('UPDATE knowledge_bases SET name=?, updated_at=datetime("now","localtime") WHERE id=?',
                     (new_name, int(kb_id)))
    return {'ok': True}


@eel.expose
def delete_knowledge_base(kb_id):
    kb_id = int(kb_id)
    conn = get_connection()
    with conn:
        conn.execute('DELETE FROM chunks WHERE doc_id IN (SELECT id FROM documents WHERE kb_id=?)', (kb_id,))
        conn.execute('DELETE FROM documents WHERE kb_id=?', (kb_id,))
        conn.execute('DELETE FROM knowledge_bases WHERE id=?', (kb_id,))
    return {'ok': True}


@eel.expose
def list_knowledge_bases():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM knowledge_bases ORDER BY id').fetchall()
    return [dict_from_row(r) for r in rows]


@eel.expose
def create_knowledge_base(name, description=''):
    conn = get_connection()
    with conn:
        cur = conn.execute(
            'INSERT INTO knowledge_bases (name, description) VALUES (?, ?)',
            (name, description),
        )
        kb_id = cur.lastrowid
    return {'ok': True, 'id': kb_id}


@eel.expose
def ingest_text(kb_id, title, text):
    """将文本分块存入 SQLite"""
    kb_id = int(kb_id)
    chunks = _split_text(text)
    if not chunks:
        return {'ok': False, 'error': '文本内容为空，无法录入'}

    conn = get_connection()
    with conn:
        cur = conn.execute(
            'INSERT INTO documents (kb_id, title, source_type, chunk_count) VALUES (?, ?, ?, ?)',
            (kb_id, title, 'paste', len(chunks)),
        )
        doc_id = cur.lastrowid
        for i, chunk in enumerate(chunks):
            conn.execute(
                'INSERT INTO chunks (doc_id, kb_id, chunk_index, content) VALUES (?, ?, ?, ?)',
                (doc_id, kb_id, i, chunk),
            )

    conn.execute(
        'UPDATE knowledge_bases SET updated_at = datetime("now","localtime") WHERE id = ?',
        (kb_id,),
    )
    conn.commit()

    return {'ok': True, 'chunk_count': len(chunks)}


@eel.expose
def ingest_file(kb_id, filepath, title=None):
    """上传文件并录入知识库"""
    from backend.document_parser import parse_file

    kb_id = int(kb_id)
    if not os.path.exists(filepath):
        return {'ok': False, 'error': f'文件不存在: {filepath}'}

    if title is None:
        title = os.path.basename(filepath)

    try:
        text = parse_file(filepath)
    except Exception as e:
        return {'ok': False, 'error': f'文件解析失败: {str(e)}'}

    if not text.strip():
        return {'ok': False, 'error': '文件内容为空'}

    chunks = _split_text(text)
    if not chunks:
        return {'ok': False, 'error': '无法从文件中提取有效文本'}

    conn = get_connection()
    with conn:
        cur = conn.execute(
            'INSERT INTO documents (kb_id, title, source_type, source_path, chunk_count) VALUES (?, ?, ?, ?, ?)',
            (kb_id, title, 'file', filepath, len(chunks)),
        )
        doc_id = cur.lastrowid
        for i, chunk in enumerate(chunks):
            conn.execute(
                'INSERT INTO chunks (doc_id, kb_id, chunk_index, content) VALUES (?, ?, ?, ?)',
                (doc_id, kb_id, i, chunk),
            )

    conn.execute(
        'UPDATE knowledge_bases SET updated_at = datetime("now","localtime") WHERE id = ?',
        (kb_id,),
    )
    conn.commit()

    return {'ok': True, 'chunk_count': len(chunks), 'doc_id': doc_id, 'title': title}


@eel.expose
def select_file_dialog():
    """打开 Windows 文件选择对话框"""
    import subprocess
    import json

    ps_script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dlg = New-Object System.Windows.Forms.OpenFileDialog
$dlg.Title = '选择文档文件'
$dlg.Filter = '支持的文档 (*.txt;*.docx;*.pdf)|*.txt;*.docx;*.pdf|文本文件 (*.txt)|*.txt|Word 文档 (*.docx)|*.docx|PDF 文档 (*.pdf)|*.pdf|所有文件 (*.*)|*.*'
$dlg.Multiselect = $false
if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    @{ok=$true; path=$dlg.FileName; name=[System.IO.Path]::GetFileName($dlg.FileName)} | ConvertTo-Json -Compress
} else {
    @{ok=$false; path=''} | ConvertTo-Json -Compress
}
'''
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            if data.get('ok') and data.get('path'):
                return {'ok': True, 'path': data['path'], 'name': data.get('name', os.path.basename(data['path']))}
    except Exception:
        pass

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        filepath = filedialog.askopenfilename(
            title='选择文档文件',
            filetypes=[('支持的文档', '*.txt;*.docx;*.pdf'), ('所有文件', '*.*')],
        )
        root.destroy()
        if filepath:
            return {'ok': True, 'path': filepath, 'name': os.path.basename(filepath)}
    except Exception:
        pass

    return {'ok': False, 'path': ''}


@eel.expose
def search_knowledge_base(kb_id, query, k=5):
    """TF-IDF 语义检索"""
    kb_id = int(kb_id)
    conn = get_connection()
    chunks = conn.execute(
        'SELECT id, doc_id, chunk_index, content FROM chunks WHERE kb_id=?', (kb_id,)
    ).fetchall()

    if not chunks:
        return {'ok': True, 'results': []}

    contents = [c['content'] for c in chunks]
    results = search_tfidf(contents, query, k)
    items = []
    for r in results:
        chunk = chunks[r['index']]
        items.append({
            'id': f'kb{kb_id}_d{chunk["doc_id"]}_c{chunk["chunk_index"]}',
            'content': chunk['content'],
            'metadata': {'chunk_index': chunk['chunk_index'], 'kb_id': kb_id},
            'score': r['score'],
        })
    return {'ok': True, 'results': items}


@eel.expose
def get_kb_documents(kb_id):
    """获取知识库中的文档列表"""
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM documents WHERE kb_id = ? ORDER BY created_at DESC',
        (int(kb_id),),
    ).fetchall()
    return [dict_from_row(r) for r in rows]


@eel.expose
def delete_document(doc_id):
    """删除文档及其所有 chunks"""
    conn = get_connection()
    doc = conn.execute('SELECT * FROM documents WHERE id = ?', (int(doc_id),)).fetchone()
    if not doc:
        return {'ok': False, 'error': '文档不存在'}
    with conn:
        conn.execute('DELETE FROM chunks WHERE doc_id = ?', (int(doc_id),))
        conn.execute('DELETE FROM documents WHERE id = ?', (int(doc_id),))
    return {'ok': True}


@eel.expose
def get_kb_stats(kb_id):
    """知识库统计信息"""
    kb_id = int(kb_id)
    conn = get_connection()
    doc_count = conn.execute(
        'SELECT COUNT(*) FROM documents WHERE kb_id = ?', (kb_id,)
    ).fetchone()[0]
    chunk_count = conn.execute(
        'SELECT COALESCE(SUM(chunk_count), 0) FROM documents WHERE kb_id = ?', (kb_id,)
    ).fetchone()[0]
    chunk_total = conn.execute(
        'SELECT COUNT(*) FROM chunks WHERE kb_id = ?', (kb_id,)
    ).fetchone()[0]
    return {'document_count': doc_count, 'chunk_count': chunk_count, 'vector_count': chunk_total}
