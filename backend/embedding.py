"""文本检索 — 本地 TF-IDF（无需下载任何模型，纯 Python）"""

import threading
import re
from collections import Counter
from math import log

_stopwords = None
_lock = threading.Lock()


def _get_stopwords():
    """中文停用词（常见无意义词）"""
    global _stopwords
    if _stopwords is not None:
        return _stopwords
    with _lock:
        if _stopwords is not None:
            return _stopwords
        _stopwords = set('''
        的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你
        会 着 没有 看 好 自己 这 他 她 它 们 那 些 所 因为 所以 但是
        如果 虽然 可以 这个 那个 什么 怎么 怎样 哪 吗 呢 吧 啊 哦 嗯
        啦 哈 嘛 呀 哇 唉 而且 然后 虽然 不过 还是 只是 已经 比较
        非常 真的 太 好 大 小 多 少 之 被 把 从 对 与 或 等 其 以
        及 并 而 但 却 且 虽 然 若 则 因 故 所以 于是 然后 接着
        the a an is are was were be been being have has had having
        do does did doing will would shall should can could may might
        must i you he she it we they me him her us them my your his
        its our their this that these those what which who whom when
        where why how if then than too very just about also
        '''.split())
        return _stopwords


def _tokenize(text):
    """中文分词（简单 2-gram + 单字过滤）"""
    if not text:
        return []
    stopwords = _get_stopwords()
    # 清理文本
    text = re.sub(r'[^一-鿿\w]', ' ', text)
    # 提取中文 2-gram
    chars = re.findall(r'[一-鿿]', text)
    bigrams = [chars[i]+chars[i+1] for i in range(len(chars)-1) if chars[i] not in stopwords and chars[i+1] not in stopwords]
    # 提取英文词
    words = re.findall(r'[a-zA-Z]+', text.lower())
    tokens = [w for w in words if len(w) > 1 and w not in stopwords] + bigrams
    return tokens


def _compute_tfidf(documents, query_tokens):
    """计算 TF-IDF 分数"""
    N = len(documents)
    if N == 0:
        return []

    # 文档分词
    doc_tokens = [_tokenize(d) for d in documents]

    # 计算 IDF
    df = Counter()
    for tokens in doc_tokens:
        for t in set(tokens):
            df[t] += 1
    idf = {t: log((N + 1) / (df[t] + 1)) + 1 for t in df}

    # 计算 TF-IDF 分数
    scores = []
    for i, tokens in enumerate(doc_tokens):
        score = sum(idf.get(t, 0) * min(1, tokens.count(t) / max(len(tokens), 1)) for t in query_tokens if t in idf)
        scores.append((i, score))
    return scores


def search_tfidf(chunks, query, k=5):
    """TF-IDF 检索，返回 top-k 结果"""
    if not chunks:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    scores = _compute_tfidf(chunks, query_tokens)
    scores.sort(key=lambda x: x[1], reverse=True)
    return [{'index': i, 'score': s, 'content': chunks[i]} for i, s in scores[:k] if s > 0]


def get_embedding_dimension():
    return 1  # TF-IDF 不需要维度
