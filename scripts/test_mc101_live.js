/**
 * test_mc101_live.js
 * Tests the mc101_sysex.js library by sending real SysEx to the MC-101.
 * Prerequisites: MC-101 connected via USB MIDI, amidi available.
 * Usage: node scripts/test_mc101_live.js
 */
'use strict';

const MC101SysEx = require('../mc101_sysex.js');
const { spawnSync, execSync } = require('child_process');
const fs = require('fs');

const DEVICE = 'hw:3,0,0'; // MC-101 MIDI port
const TIMEOUT_SECS = 2;    // seconds to wait for response
const TMP_FILE = '/tmp/mc101_test_response.bin';

// ─── Helpers ────────────────────────────────────────────────────────────────

function toHex(bytes) {
    return Array.from(bytes).map(b => b.toString(16).toUpperCase().padStart(2, '0')).join(' ');
}

/**
 * Send a SysEx string via amidi (no response expected).
 */
function sendSysEx(sysexStr) {
    const result = spawnSync('amidi', ['-p', DEVICE, '-S', sysexStr]);
    if (result.status !== 0) {
        console.error('  ✗ amidi error:', result.stderr.toString());
        return false;
    }
    return true;
}

/**
 * Send a SysEx query and receive a response.
 * Returns Buffer with response bytes, or null on failure.
 */
function querySysEx(sysexStr) {
    if (fs.existsSync(TMP_FILE)) fs.unlinkSync(TMP_FILE);
    const result = spawnSync('amidi', [
        '-p', DEVICE,
        '-S', sysexStr,
        '-r', TMP_FILE,
        '-t', String(TIMEOUT_SECS)
    ]);
    const stderr = result.stderr ? result.stderr.toString() : '';
    if (result.status !== 0) {
        console.error('  ✗ amidi error:', stderr);
        return null;
    }
    if (!fs.existsSync(TMP_FILE)) {
        console.error('  ✗ No response file written');
        return null;
    }
    // amidi writes raw MIDI to stdout or -r file - filter out Active Sensing (FE) bytes
    const raw = fs.readFileSync(TMP_FILE);
    const filtered = Buffer.from(Array.from(raw).filter(b => b !== 0xFE));
    return filtered;
}

function sleep(ms) {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

// ─── Tests ───────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function test(name, fn) {
    console.log(`\n[TEST] ${name}`);
    try {
        const ok = fn();
        if (ok) { console.log('  ✓ PASS'); passed++; }
        else { console.log('  ✗ FAIL'); failed++; }
    } catch (e) {
        console.log('  ✗ ERROR:', e.message);
        failed++;
    }
}

// ─── 1. Library SysEx Generation ─────────────────────────────────────────────

test('Library: RQ1 System Common checksum', () => {
    const s = MC101SysEx.makeRQ1('00 00 00 00', 0x10);
    const expected = 'F0 41 10 00 00 00 5E 11 00 00 00 00 00 00 00 10 70 F7';
    console.log('  Generated:', s);
    console.log('  Expected: ', expected);
    return s === expected;
});

test('Library: DT1 Pan Hard Right Track2/Partial1', () => {
    const s = MC101SysEx.makeDT1('32 11 20 07', 0x7F);
    const expected = 'F0 41 10 00 00 00 5E 12 32 11 20 07 7F 17 F7';
    console.log('  Generated:', s);
    console.log('  Expected: ', expected);
    return s === expected;
});

test('Library: setToneParam(2,1,1,66) address and checksum', () => {
    const s = MC101SysEx.setToneParam(2, 1, 1, 66);
    // address: track2->0x11, partial1->0x20, offset 0x01 -> full addr 32 11 20 01
    // data: 66=0x42, checksum: (128 - (0x32+0x11+0x20+0x01+0x42) % 128) % 128
    const chk = (128 - ((0x32 + 0x11 + 0x20 + 0x01 + 0x42) % 128)) % 128;
    const expected = `F0 41 10 00 00 00 5E 12 32 11 20 01 42 ${chk.toString(16).toUpperCase().padStart(2, '0')} F7`;
    console.log('  Generated:', s);
    console.log('  Expected: ', expected);
    return s === expected;
});

test('Library: getToneParam (RQ1) Track2/Partial1/offset0', () => {
    const s = MC101SysEx.getToneParam(2, 1, 0, 1);
    // address: 32 11 20 00, size=1(0x01)
    // checksum: 128 - ((0x32+0x11+0x20+0x00+0x00+0x00+0x00+0x01) % 128) % 128
    const chk = (128 - ((0x32 + 0x11 + 0x20 + 0x00 + 0x00 + 0x00 + 0x00 + 0x01) % 128)) % 128;
    const expected = `F0 41 10 00 00 00 5E 11 32 11 20 00 00 00 00 01 ${chk.toString(16).toUpperCase().padStart(2, '0')} F7`;
    console.log('  Generated:', s);
    console.log('  Expected: ', expected);
    return s === expected;
});

