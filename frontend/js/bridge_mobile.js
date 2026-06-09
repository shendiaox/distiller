/* 移动版桥接 —— 用 fetch() 替换 Eel */

const API = '';

async function apiCall(method, url, body) {
    try {
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) opts.body = JSON.stringify(body);
        const resp = await fetch(API + url, opts);
        const data = await resp.json();
        if (data === undefined || data === null) return { ok: false, error: '后端无响应' };
        return data;
    } catch (err) {
        return { ok: false, error: err.message || String(err) };
    }
}

const Distiller = {
    hello: () => apiCall('GET', '/api/hello'),
    getConfig: () => apiCall('GET', '/api/get_config'),
    setApiKey: (key) => apiCall('POST', '/api/set_api_key', { key }),
    testConnection: () => apiCall('GET', '/api/test_api_connection'),
    sendMessage: (msg, history, kbId, skillId) =>
        apiCall('POST', '/api/send_message', { message: msg, history, kb_id: kbId, skill_id: skillId }),
    sendMessageStream: (msg, history, kbId, skillId) =>
        apiCall('POST', '/api/send_message_stream', { message: msg, history, kb_id: kbId, skill_id: skillId }),

    listKBs: () => apiCall('GET', '/api/list_knowledge_bases'),
    createKB: (name, desc) => apiCall('POST', '/api/create_knowledge_base', { name, description: desc }),
    renameKB: (kbId, name) => apiCall('POST', '/api/rename_knowledge_base', { kb_id: kbId, name }),
    deleteKB: (kbId) => apiCall('POST', '/api/delete_knowledge_base', { kb_id: kbId }),
    ingestText: (kbId, title, text) => apiCall('POST', '/api/ingest_text', { kb_id: kbId, title, text }),
    ingestFile: () => apiCall('GET', '/api/select_file_dialog'),
    selectFile: () => apiCall('GET', '/api/select_file_dialog'),
    searchKB: (kbId, query, k) => apiCall('GET', `/api/search_knowledge_base?kb_id=${kbId}&query=${encodeURIComponent(query)}&k=${k||5}`),
    getKBDocs: (kbId) => apiCall('GET', `/api/get_kb_documents?kb_id=${kbId}`),
    deleteDoc: (docId) => apiCall('POST', '/api/delete_document', { doc_id: docId }),
    getKBStats: (kbId) => apiCall('GET', `/api/get_kb_stats?kb_id=${kbId}`),

    getDistillModes: () => apiCall('GET', '/api/get_distillation_modes'),
    distill: (kbId, mode, instruction) =>
        apiCall('POST', '/api/distill', { kb_id: kbId, mode, instruction }),
    distillGenerate: (kbId, styleReport, request) =>
        apiCall('POST', '/api/distill_generate', { kb_id: kbId, style_report: styleReport, request }),

    webSearch: (query, max) =>
        apiCall('GET', `/api/web_search?query=${encodeURIComponent(query)}&max=${max||10}`),
    fetchAndIngest: (kbId, urls) =>
        apiCall('POST', '/api/fetch_and_ingest_urls', { kb_id: kbId, urls }),

    listSkills: () => apiCall('GET', '/api/list_skills'),
    createSkill: (name, type, prompt, desc) =>
        apiCall('POST', '/api/create_skill', { name, type, system_prompt: prompt, description: desc }),
    updateSkill: (id, name, prompt, desc) =>
        apiCall('POST', '/api/update_skill', { id, name, system_prompt: prompt, description: desc }),
    deleteSkill: (id) => apiCall('POST', '/api/delete_skill', { id }),
    getSkill: (id) => apiCall('GET', `/api/get_skill?id=${id}`),
    saveDistillAsSkill: (name, report, modeName) =>
        apiCall('POST', '/api/save_distill_as_skill', { name, report, mode_name: modeName }),

    getPersonaTemplate: () => apiCall('GET', '/api/get_persona_template'),
};
