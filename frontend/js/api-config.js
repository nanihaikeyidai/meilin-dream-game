/**
 * LLM API 配置：Electron 持久化 / 浏览器经 server 文件 + localStorage 备份
 */
(function (global) {
  const STORAGE_KEY = 'girlgame_api_config';
  const DEFAULT_MODEL = 'deepseek-v4-flash';

  function normalizeConfig(config) {
    return {
      baseUrl: (config?.baseUrl || '').trim(),
      apiKey: (config?.apiKey || '').trim(),
      model: (config?.model || DEFAULT_MODEL).trim(),
    };
  }

  function loadLocalConfig() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? normalizeConfig(JSON.parse(raw)) : {};
    } catch {
      return {};
    }
  }

  function saveLocalConfig(config) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeConfig(config)));
  }

  async function loadServerConfig() {
    const r = await fetch('/api/config', { method: 'GET' });
    if (!r.ok) throw new Error('load config ' + r.status);
    return normalizeConfig(await r.json());
  }

  async function saveServerConfig(config) {
    const payload = normalizeConfig(config);
    const r = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error('save config ' + r.status);
    return payload;
  }

  async function loadApiConfig() {
    if (global.electronAPI?.apiKey?.load) {
      return global.electronAPI.apiKey.load();
    }

    let serverConfig = {};
    try {
      serverConfig = await loadServerConfig();
      if (isConfigComplete(serverConfig)) {
        saveLocalConfig(serverConfig);
        return serverConfig;
      }
    } catch {
      /* dev server 未启动或无 /api/config 时走 localStorage */
    }

    const localConfig = loadLocalConfig();
    if (isConfigComplete(localConfig)) {
      try {
        await saveServerConfig(localConfig);
      } catch {
        /* ignore migration failure */
      }
      return localConfig;
    }

    return isConfigComplete(serverConfig) ? serverConfig : localConfig;
  }

  async function saveApiConfig(config) {
    const payload = normalizeConfig(config);
    if (global.electronAPI?.apiKey?.save) {
      return global.electronAPI.apiKey.save(payload);
    }

    saveLocalConfig(payload);
    try {
      await saveServerConfig(payload);
    } catch (err) {
      console.warn('[API Config] server save failed, kept in localStorage:', err.message || err);
    }
    return { success: true };
  }

  function isLocalBase(baseUrl) {
    try {
      const host = new URL(baseUrl).hostname;
      return host === 'localhost' || host === '127.0.0.1';
    } catch {
      return false;
    }
  }

  function isConfigComplete(config) {
    const baseUrl = config?.baseUrl?.trim();
    if (!baseUrl) return false;
    if (isLocalBase(baseUrl)) return true;
    return !!config?.apiKey?.trim();
  }

  function getModel(config) {
    return config?.model?.trim() || DEFAULT_MODEL;
  }

  function getProxyHeaders(config) {
    if (!config?.baseUrl?.trim()) return {};
    const headers = { 'X-LLM-Base': config.baseUrl.trim() };
    if (config.apiKey?.trim()) headers['X-LLM-Key'] = config.apiKey.trim();
    return headers;
  }

  async function fetchProxyHealth() {
    try {
      const r = await fetch('/proxy/health');
      return r.ok ? await r.json() : {};
    } catch {
      return {};
    }
  }

  async function resolveLlmSetup() {
    const health = await fetchProxyHealth();
    if (health.mockLlm || health.llmAuth) {
      return { mode: 'server', health, config: null };
    }
    const config = await loadApiConfig();
    if (isConfigComplete(config)) {
      return { mode: 'client', health, config };
    }
    return { mode: 'needs_config', health, config: config || {} };
  }

  async function buildProxyRequest(bodyFields) {
    const setup = await resolveLlmSetup();
    if (setup.mode === 'needs_config') {
      throw new Error('请先配置 API（Base URL 与 API Key）');
    }
    const headers = { 'Content-Type': 'application/json' };
    if (setup.mode === 'client') {
      Object.assign(headers, getProxyHeaders(setup.config));
    }
    const model = getModel(setup.config);
    return {
      headers,
      body: { model, ...bodyFields },
      setup,
    };
  }

  async function testApiConfig(config) {
    if (!isConfigComplete(config)) {
      throw new Error('请填写 Base URL' + (isLocalBase(config?.baseUrl || '') ? '' : ' 与 API Key'));
    }
    const headers = {
      'Content-Type': 'application/json',
      ...getProxyHeaders(config),
    };
    const response = await fetch('/proxy/chat/completions', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: getModel(config),
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 8,
        stream: false,
      }),
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error('连接测试失败 ' + response.status + ': ' + errText.slice(0, 160));
    }
    return true;
  }

  global.AvgApiConfig = {
    STORAGE_KEY,
    DEFAULT_MODEL,
    loadApiConfig,
    saveApiConfig,
    isConfigComplete,
    isLocalBase,
    getModel,
    getProxyHeaders,
    fetchProxyHealth,
    resolveLlmSetup,
    buildProxyRequest,
    testApiConfig,
  };
})(window);
