// packet.js

const { Buffer } = require('buffer');

// Constants
const WS_IP_ADDR = '127.0.0.1';
const WS_PORT = 8080;

const CCU_IP_ADDR = '127.0.0.1';
const CCU_PORT = 5001;
const DIVI_IP_ADDR = '127.0.0.1';
const DIVI_PORT = 5002;
const PIVI1_IP_ADDR = '127.0.0.1';
const PIVI1_PORT = 5003;
const PIVI2_IP_ADDR = '127.0.0.1';
const PIVI2_PORT = 5004;
const PIVI3_IP_ADDR = '127.0.0.1';
const PIVI3_PORT = 5005;
const CLOUDE_IP_ADDR = '127.0.0.1';
const CLOUDE_PORT = 5006;

const LTE_IP_ADDR = '127.0.0.1';
const LTE_PORT = 5012;
const CAN_IP_ADDR = '127.0.0.1';
const CAN_PORT = 5013;
const WAVE_IP_ADDR = '127.0.0.1';
const WAVE_PORT = 5014;

// Mapping of destination IDs to IP addresses and ports
const targetMapping = {
    0: { ip: CCU_IP_ADDR, port: CCU_PORT },
    1: { ip: LTE_IP_ADDR, port: LTE_PORT },
    2: { ip: CAN_IP_ADDR, port: CAN_PORT },
    3: { ip: WAVE_IP_ADDR, port: WAVE_PORT },
    5: { ip: DIVI_IP_ADDR, port: DIVI_PORT },
    6: { ip: PIVI1_IP_ADDR, port: PIVI1_PORT },
    7: { ip: PIVI2_IP_ADDR, port: PIVI2_PORT },
    8: { ip: PIVI3_IP_ADDR, port: PIVI3_PORT },
    9: { ip: CLOUDE_IP_ADDR, port: CLOUDE_PORT }
};

class ProtocolPacket {
    constructor(source_id, dest_id, service_id, message_type, ift_id, ift_type, data_length, payload_data) {
        this.source_id = source_id;
        this.dest_id = dest_id;
        this.service_id = service_id;
        this.message_type = message_type;
        this.ift_id = ift_id;
        this.ift_type = ift_type;
        this.data_length = data_length;
        this.payload_data = payload_data;
    }
    
    // pack method to convert the packet to a binary format
    pack() {
        const buffer = new ArrayBuffer(12 + this.payload_data.length); // 12 bytes header + payload length
        const view = new DataView(buffer);

        // Set the fields in the buffer
        view.setUint8(0, this.source_id); // Source ID (1 byte)
        view.setUint8(1, this.dest_id);   // Dest ID (1 byte)
        view.setUint16(2, this.service_id, true); // Service ID (2 bytes, little-endian)
        view.setUint16(4, this.message_type, true); // Message Type (2 bytes, little-endian)
        view.setUint16(6, this.ift_id, true); // IFT ID (2 bytes, little-endian)
        view.setUint16(8, this.ift_type, true); // IFT Type (2 bytes, little-endian)
        view.setUint16(10, this.payload_data.length, true); // Data Length (2 bytes, little-endian)

        // Encode payload data (assuming it's a string)
        const encoder = new TextEncoder();
        const payloadBuffer = encoder.encode(this.payload_data);
        new Uint8Array(buffer, 12).set(payloadBuffer); // Add payload after 12 bytes

        return Buffer.from(buffer); // Return as Buffer for use in UDP client
    }

    static unpack(packet_data) {
        console.log('--- Received Packet Data ---');
        console.log('Full packet (hex):', packet_data.toString('hex'));
        console.log('Full packet (utf8):', packet_data.toString('utf8'));

        const header = packet_data.slice(0, 12);
        console.log('Header (hex):', header.toString('hex'));

        const source_id = packet_data.readUInt8(0);
        const dest_id = packet_data.readUInt8(1);
        // const service_id = packet_data.readUInt16BE(2);
        // const message_type = packet_data.readUInt16BE(4);
        // const ift_id = packet_data.readUInt16BE(6);
        // const ift_type = packet_data.readUInt16BE(8);
        // const data_length = packet_data.readUInt16BE(10);

        const service_id = packet_data.readUInt16LE(2);
        const message_type = packet_data.readUInt16LE(4);
        const ift_id = packet_data.readUInt16LE(6);
        const ift_type = packet_data.readUInt16LE(8); 
        const data_length = packet_data.readUInt16LE(10);

        console.log('Extracted header:', { 
            source_id, dest_id, service_id, message_type, 
            ift_id, ift_type, data_length 
        });

        const payload_data = packet_data.slice(12);
        console.log('Payload (hex):', payload_data.toString('hex'));
        console.log('Payload (utf8):', payload_data.toString('utf8'));

        let parsedPayload;
        try {
            const payloadString = payload_data.toString('utf8').trim();
            console.log('Trimmed payload string:', payloadString);

            // Check if it's in JSON format
            if (payloadString.startsWith('{') && payloadString.endsWith('}')) {
                parsedPayload = JSON.parse(payloadString);
                console.log('Payload parsed as JSON:', parsedPayload);
            } else {
                // If not JSON, treat as string
                parsedPayload = payloadString;
                console.log('Payload treated as string');
            }
        } catch (error) {
            console.error('Error processing payload:', error.message);
            // Use original string in case of error
            parsedPayload = payload_data.toString('utf8');
        }

        const packet = new ProtocolPacket(
            source_id, dest_id, service_id, message_type,
            ift_id, ift_type, data_length, parsedPayload
        );

        console.log('--- End of Packet Processing ---');

        return packet.toJSON();
    }

    toJSON() {
        const result = {
            source_id: this.source_id,
            dest_id: this.dest_id,
            service_id: this.service_id,
            message_type: this.message_type,
            ift_id: this.ift_id,
            ift_type: this.ift_type,
            data_length: this.data_length,
            payload_data: this.payload_data
        };

        console.log('toJSON result:', JSON.stringify(result, null, 2));

        return JSON.stringify(result);
    }
}

module.exports = {
    ProtocolPacket,
    WS_IP_ADDR,
    WS_PORT,
    CCU_IP_ADDR,
    CCU_PORT,
    DIVI_IP_ADDR,
    DIVI_PORT,
    PIVI1_IP_ADDR,
    PIVI1_PORT,
    PIVI2_IP_ADDR,
    PIVI2_PORT,
    PIVI3_IP_ADDR,
    PIVI3_PORT,
    CLOUDE_IP_ADDR,
    CLOUDE_PORT,
    LTE_IP_ADDR,
    LTE_PORT,
    CAN_IP_ADDR,
    CAN_PORT,
    WAVE_IP_ADDR,
    WAVE_PORT,
    targetMapping
};