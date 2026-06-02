/**
 * 初始剧情预载：角色设定页提前生成首段剧情，进入游戏后直接消费缓存。
 */
(function (global) {
  const STORAGE_KEY = 'avg_initial_story_preload';
  const PROMPT_VERSION = 1;

  function personalityLabel(key) {
    const map = {
      silent: '沉默寡言',
      cheerful: '活泼开朗',
      gentle: '温柔体贴',
      tsundere: '傲娇毒舌',
    };
    return map[key] || key || '温柔体贴';
  }

  function genderNarrativeHint(gender) {
    if (gender === '男') {
      return '主角为男性。NPC 的称谓、亲密边界、恋爱互动、身体动作和社会期待应按男性主角自然处理。';
    }
    if (gender === '女') {
      return '主角为女性。NPC 的称谓、亲密边界、恋爱互动、身体动作和社会期待应按女性主角自然处理。';
    }
    return '主角性别为其他/非固定。NPC 应使用中性称谓，避免默认套用男性或女性身体、身份与恋爱互动。';
  }

  function normalizeCharacter(template, character) {
    return {
      name: (character?.name || template?.defaultPlayerName || '你').trim(),
      gender: character?.gender || '其他',
      personalityText: (character?.personalityText || character?.personality || '').trim(),
      personality: character?.personality || 'gentle',
      background: (character?.background || '').trim(),
    };
  }

  function buildCharacterKey(templateId, character) {
    const keyPayload = {
      promptVersion: PROMPT_VERSION,
      templateId,
      name: character.name,
      gender: character.gender,
      personalityText: character.personalityText || character.personality || '',
      background: character.background || '',
    };
    return JSON.stringify(keyPayload);
  }

  function buildSystemPrompt(template, storyContent, character) {
    const playerAttrs = normalizeCharacter(template, character);
    const pers =
      playerAttrs.personalityText ||
      personalityLabel(playerAttrs.personality);
    const bgLine = playerAttrs.background
      ? '\n玩家背景：' + playerAttrs.background
      : '';
    const gender = playerAttrs.gender || '其他';

    return `你是 AI AVG 游戏引擎。你的角色是旁白 + 所有 NPC + 系统面板。

故事设定：
${storyContent}

玩家角色：${playerAttrs.name}，性别：${gender}，性格：${pers}${bgLine}
性别差异化规则：${genderNarrativeHint(gender)}

角色信息：
${template.charactersPrompt}

游戏规则：
1. 每次输出包含场景叙述（第二人称「你」）
2. 不要询问玩家名字或性格，直接开始故事
3. 故事从「${template.openingBeat}」切入——${playerAttrs.name}进入剧情
4. 场景标题用 ### 标记
5. **每次仅输出 3 个编号选项**：1.【…】2.【…】3.【…】，禁止第 4 个预设项，禁止 A/B/C 格式
6. ${template.styleHint}
7. 场景切换用 [SCENE: 场景ID]，支持：${template.sceneIdsPrompt}
8. **角色台词（必须，按剧情情绪填写）**：每一句对白单独一行
   格式：角色名 [MOOD: 情绪] [EXPR: 表情]「对白正文」
   - 根据当前剧情语义选择 MOOD 与 EXPR，二者应一致（例：诀别 → MOOD:sad EXPR:sad；调侃 → MOOD:warm EXPR:smile）
   - MOOD 驱动语音语气（VoxCPM2），EXPR 驱动立绘 PNG，须随情节变化，勿整段都用 neutral
   - MOOD 仅允许：neutral, warm, happy, sad, angry, cold, surprised, blush
   - EXPR 仅允许：default, smile, happy, sad, angry, blush, cold, surprised
9. 纯旁白叙述不写「」、不加 MOOD/EXPR；有「」对白则必须带标签`;
  }

  async function loadStoryMarkdown(templateId) {
    const rel = templateId + '/story/main.md';
    if (global.electronAPI?.fs?.read) {
      return global.electronAPI.fs.read(rel);
    }
    const res = await fetch('/templates/' + templateId + '/story/main.md');
    if (!res.ok) throw new Error('无法加载剧本：' + templateId);
    return res.text();
  }

  function readCached() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function saveCached(payload) {
    const store = readCached();
    const entries = store?.entries || {};
    entries[payload.key] = payload;

    const keys = Object.keys(entries).sort((a, b) => {
      return (entries[b].createdAt || 0) - (entries[a].createdAt || 0);
    });
    for (const staleKey of keys.slice(3)) {
      delete entries[staleKey];
    }

    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ entries }));
  }

  function getMatching(templateId, character) {
    const key = buildCharacterKey(templateId, character);
    const cached = readCached();
    const payload = cached?.entries?.[key] || (cached?.key === key ? cached : null);
    if (!payload?.response) return null;
    return payload;
  }

  function consumeMatching(templateId, character) {
    const key = buildCharacterKey(templateId, character);
    const cached = getMatching(templateId, character);
    if (!cached) return null;

    const store = readCached();
    if (store?.entries) {
      delete store.entries[key];
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
    return cached;
  }

  async function preloadInitialStory(template, character) {
    const normalized = normalizeCharacter(template, character);
    const key = buildCharacterKey(template.id, normalized);
    const existing = getMatching(template.id, normalized);
    if (existing) return existing;

    const storyContent = await loadStoryMarkdown(template.id);
    const messages = [
      { role: 'system', content: buildSystemPrompt(template, storyContent, normalized) },
      { role: 'user', content: '开始故事' },
    ];
    const response = await global.AvgApi.callLLM(messages, { maxTokens: 1024 });
    const payload = {
      key,
      templateId: template.id,
      character: normalized,
      messages,
      response,
      createdAt: Date.now(),
    };
    saveCached(payload);
    return payload;
  }

  global.AvgStoryPreload = {
    PROMPT_VERSION,
    normalizeCharacter,
    personalityLabel,
    genderNarrativeHint,
    buildCharacterKey,
    buildSystemPrompt,
    loadStoryMarkdown,
    preloadInitialStory,
    getMatching,
    consumeMatching,
  };
})(window);
