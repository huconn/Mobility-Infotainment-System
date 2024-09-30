// server.js
// This file sets up WebSocket and UDP servers, and handles message routing from WebSocket clients to UDP servers.

const WebSocket = require('ws');
const dgram = require('dgram');
const {
    ProtocolPacket,
    WS_PORT,
    CCU_IP_ADDR,
    CCU_PORT,
    targetMapping
} = require('../common/packet');  // Import from packet.js

// WebSocket server setup
const wss = new WebSocket.Server({ port: WS_PORT });

// UDP client setup (used to send messages)
const udpClientSocket = dgram.createSocket('udp4');

// UDP server setup (used to receive messages)
const udpServerSocket = dgram.createSocket('udp4');

// WebSocket connection handler
wss.on('connection', (ws) => {
    console.log('WebSocket client connected');

    // Handle messages from WebSocket clients
    ws.on('message', (message) => {
        console.log('Message received from WebSocket client:', message);

        if (Buffer.isBuffer(message)) {
            // Select UDP server based on dest_id (2nd byte)
            const destId = message.readUInt8(1);
            const target = targetMapping[destId];
            console.log('destId:', destId, 'Target.ip:', target.ip, 'Target.port:', target.port);

            if (target) {
                // Forward the binary data to the appropriate UDP server
                udpClientSocket.send(message, target.port, target.ip, (err) => {
                    if (err) {
                        console.error('Error sending UDP message:', err);
                    } else {
                        console.log(`Message sent to UDP server (${target.ip}:${target.port})`);
                    }
                });
            } else {
                console.error(`Unknown dest_id: ${destId}`);
            }
        } else {
            console.error('Received message is not in the expected binary format');
        }
    });
});

// UDP message receiver
udpServerSocket.on('message', (msg, rinfo) => {
  //console.log(`UDP Server received: ${msg} from ${rinfo.address}:${rinfo.port}`);
    console.log(`UDP Server received (hex): ${msg.toString('hex')} from ${rinfo.address}:${rinfo.port}`);
    console.log(`UDP Server received (binary): ${Array.from(msg).map(byte => byte.toString(2).padStart(8, '0')).join(' ')} from ${rinfo.address}:${rinfo.port}`);

    // Unpack the received message and convert to JSON format
    const jsonMessage = ProtocolPacket.unpack(msg);

    // Broadcast the JSON message to all connected WebSocket clients
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(jsonMessage);
        }
    });
});

// Set up UDP server to listen for incoming messages
udpServerSocket.bind(CCU_PORT, CCU_IP_ADDR, () => {
    console.log(`UDP server is listening on ${CCU_IP_ADDR}:${CCU_PORT}`);
});

// Log server information
console.log(`WebSocket server is running on port ${WS_PORT}`);
console.log(`UDP client is running on port ${WS_PORT + 1}`);