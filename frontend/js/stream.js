/**
 * LLM 流式输出（OpenAI 兼容 SSE）
 */
(function (global) {
  async function callLLMStream(messages, callbacks) {
    const { onDelta, onDone, onError } = callbacks || {};

    try {
      const { headers, body } = await global.AvgApiConfig.buildProxyRequest({
        messages,
        temperature: 0.7,
        max_tokens: 1024,
        stream: true,
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

      if (!response.body) {
        const data = await response.json();
        const content = data.choices?.[0]?.message?.content || '';
        if (onDelta) onDelta(content, content);
        if (onDone) onDone(content);
        return content;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const data = trimmed.slice(5).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const json = JSON.parse(data);
            const delta = json.choices?.[0]?.delta?.content;
            if (delta) {
              fullContent += delta;
              if (onDelta) onDelta(fullContent, delta);
            }
          } catch (_) {
            /* 忽略非 JSON 行 */
          }
        }
      }

      if (onDone) onDone(fullContent);
      return fullContent;
    } catch (err) {
      if (onError) onError(err);
      else throw err;
    }
  }

  global.AvgStream = { callLLMStream };
})(window);
