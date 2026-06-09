/* Eel 后端调用封装 */

// 统一错误处理包装
function safeCall(fn) {
    return async (...args) => {
        try {
            const result = await fn(...args);
            if (result === undefined || result === null) {
                return { ok: false, error: '后端无响应，请检查 Python 控制台是否有报错' };
            }
            return result;
        } catch (err) {
            const msg = err?.message || err?.toString() || '未知错误';
            return { ok: false, error: msg };
        }
    };
}

const Distiller = {
    hello: safeCall(() => eel.hello()()),
    getConfig: safeCall(() => eel.get_config()()),
    setApiKey: safeCall((key) => eel.set_api_key(key)()),
    testConnection: safeCall(() => eel.test_api_connection()()),
    sendMessage: safeCall((msg, history, kbId, skillId) => eel.send_message(msg, history, kbId, skillId)()),
    sendMessageStream: safeCall((msg, history, kbId, skillId) => eel.send_message_stream(msg, history, kbId, skillId)()),

    // 知识库
    listKBs: safeCall(() => eel.list_knowledge_bases()()),
    createKB: safeCall((name, desc) => eel.create_knowledge_base(name, desc)()),
    renameKB: safeCall((kbId, name) => eel.rename_knowledge_base(kbId, name)()),
    deleteKB: safeCall((kbId) => eel.delete_knowledge_base(kbId)()),
    ingestText: safeCall((kbId, title, text) => eel.ingest_text(kbId, title, text)()),
    ingestFile: safeCall((kbId, filepath, title) => eel.ingest_file(kbId, filepath, title)()),
    selectFile: safeCall(() => eel.select_file_dialog()()),
    searchKB: safeCall((kbId, query, k) => eel.search_knowledge_base(kbId, query, k)()),
    getKBDocs: safeCall((kbId) => eel.get_kb_documents(kbId)()),
    deleteDoc: safeCall((docId) => eel.delete_document(docId)()),
    getKBStats: safeCall((kbId) => eel.get_kb_stats(kbId)()),

    // 蒸馏
    getDistillModes: safeCall(() => eel.get_distillation_modes()()),
    distill: safeCall((kbId, mode, instruction) => eel.distill(kbId, mode, instruction)()),
    distillGenerate: safeCall((kbId, styleReport, request) => eel.distill_generate(kbId, styleReport, request)()),

    // 搜索
    webSearch: safeCall((query, max) => eel.web_search(query, max)()),
    fetchAndIngest: safeCall((kbId, urls) => eel.fetch_and_ingest_urls(kbId, urls)()),

    // Skills
    listSkills: safeCall(() => eel.list_skills()()),
    createSkill: safeCall((name, type, prompt, desc) => eel.create_skill(name, type, prompt, desc)()),
    updateSkill: safeCall((id, name, prompt, desc) => eel.update_skill(id, name, prompt, desc)()),
    deleteSkill: safeCall((id) => eel.delete_skill(id)()),
    getSkill: safeCall((id) => eel.get_skill(id)()),
    saveDistillAsSkill: safeCall((name, report, modeName) => eel.save_distill_as_skill(name, report, modeName)()),

    // 模板
    getPersonaTemplate: safeCall(() => eel.get_persona_template()()),
};
