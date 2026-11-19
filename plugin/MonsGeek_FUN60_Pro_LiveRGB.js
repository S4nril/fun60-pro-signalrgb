/*
 * MonsGeek FUN60 Pro (device ID 2304) - experimental live RGB for SignalRGB
 *
 * STATUS: EXPERIMENTAL. Validated on real hardware by the maintainer on one keyboard (FUN60 Pro,
 * model 2304, firmware V309); not tested on anything else.
 *
 * This plugin only streams colors when the keyboard reports ALL of:
 *   - model ID 2304 (0x0900)
 *   - firmware version 0x0309
 *   - the live-mode marker "F6PK" in the identity reply (bytes 3-6 for the v1 image, bytes 9-12 for v2)
 * With the original firmware none of these live-mode conditions are met, so the plugin
 * refuses to stream and sends the keyboard nothing but read requests (identity 0x8F and
 * LED settings 0x87). It NEVER sends a color page with apply flag 1 (the flag the vendor
 * driver uses, which is a permanent save). Every streamed frame uses apply flag 2.
 *
 * Writes it can make to the keyboard (only on verified firmware):
 *   - one LED-settings write (cmd 0x07) to switch to mode 13 "User Picture", only if the
 *     keyboard is not already in that mode;
 *   - optionally one write on exit to restore the previous LED settings.
 *
 * Protocol (read from the vendor web driver and from captured USB traffic):
 *   feature report, report ID 0, 64 data bytes, interface 2
 *   color page : 0C 00 FF <page> <size> <flag> 00 <chk> <56 body bytes>
 *                chk = 0xFF - (sum of the first 7 bytes & 0xFF)
 *                pages 0..5 carry 56 bytes, page 6 carries 42 (378 = 126 slots x RGB)
 *   LED params : 07 <mode> <speedRaw> <brightness> <option> <R> <G> <B> <chk>
 *                chk (index 8) = 0xFF - (sum of the first 8 bytes & 0xFF)
 *   read cmds  : 8F (identity) / 87 (LED params) : <cmd> 00 00 00 00 00 00 <0xFF-cmd>
 *   slot index = column * 6 + row; Esc is slot 1 on the 60% layout
 */

export function Name() { return "MonsGeek FUN60 Pro (experimental live RGB)"; }
export function VendorId() { return 0x3151; }
export function ProductId() { return 0x502D; }
export function Publisher() { return "Community (experimental)"; }
export function Size() { return [15, 5]; }
export function DefaultPosition() { return [10, 100]; }
export function DefaultScale() { return 8.0; }

export function ControllableParameters() {
	return [
		{ "property": "LightingMode", "group": "lighting", "label": "Lighting Mode", "type": "combobox", "values": ["Canvas", "Forced"], "default": "Canvas" },
		{ "property": "forcedColor", "group": "lighting", "label": "Forced Color", "min": "0", "max": "360", "type": "color", "default": "#009bde" },
		{ "property": "shutdownMode", "group": "lighting", "label": "On exit", "type": "combobox", "values": ["Leave as is", "Restore previous mode"], "default": "Leave as is" },
		{ "property": "frameIntervalMs", "group": "lighting", "label": "Frame interval (ms)", "step": "1", "type": "number", "min": "20", "max": "200", "default": "40" },
		{ "property": "debugSlot", "group": "debug", "label": "Debug: light only this LED slot (-1 = off)", "step": "1", "type": "number", "min": "-1", "max": "125", "default": "-1" },
	];
}

const MODEL_ID = 2304;            // 0x0900
const FW_VERSION = 0x0309;
const MARKER = [0x46, 0x36, 0x50, 0x4B]; // "F6PK"
const SLOT_COUNT = 126;
const STREAM_BYTES = SLOT_COUNT * 3;      // 378
const PAGE_BODY = 56;
const PAGE_COUNT = 7;
const FLAG_LIVE = 2;              // RAM-only apply flag of the patched firmware (never 1)
const KEEPALIVE_MS = 500;

