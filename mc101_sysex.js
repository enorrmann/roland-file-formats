/**
 * MC101SysEx - Roland MC-101 System Exclusive Generator Library
 * Generates Roland RQ1 (Request Data) and DT1 (Set Data) SysEx strings.
 */
class MC101SysEx {
    /**
     * Calculates the Roland checksum for a given array of bytes.
     * @param {number[]} bytes Array of integer bytes (address + data/size)
     * @returns {number} The checksum byte
     */
    static calculateChecksum(bytes) {
        let sum = bytes.reduce((acc, val) => acc + val, 0);
        return (128 - (sum % 128)) % 128;
    }

    /**
     * Helper to convert an array of byte values (numbers) to a space-separated hex string.
     * @param {number[]} bytes Array of bytes
     * @returns {string} Hex string (e.g., "F0 41 10")
     */
    static bytesToHex(bytes) {
        return bytes.map(b => b.toString(16).toUpperCase().padStart(2, '0')).join(' ');
    }

    /**
     * Helper to parse a hex string into an array of byte numbers.
     * @param {string} hexStr Space-separated hex string (e.g., "32 11 20 00")
     * @returns {number[]} Array of bytes
     */
    static hexToBytes(hexStr) {
        if (!hexStr) return [];
        return hexStr.trim().split(/\s+/).map(h => parseInt(h, 16));
    }

    /**
     * Helper to convert an integer to a 4-byte Roland size array.
     * Format: 00 00 00 7F
     * @param {number} size
     * @returns {number[]} Array of 4 size bytes
     */
    static sizeTo4Bytes(size) {
        return [
            (size >> 21) & 0x7F,
            (size >> 14) & 0x7F,
            (size >> 7) & 0x7F,
            size & 0x7F
        ];
    }

    /**
     * Builds a complete SysEx string.
     * @param {number} command 0x11 for RQ1, 0x12 for DT1
     * @param {number[]} addressBytes 4-byte address array
     * @param {number[]} payloadBytes Size bytes (for RQ1) or Data bytes (for DT1)
     * @returns {string} The full SysEx string formatted as hex
     */
    static buildSysExString(command, addressBytes, payloadBytes) {
        const header = [0xF0, 0x41, 0x10, 0x00, 0x00, 0x00, 0x5E, command];
        const checksum = this.calculateChecksum([...addressBytes, ...payloadBytes]);
        const end = [0xF7];

        const fullMessage = [...header, ...addressBytes, ...payloadBytes, checksum, ...end];
        return this.bytesToHex(fullMessage);
    }

    /**
     * Generates an RQ1 Request Data SysEx string.
     * @param {string} addressHex 4-byte address (e.g., "32 11 20 00")
     * @param {number} size Integer size of data to request (e.g., 1)
     * @returns {string} Complete RQ1 SysEx string
     */
    static makeRQ1(addressHex, size = 1) {
        const addrBytes = this.hexToBytes(addressHex);
        const sizeBytes = this.sizeTo4Bytes(size);
        return this.buildSysExString(0x11, addrBytes, sizeBytes);
    }

    /**
     * Generates a DT1 Set Data SysEx string.
     * @param {string} addressHex 4-byte address (e.g., "32 11 20 00")
     * @param {string|number|number[]} data Data to set. Can be hex string ("7F"), integer (127), or byte array.
     * @returns {string} Complete DT1 SysEx string
     */
    static makeDT1(addressHex, data) {
        const addrBytes = this.hexToBytes(addressHex);
        let dataBytes = [];

        if (typeof data === 'string') {
            dataBytes = this.hexToBytes(data);
        } else if (Array.isArray(data)) {
            dataBytes = data;
        } else if (typeof data === 'number') {
            // Assuming a single byte if passed as a number. 
            // For multi-byte numbers, pass an array of bytes or a hex string.
            dataBytes = [data & 0x7F];
        }

        return this.buildSysExString(0x12, addrBytes, dataBytes);
    }

    // --- Parameter Specific Methods ---

