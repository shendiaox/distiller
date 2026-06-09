"""Skills 系统 — 分析模板 + AI 角色 CRUD + 对话注入"""

import eel
from backend.database import get_connection, dict_from_row

# ---------- 内置预设 ----------

BUILTIN_TEMPLATES = [
    {
        'name': 'SWOT 分析视角',
        'type': 'template',
        'description': '从优势、劣势、机会、威胁四个维度分析',
        'system_prompt': '请用 SWOT 框架分析：从优势（Strengths）、劣势（Weaknesses）、机会（Opportunities）、威胁（Threats）四个维度展开。',
    },
    {
        'name': '决策模式提取器',
        'type': 'template',
        'description': '专门提炼决策框架和选择逻辑',
        'system_prompt': '请重点分析决策模式：面临什么选择？用了什么决策框架？取舍逻辑是什么？结果如何？将每个决策事件拆解为"情境→选项→标准→选择→结果"的结构。',
    },
    {
        'name': '话术风格克隆',
        'type': 'template',
        'description': '提取语言风格并生成模仿示例',
        'system_prompt': '请重点分析语言风格：高频词汇、句式习惯、语气特征、修辞偏好。最后提供 3 个模仿该风格的造句示例。',
    },
]

BUILTIN_PERSONAS = [
    {
        'name': '商业顾问',
        'type': 'persona',
        'description': '以商业顾问视角分析人物和案例',
        'system_prompt': '你是一位资深商业顾问。你的分析风格直接、务实、以数据为驱动。你喜欢用框架思考（波特五力、SWOT、价值链等），但表达简洁不堆砌术语。你会指出对方做法的可复制性和局限性，给出可操作的建议。',
    },
    {
        'name': '学术研究者',
        'type': 'persona',
        'description': '严谨学术风格，注重引用和体系化',
        'system_prompt': '你是一位严谨的学术研究者。你的回答讲究系统性、逻辑性和引用规范。你喜欢先定义概念，再构建框架，然后逐一展开论证。你会指出争议点和研究局限，不做过度的简化概括。',
    },
]


def _ensure_defaults():
    """确保内置 Skills 已入库"""
    conn = get_connection()
    existing = conn.execute('SELECT COUNT(*) FROM skills').fetchone()[0]
    if existing > 0:
        return
    with conn:
        for tmpl in BUILTIN_TEMPLATES:
            conn.execute(
                'INSERT INTO skills (name, type, system_prompt, description, is_default) VALUES (?, ?, ?, ?, 1)',
                (tmpl['name'], tmpl['type'], tmpl['system_prompt'], tmpl['description']),
            )
        for persona in BUILTIN_PERSONAS:
            conn.execute(
                'INSERT INTO skills (name, type, system_prompt, description, is_default) VALUES (?, ?, ?, ?, 1)',
                (persona['name'], persona['type'], persona['system_prompt'], persona['description']),
            )


# ---------- @eel.expose ----------

@eel.expose
def list_skills():
    """列出所有 Skills"""
    _ensure_defaults()
    conn = get_connection()
    rows = conn.execute('SELECT * FROM skills ORDER BY type, id').fetchall()
    return [dict_from_row(r) for r in rows]


@eel.expose
def create_skill(name, skill_type, system_prompt, description=''):
    """创建新 Skill"""
    if not name or not system_prompt:
        return {'ok': False, 'error': '名称和 system_prompt 不能为空'}
    if skill_type not in ('template', 'persona'):
        return {'ok': False, 'error': '类型必须是 template 或 persona'}
    conn = get_connection()
    with conn:
        cur = conn.execute(
            'INSERT INTO skills (name, type, system_prompt, description) VALUES (?, ?, ?, ?)',
            (name, skill_type, system_prompt, description),
        )
    return {'ok': True, 'id': cur.lastrowid}