// [name, slot, x, y]  -- slot = column * 6 + row
// VERIFIED with USB captures of the vendor driver (22 keys):
//   Esc 1, 1 -> 7, Q 8, A 9, Left Shift 4, Z 16, Right Shift 76, Backspace 79, \ 80, Enter 81,
//   = 73, ] 74, ' 69, / 70, and the whole bottom row: Left Ctrl 5, Left Win 17, Left Alt 23,
//   Space 41, Right Alt 65, Fn 71, Menu 77, Right Ctrl 83.
// DERIVED (39 keys): each row's first and last letter keys are verified and the keys between them
//   occupy consecutive columns with no gap (12 keys for columns 1..12 on the number and Q rows,
//   11 for columns 1..11 on the A row, 10 for columns 2..11 on the Z row); Tab (2) and Caps (3)
//   are the two remaining slots of column 0. Not individually captured.
const vKeys = [
	// row 0
	["Esc", 1, 0, 0], ["1", 7, 1, 0], ["2", 13, 2, 0], ["3", 19, 3, 0], ["4", 25, 4, 0], ["5", 31, 5, 0],
	["6", 37, 6, 0], ["7", 43, 7, 0], ["8", 49, 8, 0], ["9", 55, 9, 0], ["0", 61, 10, 0], ["-", 67, 11, 0],
	["=", 73, 12, 0], ["Backspace", 79, 14, 0],
	// row 1
	["Tab", 2, 0, 1], ["Q", 8, 2, 1], ["W", 14, 3, 1], ["E", 20, 4, 1], ["R", 26, 5, 1], ["T", 32, 6, 1],
	["Y", 38, 7, 1], ["U", 44, 8, 1], ["I", 50, 9, 1], ["O", 56, 10, 1], ["P", 62, 11, 1], ["[", 68, 12, 1],
	["]", 74, 13, 1], ["\\", 80, 14, 1],
	// row 2
	["Caps Lock", 3, 0, 2], ["A", 9, 2, 2], ["S", 15, 3, 2], ["D", 21, 4, 2], ["F", 27, 5, 2], ["G", 33, 6, 2],
	["H", 39, 7, 2], ["J", 45, 8, 2], ["K", 51, 9, 2], ["L", 57, 10, 2], [";", 63, 11, 2], ["'", 69, 12, 2],
	["Enter", 81, 14, 2],
	// row 3
	["Left Shift", 4, 1, 3], ["Z", 16, 2, 3], ["X", 22, 3, 3], ["C", 28, 4, 3], ["V", 34, 5, 3], ["B", 40, 6, 3],
	["N", 46, 7, 3], ["M", 52, 8, 3], [",", 58, 9, 3], [".", 64, 10, 3], ["/", 70, 11, 3], ["Right Shift", 76, 13, 3],
	// row 4
	["Left Ctrl", 5, 0, 4], ["Left Win", 17, 1, 4], ["Left Alt", 23, 3, 4], ["Space", 41, 6, 4],
	["Right Alt", 65, 10, 4], ["Fn", 71, 11, 4], ["Menu", 77, 13, 4], ["Right Ctrl", 83, 14, 4],
];

const vLedNames = vKeys.map(k => k[0]);
const vLedPositions = vKeys.map(k => [k[2], k[3]]);

export function LedNames() { return vLedNames; }
export function LedPositions() { return vLedPositions; }

let streamingEnabled = false;
let savedLed = null;          // raw bytes 1..7 of the LED settings read at start
let changedMode = false;
let lastSend = 0;
let lastStream = null;

export function Validate(endpoint) {
	// vendor configuration interface (USB interface 2, usage page 0xFFFF)
	return endpoint.interface === 2 && endpoint.usage_page === 0xFFFF;
}

// ------------------------------------------------------------------ helpers

function hexToRgb(hex) {
	const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
	return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [0, 0, 0];
}

function pad65(bytes) {
	const p = new Array(65).fill(0);
	for (let i = 0; i < bytes.length; i++) { p[1 + i] = bytes[i]; } // p[0] = report ID 0
	return p;
}

function sendFeature(bytes) {
	device.send_report(pad65(bytes), 65);
}

// Read-type commands: <cmd> 00 00 00 00 00 00 <0xFF-cmd>, then GET_REPORT.
// Returns the reply as an array whose index 0 is the echoed command byte, or null.
function queryFeature(cmd) {
	sendFeature([cmd, 0, 0, 0, 0, 0, 0, (0xFF - cmd) & 0xFF]);
	device.pause(20);
	const resp = device.get_report(new Array(65).fill(0), 65);
	if (!resp || resp.length < 9) { return null; }
	if (resp[0] === cmd) { return resp.slice(0, 64); }
	if (resp[1] === cmd) { return resp.slice(1, 65); } // some stacks keep the report ID byte
	return null;
}

