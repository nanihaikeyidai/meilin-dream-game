/**
 * LLM 调用：Electron 直连 / 浏览器走 server 代理
 */
(function (global) {
  const { loadApiConfig, isConfigComplete, buildProxyRequest, getModel, DEFAULT_MODEL } =
    global.AvgApiConfig;

  async function callLLM(messages, options) {
    const temperature = options?.temperature ?? 0.7;
    const maxTokens = options?.maxTokens ?? 1024;

    if (global.electronAPI?.llm?.chat) {
      const config = await loadApiConfig();
      if (!isConfigComplete(config)) {
        throw new Error('请先配置 API（Base URL 与 API Key）');
      }
      return global.electronAPI.llm.chat(messages, {
        baseUrl: config.baseUrl,
        apiKey: config.apiKey,
        model: options?.model || getModel(config),
        temperature,
        maxTokens,
      });
    }

    const { headers, body } = await buildProxyRequest({
      messages,
      temperature,
      max_tokens: maxTokens,
      ...(options?.model ? { model: options.model } : {}),
    });

    const response = await fetch('/proxy/chat/completions', {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
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
