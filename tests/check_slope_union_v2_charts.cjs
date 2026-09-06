// Tests generated chart JavaScript without claiming a real browser screenshot.
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const root = path.resolve(__dirname, '../artifacts/half_day_slope_union_v2/final');
for (const year of [2021, 2022, 2023, 2024, 2025]) {
  const code = fs.readFileSync(path.join(root, `trades_${year}.html`), 'utf8').split('<script>')[1].split('</script>')[0];
  const context = new Proxy({}, {
    get: (t, k) => t[k] ?? ((...args) => {
      for (const a of args) if (typeof a === 'number' && !Number.isFinite(a)) throw Error(`nonfinite ${k}`);
    }),
    set: (t, k, v) => (t[k] = v, true)
  });
  const elements = {
    chart: {clientWidth: 1200, getContext: () => context, addEventListener: () => {}, toDataURL: () => ''},
    trade: {value: '0', appendChild: () => {}}, date: {value: `${year}-09-01`}, info: {textContent: ''}
  };
  const sandbox = {
    document: {getElementById: k => elements[k], createElement: () => ({click: () => {}})},
    devicePixelRatio: 1, window: {}
  };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  vm.runInContext('goTrade();zoom(.5);zoom(2);goDate()', sandbox);
  if (elements.info.textContent.slice(0, 10) < elements.date.value) throw Error('date navigation');
  console.log(year, 'PASS: mock canvas, date, trade, zoom', elements.info.textContent);
}
