/**
 * 游戏主循环：模板加载、对话、选项、存档
 */
(function () {
  const { getTemplate } = window.AvgTemplates;
  const { createEngine, escapeHtml, splitIntoPages, renderPageText } = window.AvgEngine;
  const { callLLM } = window.AvgApi;
  const { saveApiConfig, loadApiConfig, isConfigComplete, resolveLlmSetup, testApiConfig, DEFAULT_MODEL } =
    window.AvgApiConfig;
  const { callLLMStream } = window.AvgStream;
  const { save: saveGame, load: loadGame } = window.AvgSave;

  let template = null;
  let engine = null;
  let tts = null;

  let playerAttrs = { name: '陈远', personality: 'gentle', personalityText: '' };
  let storyContent = '';

  const messages = [];
  let turnCount = 0;
  let currentPage = -1;
  let currentPages = [];
  let awaitingChoice = false;
  let isStreaming = false;
  let choiceActions = [];

  const bgImage = document.getElementById('bgImage');
  const spriteImage = document.getElementById('spriteImage');
  const textBody = document.getElementById('textBody');
  const textName = document.getElementById('textName');
  const textNext = document.getElementById('textNext');
  const choicesOverlay = document.getElementById('choicesOverlay');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const errorOverlay = document.getElementById('errorOverlay');
  const errorText = document.getElementById('errorText');
  const customInputInline = document.getElementById('customInputInline');
  const storyToast = document.getElementById('storyToast');
  let storyToastTimer = null;

  function showStoryToast(message) {
    if (!storyToast) return;
    storyToast.textContent = message;
    storyToast.classList.add('visible');
    clearTimeout(storyToastTimer);
    storyToastTimer = setTimeout(() => storyToast.classList.remove('visible'), 1800);
  }

  function formatConnectError(err) {
    const msg = err?.message || String(err);
    let extra = '';
    try {
      const jsonMatch = msg.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const body = JSON.parse(jsonMatch[0]);
        if (body.hint) extra = '。' + body.hint;
        else if (body.error === '上游服务不可达' || body.needsClientConfig) {
          extra = '。请点击「配置 API」填写 Base URL 与 API Key';
        }
      }
    } catch {
      /* ignore parse errors */
    }
    return '连接失败：' + msg + extra;
  }

  let apiConfigPromise = null;

  function fillApiConfigForm(config) {
    document.getElementById('cfgBaseUrl').value =
      config.baseUrl || 'https://api.deepseek.com/v1';
    document.getElementById('cfgApiKey').value = config.apiKey || '';
    document.getElementById('cfgModel').value = config.model || DEFAULT_MODEL;
  }

  function showApiConfigModal(existingConfig, options) {
    if (apiConfigPromise) return apiConfigPromise;
    const opts = options || {};
    const overlay = document.getElementById('apiConfigOverlay');
    const status = document.getElementById('apiConfigStatus');
    const saveBtn = document.getElementById('apiConfigSave');
    const cancelBtn = document.getElementById('apiConfigCancel');
    fillApiConfigForm(existingConfig || {});
    status.textContent = '';
    status.className = 'api-config-status';
    overlay.classList.add('visible');

    apiConfigPromise = new Promise((resolve) => {
      async function onSave() {
        const config = {
          baseUrl: document.getElementById('cfgBaseUrl').value.trim(),
          apiKey: document.getElementById('cfgApiKey').value.trim(),
          model: document.getElementById('cfgModel').value.trim(),
        };
        if (!isConfigComplete(config)) {
          status.textContent = '请填写 Base URL' + (config.baseUrl && !config.apiKey ? ' 与 API Key' : '');
          return;
        }
        saveBtn.disabled = true;
        status.textContent = '正在测试连接…';
        try {
          await saveApiConfig(config);
          if (!window.electronAPI?.llm?.chat) {
            await testApiConfig(config);
          }
          status.textContent = '保存成功';
          status.className = 'api-config-status ok';
          overlay.classList.remove('visible');
          cleanup(true);
        } catch (e) {
          status.textContent = e.message;
          status.className = 'api-config-status';
        } finally {
          saveBtn.disabled = false;
        }
      }

      function onCancel() {
        if (opts.required) {
          status.textContent = '需要配置 API 才能开始游戏';
          return;
        }
        overlay.classList.remove('visible');
        cleanup(false);
      }

      function cleanup(result) {
        saveBtn.onclick = null;
        cancelBtn.onclick = null;
        apiConfigPromise = null;
        resolve(result);
      }

      saveBtn.onclick = onSave;
      cancelBtn.onclick = onCancel;
    });

    return apiConfigPromise;
  }

  async function ensureApiConfig() {
    const setup = await resolveLlmSetup();
    if (setup.mode !== 'needs_config') return true;
    return showApiConfigModal(setup.config, { required: true });
  }

  window.openApiConfig = async function () {
    errorOverlay.classList.remove('visible');
    document.getElementById('settingsPanel')?.classList.remove('visible');
    const config = await loadApiConfig();
    return showApiConfigModal(config, { required: false });
  };

  function personalityLabel(key) {
    const map = {
      silent: '沉默寡言',
      cheerful: '活泼开朗',
      gentle: '温柔体贴',
      tsundere: '傲娇毒舌',
    };
    return map[key] || key;
  }

  async function loadStoryMarkdown(templateId) {
    const rel = templateId + '/story/main.md';
    if (window.electronAPI?.fs?.read) {
      return window.electronAPI.fs.read(rel);
    }
    const res = await fetch('/templates/' + templateId + '/story/main.md');
    if (!res.ok) throw new Error('无法加载剧本：' + templateId);
    return res.text();
  }

  async function resolveContext() {
    const params = new URLSearchParams(location.search);
    let templateId = params.get('template');

    const storedTpl = sessionStorage.getItem('selectedTemplate');
    const storedChar = sessionStorage.getItem('character');
    let fromFlow = false;

    if (storedTpl) {
      try {
        templateId = JSON.parse(storedTpl).id || templateId;
        fromFlow = true;
      } catch (_) {}
    }
    if (!templateId) templateId = 'changan-moon';

    const tpl = getTemplate(templateId);
    if (storedChar) {
      try {
        const c = JSON.parse(storedChar);
        playerAttrs.name = c.name || tpl.defaultPlayerName;
        playerAttrs.personalityText = c.personality || '';
        playerAttrs.gender = c.gender;
        playerAttrs.background = c.background || '';
        fromFlow = true;
      } catch (_) {}
    } else {
      playerAttrs.name = tpl.defaultPlayerName;
    }

    return { templateId, template: tpl, skipStart: fromFlow && !!storedChar };
  }

  function formatSaveTime(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  }

  function hasPlayableSave(data) {
    if (!data?.messages?.length) return false;
    if (data.messages.some((m) => m.role === 'assistant')) return true;
    return data.messages.some((m) => m.role === 'user' && m.content !== '开始故事');
  }

  function showContinuePrompt(data) {
    const block = document.getElementById('continueBlock');
    const meta = document.getElementById('continueMeta');
    const newBtn = document.getElementById('newStoryBtn');
    if (!block || !meta) return;

    const name = data.playerAttrs?.name || template?.defaultPlayerName || '旅人';
    const turn = data.turnCount || 0;
    const when = data.savedAt ? '存档于 ' + formatSaveTime(data.savedAt) : '';
    meta.textContent = name + ' · 已进行 ' + turn + ' 回合' + (when ? '\n' + when : '');
    block.classList.add('visible');
    const startBtn = document.getElementById('startStoryBtn');
    if (startBtn) startBtn.style.display = 'none';
    if (newBtn) newBtn.style.display = 'block';

    if (data.playerAttrs?.name) {
      const nameInput = document.getElementById('playerName');
      if (nameInput) nameInput.value = data.playerAttrs.name;
    }
    if (data.playerAttrs?.personality) {
      document.querySelectorAll('.pers-opt').forEach((el) => {
        el.classList.toggle('selected', el.dataset.val === data.playerAttrs.personality);
      });
      playerAttrs.personality = data.playerAttrs.personality;
    }
  }

  function enterGameScreen() {
    document.getElementById('startOverlay').style.display = 'none';
    document.getElementById('gameScreen').style.display = 'block';
    document.getElementById('menuBtn').classList.add('visible');
    document.getElementById('settingsBtn').classList.add('visible');
  }

  async function applySaveData(data) {
    Object.assign(playerAttrs, data.playerAttrs || {});
    messages.length = 0;
    (data.messages || []).forEach((m) => messages.push(m));
    turnCount = data.turnCount || 0;
    engine.setState(data.engineState);
    if (data.bgSrc) bgImage.src = data.bgSrc;

    const last = messages[messages.length - 1];
    if (last?.role === 'user') {
      awaitingChoice = false;
      await requestLLM();
      return;
    }

    const lastAssistant = messages.filter((m) => m.role === 'assistant').pop();
    if (lastAssistant) {
      const { pages } = splitIntoPages(lastAssistant.content, textBody);
      currentPages = pages;
      currentPage = typeof data.currentPage === 'number' ? data.currentPage : -1;
      awaitingChoice = !!data.awaitingChoice;
      if (awaitingChoice) showChoices();
      else if (pages.length) showPage(Math.max(0, currentPage));
      else showChoices();
    }
  }

  function applyStartScreen(tpl) {
    document.title = tpl.title + ' — AI Visual Novel';
    const sub = document.getElementById('startSub');
    const title = document.getElementById('startTitle');
    const desc = document.getElementById('startDesc');
    if (sub) sub.textContent = '—— ' + tpl.subtitle + ' ——';
    if (title) title.textContent = tpl.title;
    if (desc) desc.innerHTML = tpl.desc;
    const nameInput = document.getElementById('playerName');
    if (nameInput && !nameInput.value.trim()) nameInput.value = tpl.defaultPlayerName;
    if (tpl.defaultBg) bgImage.src = tpl.defaultBg;
  }

  function buildSystemPrompt() {
    const pers =
      playerAttrs.personalityText ||
      personalityLabel(playerAttrs.personality);
    const bgLine = playerAttrs.background
      ? '\n玩家背景：' + playerAttrs.background
      : '';

    return `你是 AI AVG 游戏引擎。你的角色是旁白 + 所有 NPC + 系统面板。

故事设定：
${storyContent}

玩家角色：${playerAttrs.name}，性格：${pers}${bgLine}

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

  function showTypingInDialog() {
    tts.stop();
    isStreaming = true;
    choicesOverlay.classList.remove('visible');
    customInputInline.classList.remove('visible');
    textNext.textContent = '';
    textBody.innerHTML =
      '<p class="typing-wait">正在落笔<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span></p>';
  }

  function finishAssistantResponse(response) {
    isStreaming = false;
    messages.push({ role: 'assistant', content: response });

    const { pages } = splitIntoPages(response, textBody);
    currentPages = pages;

    const sceneId = engine.detectScene(response);
    if (sceneId) engine.updateBg(bgImage, sceneId);
    engine.applyCharacterFromText(spriteImage, textName, response);

    if (pages.length === 0) showChoices();
    else showPage(0);
    autoSaveProgress();
  }

  async function requestLLM() {
    showTypingInDialog();
    try {
      await callLLMStream(messages, {
        onDone: (full) => {
          if (!full || !full.trim()) {
            return fallbackLLM();
          }
          finishAssistantResponse(full);
        },
        onError: () => fallbackLLM(),
      });
    } catch (e) {
      await fallbackLLM(e);
    }
  }

  async function fallbackLLM(prevErr) {
    try {
      const response = await callLLM(messages);
      finishAssistantResponse(response);
    } catch (e) {
      isStreaming = false;
      errorText.textContent = formatConnectError(prevErr || e);
      errorOverlay.classList.add('visible');
    }
  }

  window.selectPers = function (el) {
    document.querySelectorAll('.pers-opt').forEach((c) => c.classList.remove('selected'));
    el.classList.add('selected');
    playerAttrs.personality = el.dataset.val;
  };

  window.startGame = async function () {
    if (!(await ensureApiConfig())) return;

    const existing = loadGame(template.id, 'auto');
    if (hasPlayableSave(existing)) {
      const ok = await showConfirm('开始新故事将覆盖当前自动存档，确定吗？');
      if (!ok) return;
    }

    const name = document.getElementById('playerName').value.trim() || template.defaultPlayerName;
    playerAttrs.name = name;
    enterGameScreen();
    initGame();
  };

  window.continueSavedGame = async function () {
    if (!(await ensureApiConfig())) return;
    const data = loadGame(template.id, 'auto');
    if (!hasPlayableSave(data)) {
      showStoryToast('没有找到可继续的存档');
      return;
    }
    enterGameScreen();
    await applySaveData(data);
  };

  window.toggleMenu = function () {
    document.getElementById('menuPanel').classList.toggle('visible');
  };

  window.closeMenu = function () {
    document.getElementById('menuPanel').classList.remove('visible');
  };

  window.toggleSettings = function () {
    document.getElementById('settingsPanel').classList.toggle('visible');
  };

  window.showConfirm = function (message) {
    return new Promise((resolve) => {
      const overlay = document.getElementById('confirmOverlay');
      const msg = document.getElementById('confirmMessage');
      const ok = document.getElementById('confirmOk');
      const cancel = document.getElementById('confirmCancel');
      msg.textContent = message;
      overlay.classList.add('visible');

      function cleanup(result) {
        overlay.classList.remove('visible');
        ok.onclick = null;
        cancel.onclick = null;
        resolve(result);
      }

      ok.onclick = () => cleanup(true);
      cancel.onclick = () => cleanup(false);
    });
  };

  window.backToTitle = function () {
    closeMenu();
    document.getElementById('gameScreen').style.display = 'none';
    document.getElementById('startOverlay').style.display = 'flex';
    document.getElementById('menuBtn').classList.remove('visible');
    tts.stop();
  };

  window.restartGame = async function () {
    closeMenu();
    const ok = await showConfirm('确定重新开始？当前进度将丢失。');
    if (ok) location.reload();
  };

  window.showAbout = function () {
    closeMenu();
    showConfirm(
      (template?.title || 'AVG梦工厂') +
        ' · AI 视觉小说\n\n提示词引擎 + Web 渲染\n模板：' +
        (template?.id || '')
    ).then(() => {});
  };

  window.saveProgress = function () {
    closeMenu();
    autoSaveProgress();
    showConfirm('进度已保存。').then(() => {});
  };

  function autoSaveProgress() {
    if (!template?.id || !engine) return;
    saveGame(template.id, 'auto', {
      templateId: template.id,
      playerAttrs: { ...playerAttrs },
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      turnCount,
      engineState: engine.getState(),
      bgSrc: bgImage.src,
      currentPage,
      awaitingChoice,
    });
  }

  window.loadProgress = async function () {
    closeMenu();
    const data = loadGame(template.id, 'auto');
    if (!hasPlayableSave(data)) {
      await showConfirm('没有找到存档。');
      return;
    }
    const ok = await showConfirm('加载存档将覆盖当前进度，继续？');
    if (!ok) return;

    enterGameScreen();
    await applySaveData(data);
  };

  function showPage(index) {
    tts.stop();

    const pages = currentPages;
    if (index < 0 || index >= pages.length) {
      showChoices();
      return;
    }

    awaitingChoice = false;
    const text = pages[index];

    const sceneId = engine.detectScene(text);
    if (sceneId) engine.updateBg(bgImage, sceneId);

    engine.applyCharacterFromText(spriteImage, textName, text);

    renderPageText(textBody, text);

    const isLast = index >= pages.length - 1;
    const hasMorePages = pages.length > 1 && !isLast;
    textNext.textContent = isLast ? '▼ 查看选择' : hasMorePages ? '▼ 点击继续（还有下文）' : '▼ 点击继续';
    currentPage = index;
    choicesOverlay.classList.remove('visible');
    customInputInline.classList.remove('visible');

    tts.play(turnCount, index, text);
    if (!isLast) tts.preloadNext(turnCount, index + 1, pages[index + 1]);
  }

  window.advancePage = function () {
    if (isStreaming) {
      showStoryToast('正在加载剧情');
      return;
    }
    if (awaitingChoice) return;
    if (customInputInline.classList.contains('visible')) return;
    tts.stop();
    const next = currentPage + 1;
    if (next >= currentPages.length) showChoices();
    else showPage(next);
  };

  function buildChoiceButton(labelHtml, index, onSelect, extraClass) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'choice-btn' + (extraClass ? ' ' + extraClass : '');
    btn.style.animationDelay = index * 90 + 'ms';
    btn.innerHTML = labelHtml;
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      onSelect();
    });
    return btn;
  }

  function showChoices() {
    tts.stop();
    awaitingChoice = true;
    choiceActions = [];
    textNext.textContent = '';
    choicesOverlay.classList.remove('visible');

    const lastMsg = messages.filter((m) => m.role === 'assistant').pop();
    if (!lastMsg) return;

    const options = [];
    for (const line of lastMsg.content.split('\n')) {
      const t = line.trim();
      if (/^[\dA-Za-z][.\)】）:]/.test(t) && !/^---/.test(t)) options.push(t);
    }

    choicesOverlay.innerHTML = '';
    if (options.length === 0) {
      const optText = '继续';
      choiceActions.push(() => selectChoice(optText));
      choicesOverlay.appendChild(
        buildChoiceButton(
          '<span class="choice-label"><span class="choice-num">1.</span>继续推进剧情</span><span class="choice-hint">继续</span>',
          0,
          () => selectChoice(optText)
        )
      );
    } else {
      options.slice(0, 3).forEach((opt, i) => {
        const display = opt.replace(/^[\dA-Za-z][.\)】）:]\s*/, '').trim();
        const hint = opt.match(/（(.+)）/);
        choiceActions.push(() => selectChoice(opt));
        choicesOverlay.appendChild(
          buildChoiceButton(
            '<span class="choice-label"><span class="choice-num">' +
              (i + 1) +
              '.</span>' +
              escapeHtml(display) +
              '</span>' +
              (hint ? '<span class="choice-hint">' + escapeHtml(hint[1]) + '</span>' : ''),
            i,
            () => selectChoice(opt)
          )
        );
      });
    }

    const freeIdx = Math.min(options.length, 3) || 1;
    choicesOverlay.appendChild(
      buildChoiceButton(
        '<span class="choice-label">✎ 自由输入</span><span class="choice-hint">自己输入对话或行动</span>',
        freeIdx,
        () => openCustomInput(),
        'choice-btn-free'
      )
    );
    choicesOverlay.classList.add('visible');
  }

  window.selectChoice = function (text) {
    choiceActions = [];
    choicesOverlay.classList.remove('visible');
    awaitingChoice = false;
    sendMessage(text);
  };

  window.openCustomInput = function () {
    choiceActions = [];
    choicesOverlay.classList.remove('visible');
    customInputInline.classList.add('visible');
    document.getElementById('cipText').focus();
  };

  window.closeCustomInput = function () {
    customInputInline.classList.remove('visible');
    if (awaitingChoice) showChoices();
  };

  window.sendCustomInput = function () {
    const input = document.getElementById('cipText').value.trim();
    if (!input) return;
    customInputInline.classList.remove('visible');
    document.getElementById('cipText').value = '';
    sendMessage(input);
  };

  async function sendMessage(userText) {
    messages.push({ role: 'user', content: userText });
    turnCount++;
    autoSaveProgress();
    await requestLLM();
  }

  window.retryGame = function () {
    errorOverlay.classList.remove('visible');
    location.reload();
  };

  async function initGame() {
    messages.length = 0;
    turnCount = 0;
    currentPage = -1;
    currentPages = [];
    awaitingChoice = false;
    engine.setState({ currentCharName: null, currentCharId: null, currentExpression: 'default' });

    messages.push({ role: 'system', content: buildSystemPrompt() });
    messages.push({ role: 'user', content: '开始故事' });
    await requestLLM();
  }

  document.getElementById('playerName')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') startGame();
  });

  document.getElementById('cipText')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      sendCustomInput();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      closeCustomInput();
    }
  });

  document.querySelector('.text-window')?.addEventListener('click', (e) => {
    if (e.target.closest('.choices-panel')) return;
    if (e.target.closest('.custom-input-inline')) return;
    if (e.target.closest('button, textarea, input, a')) return;
    advancePage();
  });

  document.addEventListener('click', (e) => {
    const panel = document.getElementById('menuPanel');
    const btn = document.getElementById('menuBtn');
    if (panel?.classList.contains('visible') && !panel.contains(e.target) && !btn.contains(e.target)) {
      closeMenu();
    }
    const settingsPanel = document.getElementById('settingsPanel');
    const settingsBtn = document.getElementById('settingsBtn');
    if (
      settingsPanel?.classList.contains('visible') &&
      !settingsPanel.contains(e.target) &&
      !settingsBtn.contains(e.target)
    ) {
      settingsPanel.classList.remove('visible');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (customInputInline.classList.contains('visible')) {
        closeCustomInput();
        return;
      }
      const menu = document.getElementById('menuPanel');
      if (menu.classList.contains('visible')) {
        closeMenu();
        return;
      }
      const confirm = document.getElementById('confirmOverlay');
      if (confirm?.classList.contains('visible')) return;
      const apiCfg = document.getElementById('apiConfigOverlay');
      if (apiCfg?.classList.contains('visible')) return;
    }
    if (choicesOverlay.classList.contains('visible') && awaitingChoice) {
      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= 3 && choiceActions[num - 1]) {
        e.preventDefault();
        choiceActions[num - 1]();
        return;
      }
    }
    if (['Enter', ' ', 'ArrowDown', 'ArrowRight'].includes(e.key)) {
      e.preventDefault();
      if (errorOverlay.classList.contains('visible')) return;
      if (choicesOverlay.classList.contains('visible')) return;
      if (document.getElementById('confirmOverlay')?.classList.contains('visible')) return;
      advancePage();
    }
  });

  document.addEventListener('DOMContentLoaded', async () => {
    try {
      const ctx = await resolveContext();
      template = ctx.template;
      engine = createEngine(template);
      tts = window.AvgTts.createTts(template, template.portraits);
      tts.bindDom(
        document.getElementById('ttsPlayer'),
        document.getElementById('ttsIndicator')
      );
      tts.checkStatus();

      applyStartScreen(template);
      storyContent = await loadStoryMarkdown(ctx.templateId);
      document.getElementById('settingsBtn')?.classList.add('visible');

      const saved = loadGame(ctx.templateId, 'auto');
      if (hasPlayableSave(saved)) {
        showContinuePrompt(saved);
      }

      if (ctx.skipStart && !hasPlayableSave(saved)) {
        document.getElementById('startOverlay').style.display = 'none';
        document.getElementById('gameScreen').style.display = 'block';
        document.getElementById('menuBtn').classList.add('visible');
        if (await ensureApiConfig()) initGame();
      }
    } catch (e) {
      console.error(e);
      errorText.textContent = '初始化失败：' + e.message;
      errorOverlay.classList.add('visible');
    }
  });
})();
