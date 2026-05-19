/**
 * 浏览器端存档（localStorage）
 */
(function (global) {
  const PREFIX = 'girlgame_save_';

  function slotKey(templateId, slot) {
    return PREFIX + templateId + '_' + (slot || 'auto');
  }

  function save(templateId, slot, payload) {
    const data = {
      version: 1,
      savedAt: new Date().toISOString(),
      ...payload,
    };
    localStorage.setItem(slotKey(templateId, slot), JSON.stringify(data));
    return data;
  }

  function load(templateId, slot) {
    const raw = localStorage.getItem(slotKey(templateId, slot));
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function hasSave(templateId, slot) {
    return !!localStorage.getItem(slotKey(templateId, slot));
  }

  global.AvgSave = { save, load, hasSave };
})(window);
