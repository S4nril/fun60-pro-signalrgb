// Runs plugin/MonsGeek_FUN60_Pro_LiveRGB.js in a MOCK of the SignalRGB device API.
// Usage: node tests/test_plugin_sim.js        (needs Node.js, no packages)
// It checks the logic and the byte encoding. It does not prove the real SignalRGB API behaves the same.
const fs = require('fs'), path = require('path');
let src = fs.readFileSync(path.join(__dirname, '..', 'plugin', 'MonsGeek_FUN60_Pro_LiveRGB.js'), 'utf8')
  .replace(/^export function/gm, 'function');
src += '\n;globalThis.__p={Validate,Initialize,Render,Shutdown,buildPage,vKeys};';
let failed = 0;
const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) failed++; };
const hex = a => Buffer.from(a).toString('hex');

function makeDevice(identity, ledMode) {
  const log = [], sent = []; let last = null; const st = { mode: ledMode };
  const dev = {
    log: m => log.push(m), pause: () => {}, color: (x, y) => [(x * 16) & 255, (y * 50) & 255, 100],
    send_report: (p) => { sent.push(p.slice()); const c = p[1];
      if (c === 0x8F) last = identity.slice();
      else if (c === 0x87) last = [0x87, st.mode, 5, 3, 0, 255, 255, 255, 0];
      else if (c === 0x07) { st.mode = p[2]; st.set = p.slice(1, 10); } },
    get_report: () => { const r = new Array(64).fill(0); (last || []).forEach((v, i) => r[i] = v); return r; },
  };
  return { dev, log, sent, st };
}
function load(env) { Object.assign(globalThis, env); (0, eval)(src); return globalThis.__p; }
const defaults = { LightingMode: 'Canvas', forcedColor: '#ffffff', shutdownMode: 'Leave as is', frameIntervalMs: '20', debugSlot: '-1' };
const patchedId = [0x8f, 0x00, 0x09, 0x46, 0x36, 0x50, 0x4b, 0x09, 0x03];
const stockId = [0x8f, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x09, 0x03];

// original firmware: must refuse and send only the identity read
let m = makeDevice(stockId, 5); globalThis.device = m.dev; let P = load(defaults);
P.Initialize(); P.Render(); P.Render();
check(m.sent.every(p => p[1] === 0x8F) && /NOT enabled/.test(m.log[0]), 'original firmware: plugin refuses, only 0x8F is sent');
// right marker but wrong version
m = makeDevice([0x8f, 0, 9, 0x46, 0x36, 0x50, 0x4b, 0x0a, 0x03], 5); globalThis.device = m.dev; P = load(defaults); P.Initialize();
check(!m.sent.some(p => p[1] === 0x0c || p[1] === 0x07), 'wrong firmware version: refuses, no writes');
// wrong model
m = makeDevice([0x8f, 0x4d, 9, 0x46, 0x36, 0x50, 0x4b, 0x02, 0x03], 5); globalThis.device = m.dev; P = load(defaults); P.Initialize();
check(!m.sent.some(p => p[1] === 0x0c || p[1] === 0x07), 'wrong model (2381): refuses, no writes');
// patched firmware, keyboard in another mode
m = makeDevice(patchedId, 5); globalThis.device = m.dev; P = load({ ...defaults, shutdownMode: 'Restore previous mode' });
P.Initialize();
check(m.st.mode === 13 && hex(m.st.set) === '070d0503000 0c8c853'.replace(' ', ''), 'switches to mode 13 once with a valid checksum (07 0d 05 03 00 00 c8 c8 53)');
const before = m.sent.length; P.Render();
const pages = m.sent.slice(before).filter(p => p[1] === 0x0c);
check(pages.length === 7 && pages.map(p => p[6]).join() === '0,0,0,0,0,0,2', 'a frame = 7 pages, apply flag 2 only on the last page');
check(pages.every(p => p.length === 65 && p[8] === ((0xff - ((p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7]) & 255)) & 255)), 'every packet is 65 bytes with a correct checksum');
check(!pages.some(p => p[6] === 1), 'the permanent-save flag (1) is never sent');
P.Shutdown(false); check(m.st.mode === 5, 'Shutdown(Restore previous mode) restores the old mode');
// already in mode 13: no mode write
m = makeDevice(patchedId, 13); globalThis.device = m.dev; P = load(defaults); P.Initialize();
check(!m.sent.some(p => p[1] === 0x07), 'already in mode 13: no LED-settings write');
// encoder vs pages captured from the vendor driver (decoded from a USB capture)
const drv0 = '0c00ff00380000bc000000ff000000000000000000000000000000000000ff000000ffffffff0000000000000000000000000000000000000000000000000000';
const drv6 = '0c00ff062a0100c3' + '00'.repeat(56);
const stream = new Array(378).fill(0);
[[1, [255, 0, 0]], [7, [0, 255, 0]], [8, [0, 0, 255]], [9, [255, 255, 255]]].forEach(([s, c]) => c.forEach((v, i) => stream[s * 3 + i] = v));
check(hex(P.buildPage(stream, 0, 0)) === drv0, 'page 0 equals the vendor driver page 0');
check(hex(P.buildPage(stream, 6, 1)) === drv6, 'page 6 (flag 1) equals the vendor driver page 6');
const slots = P.vKeys.map(k => k[1]);
check(P.vKeys.length === 61 && new Set(slots).size === 61 && Math.max(...slots) < 126, '61 keys with unique slots inside 0..125');
// debug slot lights one slot
m = makeDevice(patchedId, 13); globalThis.device = m.dev; P = load({ ...defaults, debugSlot: '20' }); P.Initialize();
const b2 = m.sent.length; P.Render();
const pg = m.sent.slice(b2).filter(p => p[1] === 0x0c); const body = [].concat(...pg.map((p, i) => p.slice(9, 9 + (i === 6 ? 42 : 56))));
check(body.map((v, i) => v ? i : -1).filter(i => i >= 0).join() === '60,61,62', 'debug slot 20 lights only bytes 60..62');
console.log(failed ? '\n' + failed + ' FAILED' : '\nALL PLUGIN SIMULATION TESTS PASSED');
process.exit(failed ? 1 : 0);
