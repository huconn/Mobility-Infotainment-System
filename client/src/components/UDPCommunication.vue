<template>
  <div>
    <h2>UDP Communication</h2>
    <!-- Render buttons for each targetMapping and pass the corresponding id when clicked -->
    <button v-for="(target, id) in targetMapping" :key="id" @click="sendMessageTo(id)">
      Send to {{ getDestinationName(id) }}
    </button>
    <button @click="sendCustomMessage">Send Custom Message</button>
    <input v-model="customMessage" placeholder="Enter custom message" />
    <div v-if="receivedMessages.length > 0">
      <h3>Received Messages:</h3>
      <ul>
        <li v-for="(message, index) in receivedMessages" :key="index">
          {{ message }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { WS_IP_ADDR, WS_PORT, targetMapping, ProtocolPacket } from '../../../common/packet';
//import { WS_IP_ADDR, WS_PORT, targetMapping, ProtocolPacket } from '@common/packet';  // Assuming alias @common is set correctly

export default {
  name: 'UDPCommunication',
  data() {
    return {
      socket: null,
      receivedMessages: [],
      customMessage: '',
      targetMapping // Import targetMapping data
    };
  },
  methods: {
    initWebSocket() {
      //this.socket = new WebSocket(`ws://localhost:8080`);
      this.socket = new WebSocket(`ws://${WS_IP_ADDR}:${WS_PORT}`);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
      };
      this.socket.onmessage = (event) => {
        this.addReceivedMessage(event.data);
      };
      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
      };
    },
    addReceivedMessage(message) {
      if (this.receivedMessages.length >= 10) {
        this.receivedMessages.shift();
      }
      this.receivedMessages.push(message);
    },
    sendMessageTo(destId) {
      console.log("Destination ID:", destId);  // Check if destId is passed correctly

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const jsonPayload = {
          count: 7,
          request: 7,
          response: 7
        };

        // Create a message using ProtocolPacket
        const formattedMessage = new ProtocolPacket(
          0, // source_id (CCU ID)
          parseInt(destId), // dest_id
          0xffff, // service_id (Broadcast)
          0xffff, // message_type (Broadcast)
          0, // ift_id
          0, // ift_type
          0, // data_length (set in pack method)
          JSON.stringify(jsonPayload)
        );

        // Call createPacketBuffer method to create the packet
        const packetBuffer = formattedMessage.pack();

        // Send the packet via WebSocket
        this.socket.send(packetBuffer);
        console.log(`Formatted binary message sent to ${this.getDestinationName(destId)}:`, packetBuffer);
        console.log('JSON payload:', formattedMessage.payload_data);
      } else {
        console.error('WebSocket is not connected');
      }
    },
    sendCustomMessage() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(this.customMessage);
        console.log('Custom message sent:', this.customMessage);
      } else {
        console.error('WebSocket is not connected');
      }
    },
    getDestinationName(id) {
      const names = {
        5: 'DIVI',
        6: 'PIVI1',
        7: 'PIVI2',
        8: 'PIVI3',
        9: 'CLOUD',
        0: 'CCU',
        1: 'LTE',
        2: 'CAN',
        3: 'WAVE'
      };
      return names[id] || `Unknown (${id})`;
    },
  },
  mounted() {
    this.initWebSocket();
  },
  beforeUnmount() {
    if (this.socket) {
      this.socket.close();
    }
  }
};
</script>
