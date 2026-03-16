const MC101SysEx = require('./mc101_sysex');
const assert = require('assert');

// Test calculateChecksum
const bytes1 = [0x32, 0x11, 0x20, 0x07, 0x40];
assert.strictEqual(MC101SysEx.calculateChecksum(bytes1), 0x56, "Checksum Tone Pan to 64 failed");

const bytes2 = [0x32, 0x11, 0x20, 0x00, 0x00, 0x00, 0x00, 0x01]; // Address + Size
assert.strictEqual(MC101SysEx.calculateChecksum(bytes2), 0x1C, "Checksum Tone Level RQ1 failed");

// Test makeRQ1 (Tone Partial 1 Level, addr: 32 11 20 00, size: 1)
const rq1Level = MC101SysEx.makeRQ1("32 11 20 00", 1);
assert.strictEqual(rq1Level, "F0 41 10 00 00 00 5E 11 32 11 20 00 00 00 00 01 1C F7", "makeRQ1 failed for Tone Level");

// Test makeDT1 (Tone Partial 1 Pan Center = 64 / 0x40, addr: 32 11 20 07)
const dt1PanCenter = MC101SysEx.makeDT1("32 11 20 07", 64);
assert.strictEqual(dt1PanCenter, "F0 41 10 00 00 00 5E 12 32 11 20 07 40 56 F7", "makeDT1 failed for Tone Pan to Center");

const dt1PanCenterHex = MC101SysEx.makeDT1("32 11 20 07", "40");
assert.strictEqual(dt1PanCenterHex, "F0 41 10 00 00 00 5E 12 32 11 20 07 40 56 F7", "makeDT1 failed for Tone Pan to Center (Hex)");

// Test Tone partial offset math
const getToneLevel = MC101SysEx.getToneParam(2, 1, 0x00, 1);
assert.strictEqual(getToneLevel, "F0 41 10 00 00 00 5E 11 32 11 20 00 00 00 00 01 1C F7", "getToneParam Level failed");

const setTonePan = MC101SysEx.setToneParam(2, 1, 0x07, 64);
assert.strictEqual(setTonePan, "F0 41 10 00 00 00 5E 12 32 11 20 07 40 56 F7", "setToneParam Pan failed");

// Test Drum pad offset math
// Track 1 (Drums), Pad 0, Play Mode (offset 01)
const getDrumPlayMode = MC101SysEx.getDrumParam(1, 0, 0x01, 1);
assert.strictEqual(getDrumPlayMode, "F0 41 10 00 00 00 5E 11 32 10 00 01 00 00 00 01 3C F7", "getDrumParam Play Mode failed");

console.log("All tests passed!");