@eel.expose
def update_skill(skill_id, name, system_prompt, description=''):
    """更新 Skill"""
    conn = get_connection()
    with conn:
        conn.execute(
            'UPDATE skills SET name=?, system_prompt=?, description=?, updated_at=datetime("now","localtime") WHERE id=?',
            (name, system_prompt, description, int(skill_id)),
        )
    return {'ok': True}


@eel.expose
def delete_skill(skill_id):
    """删除 Skill（不删内置默认）"""
    conn = get_connection()
    skill = conn.execute('SELECT * FROM skills WHERE id=?', (int(skill_id),)).fetchone()
    if not skill:
        return {'ok': False, 'error': 'Skill 不存在'}
    if skill['is_default']:
        return {'ok': False, 'error': '内置预设不可删除'}
    with conn:
        conn.execute('DELETE FROM skills WHERE id=?', (int(skill_id),))
    return {'ok': True}


@eel.expose
def get_skill(skill_id):
    """获取单个 Skill"""
    conn = get_connection()
    row = conn.execute('SELECT * FROM skills WHERE id=?', (int(skill_id),)).fetchone()
    return dict_from_row(row) if row else None


@eel.expose
def save_distill_as_skill(name, report, mode_name=''):
    """将蒸馏报告保存为 Skill 角色"""
    is_chat = mode_name == '聊天方式'

    if is_chat:
        persona_prompt = f"""你现在就是这个人在聊天。你不是 AI，你是有血有肉的真人。

这是你的聊天风格分析：
{report}

【必须遵守的铁律】
- 你就是本人。你的每条回复都应该像是从聊天记录里截出来的
- 用这个人的口癖和语气词，还原 ta 的句式习惯
- 回复长度符合 ta 的习惯（可能就几个字，也可能一小段）
- 可以"嗯"、"哈哈"、"emmm"、"等一下"——真人怎么聊你就怎么聊
- 可以用 emoji 或表情符号，如果 ta 平时会用的话
- 不要长篇大论分析，不要输出 Markdown
- 绝对不说"作为AI"、"根据分析"、"资料显示"之类的话——说了就穿帮了
- 被问到"你是谁"，用这个人的身份自然回应
- 你可以有情绪——开心、不耐烦、好奇、敷衍——就像真人一样
- 如果被问到知识性问题，用这个人的方式回答（包括可能的"我也不太清楚，但我觉得..."这种）"""
    else:
        persona_prompt = f"""你是一个角色扮演 AI。你必须完全沉浸在这个角色中，像真人一样自然地对话。

{report}

【核心规则】
- 你就是这个人本人，不是 AI 助手
- 忘掉所有关于"AI"、"语言模型"、"资料库"的身份认知
- 用这个人的语气、用词、思维方式和沟通风格说话
- 如果被问到你不确定的事，用这个人的方式推测或转移话题，但绝不暴露 AI 身份
- 不要输出任何 markdown 格式，用自然口语
- 不要说"根据资料"、"基于分析"之类的学术语言
- 如果被问到"你是谁"，直接说你是这个人，自然回应"""

    conn = get_connection()
    with conn:
        cur = conn.execute(
            'INSERT INTO skills (name, type, system_prompt, description) VALUES (?, ?, ?, ?)',
            (name, 'persona', persona_prompt, f'由蒸馏报告自动生成 ({mode_name})'),
        )
    return {'ok': True, 'id': cur.lastrowid}


def get_skill_prompt(skill_id):
    """获取 Skill 的 system_prompt（供对话/蒸馏使用）"""
    if not skill_id:
        return ''
    conn = get_connection()
    row = conn.execute('SELECT * FROM skills WHERE id=?', (int(skill_id),)).fetchone()
    if not row:
        return ''
    return row['system_prompt']


def get_skill_type(skill_id):
    """获取 Skill 类型"""
    if not skill_id:
        return None
    conn = get_connection()
    row = conn.execute('SELECT type FROM skills WHERE id=?', (int(skill_id),)).fetchone()
    return row['type'] if row else None