function checkIdentity(d) {
	if (!d) { return "no reply to the identity request"; }
	const model = d[1] | (d[2] << 8);
	const version = d[7] | (d[8] << 8);
	if (model !== MODEL_ID) { return "model ID is " + model + ", expected " + MODEL_ID; }
	if (version !== FW_VERSION) { return "firmware version is 0x" + version.toString(16) + ", expected 0x309"; }
	// v1 image: marker in identity bytes 3..6; v2 image: marker in bytes 9..12 (model bytes untouched)
	const hasMarker = (off) => MARKER.every((b, i) => d[off + i] === b);
	if (hasMarker(3) || hasMarker(9)) { return null; } // verified
	return "live-mode marker not present (original firmware)";
}

function setLedParams(mode, speedRaw, brightness, option, r, g, b) {
	const body = [0x07, mode, speedRaw, brightness, option, r, g, b];
	const sum = body.reduce((a, v) => a + v, 0) & 0xFF;
	sendFeature(body.concat([(0xFF - sum) & 0xFF]));
	device.pause(30);
}

export function buildPage(stream, page, flag) {
	const size = page === PAGE_COUNT - 1 ? STREAM_BYTES - PAGE_BODY * (PAGE_COUNT - 1) : PAGE_BODY; // 56 or 42
	const head = [0x0C, 0x00, 0xFF, page, size, flag, 0x00];
	const chk = (0xFF - (head.reduce((a, v) => a + v, 0) & 0xFF)) & 0xFF;
	const body = new Array(PAGE_BODY).fill(0);
	for (let i = 0; i < size; i++) { body[i] = stream[page * PAGE_BODY + i]; }
	return head.concat([chk], body); // 64 data bytes
}

function sendStream(stream) {
	for (let p = 0; p < PAGE_COUNT; p++) {
		const flag = p === PAGE_COUNT - 1 ? FLAG_LIVE : 0;
		sendFeature(buildPage(stream, p, flag));
	}
}

function composeStream() {
	const stream = new Array(STREAM_BYTES).fill(0);
	const dbg = parseInt(debugSlot);
	if (dbg >= 0 && dbg < SLOT_COUNT) {
		stream[dbg * 3] = 255; stream[dbg * 3 + 1] = 255; stream[dbg * 3 + 2] = 255;
		return stream;
	}
	for (let i = 0; i < vKeys.length; i++) {
		const slot = vKeys[i][1];
		let col;
		if (LightingMode === "Forced") { col = hexToRgb(forcedColor); }
		else { col = device.color(vKeys[i][2], vKeys[i][3]); }
		stream[slot * 3] = col[0]; stream[slot * 3 + 1] = col[1]; stream[slot * 3 + 2] = col[2];
	}
	return stream;
}

// ------------------------------------------------------------------ lifecycle

export function Initialize() {
	streamingEnabled = false; savedLed = null; changedMode = false; lastStream = null; lastSend = 0;

	const reason = checkIdentity(queryFeature(0x8F));
	if (reason) {
		device.log("FUN60 Pro: live mode NOT enabled: " + reason + ". Nothing will be streamed.");
		return;
	}

	const led = queryFeature(0x87);
	if (!led) { device.log("FUN60 Pro: could not read LED settings; not streaming."); return; }
	savedLed = led.slice(1, 8);

	if (led[1] !== 13) {
		// same write the vendor driver makes when "User Picture" is selected: mode 13, slot 1, fixed color 0/200/200
		setLedParams(13, 5, led[3], 0, 0, 200, 200);
		changedMode = true;
		const check = queryFeature(0x87);
		if (!check || check[1] !== 13) {
			device.log("FUN60 Pro: keyboard did not switch to mode 13; not streaming.");
			return;
		}
	}
	streamingEnabled = true;
	device.log("FUN60 Pro: patched firmware verified, live mode enabled.");
}

export function Render() {
	if (!streamingEnabled) { return; }
	const now = Date.now();
	const interval = Math.max(20, parseInt(frameIntervalMs) || 40);
	if (now - lastSend < interval) { return; }

	const stream = composeStream();
	const same = lastStream && stream.every((v, i) => v === lastStream[i]);
	if (same && now - lastSend < KEEPALIVE_MS) { return; }

	sendStream(stream);
	lastStream = stream;
	lastSend = now;
}

export function Shutdown(SystemSuspending) {
	if (streamingEnabled && changedMode && shutdownMode === "Restore previous mode" && savedLed) {
		setLedParams(savedLed[0], savedLed[1], savedLed[2], savedLed[3], savedLed[4], savedLed[5], savedLed[6]);
	}
	streamingEnabled = false;
}