// ─── 2. Live MC-101 RQ1 Tests ─────────────────────────────────────────────────

test('Live MC-101: RQ1 System Common responds', () => {
    const rq1 = MC101SysEx.makeRQ1('00 00 00 00', 0x10);
    console.log('  Sending:', rq1);
    const resp = querySysEx(rq1);
    if (!resp || resp.length === 0) { console.log('  No response!'); return false; }
    console.log('  Response:', toHex(resp));
    // Should start with F0 41 10 00 00 00 5E 12 and end with F7
    const ok = resp[0] === 0xF0 && resp[1] === 0x41 && resp[7] === 0x12 && resp[resp.length - 1] === 0xF7;
    if (!ok) console.log('  Wrong header/footer in response');
    return ok;
});

test('Live MC-101: RQ1 Drum Kit Track1 responds', () => {
    sleep(50);
    const rq1 = MC101SysEx.makeRQ1('32 10 00 00', 0x10);
    console.log('  Sending:', rq1);
    const resp = querySysEx(rq1);
    if (!resp || resp.length === 0) { console.log('  No response!'); return false; }
    console.log('  Response:', toHex(resp));
    return resp[0] === 0xF0 && resp[resp.length - 1] === 0xF7;
});

test('Live MC-101: RQ1 Tone Track2 responds', () => {
    sleep(50);
    const rq1 = MC101SysEx.makeRQ1('32 11 00 00', 0x10);
    console.log('  Sending:', rq1);
    const resp = querySysEx(rq1);
    if (!resp || resp.length === 0) { console.log('  No response!'); return false; }
    console.log('  Response:', toHex(resp));
    return resp[0] === 0xF0 && resp[resp.length - 1] === 0xF7;
});

test('Live MC-101: RQ1 Tone Track2 Partial1 responds', () => {
    sleep(50);
    const rq1 = MC101SysEx.makeRQ1('32 11 20 00', 0x10);
    console.log('  Sending:', rq1);
    const resp = querySysEx(rq1);
    if (!resp || resp.length === 0) { console.log('  No response!'); return false; }
    console.log('  Response:', toHex(resp));
    return resp[0] === 0xF0 && resp[resp.length - 1] === 0xF7;
});

// ─── 3. DT1 Write + Verify Round-Trip ────────────────────────────────────────

test('Live MC-101: DT1 set Pan + RQ1 verify round-trip (Track2 Partial1 Pan)', () => {
    sleep(50);
    // Set pan to hard right (0x7F)
    const dt1_right = MC101SysEx.makeDT1('32 11 20 07', 0x7F);
    console.log('  DT1 pan=0x7F (hard right):', dt1_right);
    let ok = sendSysEx(dt1_right);
    if (!ok) return false;
    sleep(100);

    // Query back
    const rq1 = MC101SysEx.makeRQ1('32 11 20 07', 1);
    console.log('  RQ1 query:', rq1);
    const resp1 = querySysEx(rq1);
    if (!resp1 || resp1.length === 0) { console.log('  No response after DT1!'); return false; }
    console.log('  Response:', toHex(resp1));

    // Set pan back to center (0x40)
    sleep(50);
    const dt1_center = MC101SysEx.makeDT1('32 11 20 07', 0x40);
    console.log('  DT1 pan=0x40 (center):', dt1_center);
    sendSysEx(dt1_center);
    sleep(100);

    const rq1_2 = MC101SysEx.makeRQ1('32 11 20 07', 1);
    const resp2 = querySysEx(rq1_2);
    if (!resp2 || resp2.length === 0) { console.log('  No response after second DT1!'); return false; }
    console.log('  Response:', toHex(resp2));

    // The data byte in DT1 response for single-byte query is at index 12
    // resp: F0 41 10 00 00 00 5E 12 [4 addr bytes] [data...] [checksum] F7
    //        0   1  2  3  4  5  6  7  8  9 10 11   12
    const dataByte1 = resp1[12];
    const dataByte2 = resp2[12];
    console.log(`  Pan after setting 0x7F: 0x${dataByte1 !== undefined ? dataByte1.toString(16).toUpperCase() : 'N/A'}`);
    console.log(`  Pan after setting 0x40: 0x${dataByte2 !== undefined ? dataByte2.toString(16).toUpperCase() : 'N/A'}`);

    return dataByte1 === 0x7F && dataByte2 === 0x40;
});

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════');
console.log(`RESULTS: ${passed} passed, ${failed} failed out of ${passed + failed} tests`);
console.log('══════════════════════════════════════');
