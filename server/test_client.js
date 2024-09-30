// udp_test.js
// This script sends test packets to all available destinations in a round-robin fashion

const dgram = require('dgram');

const {
    ProtocolPacket,
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
} = require('../common/packet');  // Import from packet.js

const client = dgram.createSocket('udp4');

// Function to generate random integers within a given range (min to max)
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Function to generate test cases
function generateTestCase() {
    const source_id = getRandomInt(0, 10);  // Range for source_id (0~10)
    const dest_id = getRandomInt(0, 10);    // Range for dest_id (0~10)
    const service_id = getRandomInt(0x0000, 0x0004);  // Range for service_id (0x0000 ~ 0x0004)
    const message_type = getRandomInt(0x0000, 0x0004);  // Range for message_type (0x0000 ~ 0x0004)
    const ift_id = getRandomInt(0x0000, 0x00ff);  // Range for ift_id (0x0000 ~ 0x00ff)
    const ift_type = getRandomInt(0x0000, 0x00ff);  // Range for ift_type (0x0000 ~ 0x00ff)

    // Generate random payload data
    const payload = {
        id: getRandomInt(1, 10),  // Range for id field in the payload (1~10)
        status: getRandomInt(0, 1),  // Additional status data
        result: getRandomInt(0, 1)  // Result indicating success/failure
    };

    return {
        source_id,
        dest_id,
        service_id,
        message_type,
        ift_id,
        ift_type,
        payload
    };
}


// Function to send test packets based on the test cases
function sendTestPacket(testCase) {

    // Create the test packet with IFT ID, IFT Type, and payload
    const testPacket = new ProtocolPacket(
        testCase.source_id,
        testCase.dest_id,
        testCase.service_id,
        testCase.message_type,
        testCase.ift_id,
        testCase.ift_type,
        0,  // data_length (automatically set)
        JSON.stringify(testCase.payload)  // payload data
    );

    const packedData = testPacket.pack();  // Assuming pack() method exists in ProtocolPacket
    console.log('sourceId:', testPacket.source_id, 'destId:', testPacket.dest_id, 'service_id:', testPacket.service_id, 'message_type:', testPacket.message_type);
    console.log(`IFT ID: ${testPacket.ift_id}, IFT Type: ${testPacket.ift_type}, data_length: ${testPacket.data_length}, Payload: ${JSON.stringify(testCase.payload)}`);
    
    // Print packed data in hex format
    console.log('packedData:', packedData.toString('hex'));

    client.send(packedData, CCU_PORT, CCU_IP_ADDR, (err) => {
        if (err) {
            console.error(`Failed to send message from ${testPacket.source_id} to ${testPacket.dest_id}:`, err);
        } else {
            console.log(`Packet sent from ${testPacket.source_id} to ${testPacket.dest_id}`);
        }
    });
}

// Function to run the test sequence for all test cases
function runTestSequence() {
    let packetCount = 0;
    const maxPackets = 10;  // Number of packets to generate

    function sendNextPacket() {
        if (packetCount >= maxPackets) {
            console.log("Completed sending all test packets.");
            return;
        }

        const testCase = generateTestCase();  // Generate a test case
        sendTestPacket(testCase);  // Send the packet

        packetCount++;
        setTimeout(sendNextPacket, 1000);  // Send the next packet every 1 second
    }

    sendNextPacket();
}

runTestSequence();

console.log('UDP test client started. Sending packets sequentially...');

// Keep the script running
process.on('SIGINT', () => {
    client.close();
    process.exit();
});
