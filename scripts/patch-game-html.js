const fs = require('fs');
const path = require('path');

const gamePath = path.join(__dirname, '..', 'frontend', 'game.html');
let html = fs.readFileSync(gamePath, 'utf8');

const marker = '<script>\n// ======================== 开始画面';
const start = html.indexOf(marker);
const end = html.indexOf('</script>\n</body>');

if (start < 0 || end < 0) {
  console.error('markers not found', { start, end });
  process.exit(1);
}

const insert = `<!-- 自定义确认框 -->
<div class="error-overlay" id="confirmOverlay">
  <div class="confirm-box">
    <div id="confirmMessage"></div>
    <div class="confirm-actions">
      <button type="button" class="btn-confirm" id="confirmCancel">取消</button>
      <button type="button" class="btn-confirm primary" id="confirmOk">确定</button>
    </div>
  </div>
</div>

<script src="js/template-registry.js"></script>
<script src="js/engine.js"></script>
<script src="js/api.js"></script>
<script src="js/tts.js"></script>
<script src="js/save.js"></script>
<script src="js/bootstrap.js"></script>
`;

html = html.slice(0, start) + insert + html.slice(end);
fs.writeFileSync(gamePath, html);
console.log('Patched game.html');
