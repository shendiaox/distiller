"""全网搜索 — Bing 中国 + 百度百科直达 + 网页抓取"""

import eel
import requests
from bs4 import BeautifulSoup

from backend.knowledge_base import _split_text


@eel.expose
def web_search(query, max_results=10):
    """Bing 中国搜索 + 百度百科直达"""
    all_results = []
    baike_results = _search_bing(f'site:baike.baidu.com {query}', max_results=5)
    if baike_results:
        all_results.extend(baike_results)
    bing_results = _search_bing(query, max_results=max_results)
    if bing_results:
        seen = {r['href'] for r in all_results}
        for r in bing_results:
            if r['href'] not in seen:
                all_results.append(r)
    if all_results:
        return {'ok': True, 'results': all_results[:max_results], 'query': query, 'engine': 'Bing'}
    return {'ok': False, 'error': '搜索无结果。请通过「粘贴文本」「上传文件」手动录入。'}


def _search_bing(query, max_results=10):
    try:
        url = 'https://cn.bing.com/search'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        resp = requests.get(url, params={'q': query, 'count': max_results, 'setlang': 'zh-CN'}, headers=headers, timeout=12)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'lxml')
        results = []
        for item in soup.select('li.b_algo')[:max_results]:
            link = item.select_one('h2 a')
            if not link:
                continue
            title = link.get_text(strip=True)
            href = link.get('href', '')
            snippet_el = item.select_one('.b_caption p, .b_lineclamp2, .b_algoSlug')
            body = snippet_el.get_text(strip=True) if snippet_el else ''
            if title and href:
                results.append({'title': title, 'body': body, 'href': href})
        return results if results else None
    except Exception:
        return None


@eel.expose
def fetch_and_ingest_urls(kb_id, urls):
    kb_id = int(kb_id)
    results = []
    for url in urls:
        try:
            fetched = _fetch_url_content(url)
            if not fetched or not fetched.strip():
                results.append({'url': url, 'ok': False, 'error': '页面无法访问'})
                continue
            title = _extract_title(url, fetched)
            chunks = _split_text(fetched)
            if not chunks:
                results.append({'url': url, 'ok': False, 'error': '无有效文本'})
                continue
            from backend.database import get_connection
            conn = get_connection()
            with conn:
                cur = conn.execute(
                    'INSERT INTO documents (kb_id, title, source_type, source_path, chunk_count) VALUES (?, ?, ?, ?, ?)',
                    (kb_id, title, 'web_search', url, len(chunks)),
                )
                doc_id = cur.lastrowid
                for i, chunk in enumerate(chunks):
                    conn.execute(
                        'INSERT INTO chunks (doc_id, kb_id, chunk_index, content) VALUES (?, ?, ?, ?)',
                        (doc_id, kb_id, i, chunk),
                    )
            conn.execute('UPDATE knowledge_bases SET updated_at = datetime("now","localtime") WHERE id = ?', (kb_id,))
            conn.commit()
            results.append({'url': url, 'ok': True, 'title': title, 'chunk_count': len(chunks)})
        except Exception as e:
            results.append({'url': url, 'ok': False, 'error': str(e)})
    return {'ok': True, 'results': results}


def _fetch_url_content(url, timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    except Exception:
        return ''


def _extract_title(url, text):
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=6)
        soup = BeautifulSoup(resp.text, 'lxml')
        if soup.title and soup.title.string:
            return soup.title.string.strip()[:200]
    except Exception:
        pass
    first_line = text.split('\n')[0].strip()
    return first_line[:200] if first_line else url
