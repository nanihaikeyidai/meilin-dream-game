/**
 * LLM 调用：Electron 直连 / 浏览器走 server 代理
 */
(function (global) {
  const DEFAULT_MODEL = 'july';

  async function loadApiConfig() {
    if (global.electronAPI?.apiKey?.load) {
      return global.electronAPI.apiKey.load();
    }
    try {
      const raw = localStorage.getItem('girlgame_api_config');
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  async function callLLM(messages, options) {
    const model = options?.model || DEFAULT_MODEL;
    const temperature = options?.temperature ?? 0.7;
    const maxTokens = options?.maxTokens ?? 1024;

    if (global.electronAPI?.llm?.chat) {
      const config = await loadApiConfig();
      if (!config.baseUrl || !config.apiKey) {
        throw new Error('请先在设置页配置 API（Base URL 与 API Key）');
      }
      return global.electronAPI.llm.chat(messages, {
        baseUrl: config.baseUrl,
        apiKey: config.apiKey,
        model: config.model || model,
        temperature,
        maxTokens,
      });
    }

    const response = await fetch('/proxy/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(
        'API错误 ' + response.status + ': ' + (errText.length > 200 ? errText.slice(0, 200) : errText)
      );
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;
    if (!content) throw new Error('API返回为空');
    return content;
  }

  global.AvgApi = { callLLM, loadApiConfig, DEFAULT_MODEL };
})(window);