    /**
     * Calculates the address for a specific Tone Track Partial parameter.
     * Tracks are 1-based (MC-101 has 4 tracks). Drum is Track 1, Tones usually 2-4.
     * Partial is 1-4.
     * @param {number} track Track number (1-4)
     * @param {number} partial Tone Partial number (1-4)
     * @param {number} paramOffset Parameter offset in decimal or hex
     * @returns {string} Hex address string
     */
    static getTonePartialAddress(track, partial, paramOffset) {
        // Base for track 1 is 0x32 0x10. Track 2 is 0x32 0x11, etc.
        const trackByte = 0x10 + (track - 1);

        // Tone part offsets start at 0x20 for Partial 1. 0x21 for Partial 2.
        // Env offsets might be 0x24, 0x28, 0x2C, but those are sub-structures of the partial
        // if addressing standard FANTOM manual: Tone Partial 1 = 00 20 00
        // So 32 <trackByte> <0x20 + partial-1> <paramOffset>
        const partialByte = 0x20 + (partial - 1);

        const bytes = [0x32, trackByte, partialByte, paramOffset];
        return this.bytesToHex(bytes);
    }

    /**
     * Generates an RQ1 query for a Tone Track Partial parameter.
     * @param {number} track Track number (1-4)
     * @param {number} partial Tone Partial number (1-4)
     * @param {number} paramOffset Offset byte of the parameter
     * @param {number} size Expected byte size to request (default 1)
     * @returns {string} SysEx String
     */
    static getToneParam(track, partial, paramOffset, size = 1) {
        const addr = this.getTonePartialAddress(track, partial, paramOffset);
        return this.makeRQ1(addr, size);
    }

    /**
     * Generates a DT1 set command for a Tone Track Partial parameter.
     * @param {number} track Track number (1-4)
     * @param {number} partial Tone Partial number (1-4)
     * @param {number} paramOffset Offset byte of the parameter
     * @param {number|number[]|string} data The data to set
     * @returns {string} SysEx String
     */
    static setToneParam(track, partial, paramOffset, data) {
        const addr = this.getTonePartialAddress(track, partial, paramOffset);
        return this.makeDT1(addr, data);
    }

    /**
     * Calculates the address for a specific Drum Track pad parameter.
     * Drum Kits are typically mapped to Track 1.
     * @param {number} track Track number (1-4, usually 1 for Drums)
     * @param {number} pad Pad/Clip number offset (e.g., 0 for Clip 1)
     * @param {number} paramOffset Parameter offset in decimal or hex
     * @returns {string} Hex address string
     */
    static getDrumPadAddress(track, pad, paramOffset) {
        // Base for track 1 is 0x32 0x10.
        const trackByte = 0x10 + (track - 1);

        // Drum Kit pads are offsets 0x00, 0x01, etc., if using clip addressing
        // Or key offsets depending on exact MC-101 firmware layout
        const bytes = [0x32, trackByte, pad, paramOffset];
        return this.bytesToHex(bytes);
    }

    /**
     * Generates an RQ1 query for a Drum Track Pad parameter.
     * @param {number} track Track number (1-4)
     * @param {number} pad Pad index offset
     * @param {number} paramOffset Offset byte of the parameter
     * @param {number} size Expected byte size to request (default 1)
     * @returns {string} SysEx String
     */
    static getDrumParam(track, pad, paramOffset, size = 1) {
        const addr = this.getDrumPadAddress(track, pad, paramOffset);
        return this.makeRQ1(addr, size);
    }

    /**
     * Generates a DT1 set command for a Drum Track Pad parameter.
     * @param {number} track Track number (1-4)
     * @param {number} pad Pad index offset
     * @param {number} paramOffset Offset byte of the parameter
     * @param {number|number[]|string} data The data to set
     * @returns {string} SysEx String
     */
    static setDrumParam(track, pad, paramOffset, data) {
        const addr = this.getDrumPadAddress(track, pad, paramOffset);
        return this.makeDT1(addr, data);
    }
}

// Export for Node environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MC101SysEx;
}
