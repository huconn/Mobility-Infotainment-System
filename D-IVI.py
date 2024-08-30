import argparse
import threading
from logger import Logger 
from udpControl import UDP_Control
from tcpControl import TCP_Control
from packet import *

# Global variables
SYSTEM = 'D-IVI'
LOG_LEVEL = 'INFO'
PROTOCOL = 'UDP'
CCU_IP_ADDR = '127.0.0.1'
CCU_PORT = 5001
DIVI_IP_ADDR = '127.0.0.1'
DIVI_PORT = 5002
PIVI1_IP_ADDR = '127.0.0.1'
PIVI1_PORT = 5003
PIVI2_IP_ADDR = '127.0.0.1'
PIVI2_PORT = 5004


class D_IVI_Control:
    def __init__(self, logger, mode, protocol, **kwargs):
        self.logger = logger    
        self.mode = mode    
        self.protocol = protocol

        operation = "Init"

        if self.mode == 0:
            self.src_ip_addr = kwargs.get('src_ip_addr')
            self.src_port = kwargs.get('src_port')
            self.logger.message("INFO", operation, f"Source IP Address: {self.src_ip_addr}")
            self.logger.message("INFO", operation, f"Source Port: {self.src_port}")

            if self.protocol == 'TCP':
                self.tcpControl = TCP_Control(SYSTEM, self.src_ip_addr, self.src_port, self.logger)
                tcp_server_thread = threading.Thread(target=self.tcpControl.tcp_server, args=(self.process_message,))
                tcp_server_thread.start()

            if self.protocol == 'UDP':
                self.udpControl = UDP_Control(SYSTEM, self.src_ip_addr, self.src_port, self.logger)
                udp_server_thread = threading.Thread(target=self.udpControl.udp_server, args=(self.process_message,))
                udp_server_thread.start()

        self.dest_ip_addr = kwargs.get('dest_ip_addr')
        self.dest_port = kwargs.get('dest_port')
        self.source_id = kwargs.get('source_id')
        self.dest_id = kwargs.get('dest_id')
        self.service_id = kwargs.get('service_id')
        self.message_type = kwargs.get('message_type')
        self.ift_id = kwargs.get('ift_id')
        self.ift_type = kwargs.get('ift_type')
        self.send_data = kwargs.get('send_data')

        self.logger.message("INFO", operation, f"Dest IP Address: {self.dest_ip_addr}")
        self.logger.message("INFO", operation, f"Dest Port: {self.dest_port}")
        self.logger.message("INFO", operation, f"Source ID: {self.source_id}")
        self.logger.message("INFO", operation, f"Dest ID: {self.dest_id}")
        self.logger.message("INFO", operation, f"Service ID: {self.service_id}")
        self.logger.message("INFO", operation, f"Message Type: {self.message_type}")
        self.logger.message("INFO", operation, f"IFT ID: {self.ift_id}")
        self.logger.message("INFO", operation, f"IFT Type: {self.ift_type}")
        self.logger.message("INFO", operation, f"Data length: {len(self.send_data)}")
        self.logger.message("INFO", operation, f"Send Data: {self.send_data}")
    
        if self.mode == 1:
            # create packet and send
            packet = ProtocolPacket(self.source_id, self.dest_id, self.service_id, \
                                        self.message_type, self.ift_id, self.ift_type, len(self.send_data), self.send_data)
            self.packet_data = packet.pack()

            self.logger.message("INFO", "SEND", f"DEST:{self.dest_ip_addr}:{self.dest_port}-Packet:{self.packet_data}")    
            if self.protocol == 'TCP':
                UDP_Control.tcp_client(self, self.dest_ip_addr, self.dest_port, self.packet_data)
            elif self.protocol == 'UDP':
                UDP_Control.udp_client(self, self.dest_ip_addr, self.dest_port, self.packet_data)

    def process_message(self, received_data):
        # Unpacking the packet
        unpacked_packet = ProtocolPacket.unpack(received_data)
        source_id = unpacked_packet.source_id
        dest_id = unpacked_packet.dest_id

        service_id = unpacked_packet.service_id
        message_type = unpacked_packet.message_type
        ift_id = unpacked_packet.ift_id
        ift_type = unpacked_packet.ift_type
        data_length = unpacked_packet.data_length
        payload_data = unpacked_packet.payload_data
        operation = "Parse"

        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"Service ID: {service_id}")
        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"Message Type: {message_type}")
        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"IFT ID: {ift_id}")
        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"IFT Type: {ift_type}")
        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"Data Length: {data_length}")
        # self.logger.message("INFO", operation, f"SRC:{source_id}-DES:{dest_id}", f"Payload Data: {payload_data}")

        # Log the received message
        self.logger.message("INFO", operation, f"SRC:{SourceDestID(source_id)}({source_id}):DEST:{SourceDestID(dest_id)}({dest_id}):SID:{ServiceID(service_id)}({service_id})")

        message_type_enum = SERVICE_MESSAGE_TYPE_MAP.get(ServiceID(service_id))
        self.logger.message("INFO", operation, f"message_type : {message_type_enum(message_type)}({message_type})")

        ift_type_enum = IFT_TYPE_MAP.get(IFTID(ift_id))
        self.logger.message("INFO", operation, f"service_ift_id : {IFTID(ift_id).value}({ift_id})")
        self.logger.message("INFO", operation, f"service_ift_type : {ift_type_enum(ift_type)}({ift_type})")
        self.logger.message("INFO", operation, f"service_data_length : {data_length}")
        self.logger.message("INFO", operation, f"service_payload_data : {payload_data}")


        #process received message
        # 1. receive message from CCU
        # 2. process the message
        # 3. send message to P-IVI
        # 4. send message to CCU
        # check source id
        if source_id == SourceDestID.P_IVI_1.value:
            print("Received D-IVI Message")
            # check service id
            if service_id == ServiceID.P_IVI_CONTROL.value:
                print("Received P-IVI Control Message")
                # check message type
                if message_type == P_IVI_CONTROL_MESSAGE_TYPES.P_IVI_CONTROL_RESPONSE.value:
                    print("Received P-IVI Control Response")

                    self.logger.message("INFO", "SEND", f"Send P-IVI Control Response")
                    packet = ProtocolPacket(self.source_id, SourceDestID.CCU.value, service_id, message_type, ift_id, ift_type, data_length, payload_data)
                    self.packet_data = packet.pack()
                    self.udpControl.udp_client(CCU_IP_ADDR, CCU_PORT, self.packet_data)
                    self.logger.message("INFO", "SEND", f"packet : b{self.packet_data}")
        else:
            print("Received Unknown Message")
            self.logger.message("INFO", "RECV", f"Received Unknown Message")
            self.logger.message("INFO", "RECV", f"SRC:{source_id}-DES:{dest_id}:SID:{service_id}")
            self.logger.message("INFO", "RECV", f"message_type : {message_type_enum(message_type)}")
            self.logger.message("INFO", "RECV", f"service_ift_id : {IFTID(ift_id)}")
            self.logger.message("INFO", "RECV", f"service_ift_type : {ift_type_enum(ift_type)}")
            self.logger.message("INFO", "RECV", f"service_data_length : {data_length}")
            self.logger.message("INFO", "RECV", f"service_payload_data : {payload_data}")
            
def main(args):

    # Set logger
    logger = Logger(args.debug_level, SYSTEM, args.protocol, args.debug_devlop)
    logger.message("INFO", "Start", f"{SYSTEM} Control Service")

    if args.mode == 0:
        pIviControl = D_IVI_Control(logger, args.mode, args.protocol, src_ip_addr=args.src_ip_addr, src_port=args.src_port, \
                    dest_ip_addr=args.dest_ip_addr, dest_port=args.dest_port, source_id=args.source_id, dest_id=args.dest_id, \
                        service_id=args.service_id, message_type=args.message_type, ift_id=args.ift_id, ift_type=args.ift_type, \
                            send_data=args.send_data)
    elif args.mode == 1:
        pIviControl = D_IVI_Control(logger, args.mode, args.protocol, \
                    dest_ip_addr=args.dest_ip_addr, dest_port=args.dest_port, \
                        source_id=args.source_id, dest_id=args.dest_id, \
                            service_id=args.service_id, message_type=args.message_type,\
                                ift_id=args.ift_id, ift_type=args.ift_type, send_data=args.send_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{SYSTEM} Message Sender/Receiver")
    parser.add_argument('--mode', default=0, type=int, choices=[0, 1], help='0: Server mode, 1: Client mode')
    parser.add_argument('--protocol', default=PROTOCOL, help='Protocol (TCP or UDP)')
    parser.add_argument('--debug_level', default=LOG_LEVEL, help='Debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--debug_devlop', action='store_true')

    args, _ = parser.parse_known_args()
    if args.mode == 0:
        parser.add_argument('--src_ip_addr', default=DIVI_IP_ADDR, help='Src IP Address')
        parser.add_argument('--src_port', default=DIVI_PORT, help='Src Port')
    parser.add_argument('--dest_ip_addr', default=DIVI_IP_ADDR, help='Dest IP Address')
    parser.add_argument('--dest_port', default=DIVI_PORT, help='Dest Port')    
    parser.add_argument('--source_id', default=0x05, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Source ID')
    parser.add_argument('--dest_id', default=0x06, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Destination ID')
    parser.add_argument('--service_id', default=0x0002, choices=[service.value for service in ServiceID], help='Service ID')
    parser.add_argument('--message_type', default=0x0000, help='Message Type')
    parser.add_argument('--ift_id', default=0x0001, help='IFT ID')
    parser.add_argument('--ift_type', default=0x0001, help='IFT Type')
    parser.add_argument('--send_data', default=b"1234567890", help='Payload Data')
    parser.add_argument('--send_count', type=int, default=0, help='perioc test sending')

    # parser = argparse.ArgumentParser(description=f"{SYSTEM} TCP Message Sender/Receiver")
    # parser.add_argument('--protocol', default=PROTOCOL, help='Protocol (TCP or UDP)')
    # parser.add_argument('--src_ip_addr', default=DIVI_IP_ADDR, help='Src IP Address')
    # parser.add_argument('--src_port', default=DIVI_PORT, help='Src Port')
    # parser.add_argument('--dest_ip_addr', default=CCU_IP_ADDR, help='Dest IP Address')
    # parser.add_argument('--dest_port', default=CCU_PORT, help='Dest Port')    
    # parser.add_argument('--source_id', default=SourceDestID.D_IVI.label, choices=[source_id.label for source_id in SourceDestID], help='Source ID')    
    # parser.add_argument('--dest_id', default=SourceDestID.P_IVI_1.label, choices=[source_id.label for source_id in SourceDestID], help='Destination ID')
    # parser.add_argument('--service_id', default=ServiceID.D_IVI_CONTROL.label, choices=[service.label for service in ServiceID], help='Service ID')

    # # Add message type based on service ID
    # args, _ = parser.parse_known_args()
    # service_enum = next(service for service in ServiceID if service.label == args.service_id)
    # message_type_enum = SERVICE_MESSAGE_TYPE_MAP[service_enum]
    # parser.add_argument('--message_type', default=D_IVI_CONTROL_MESSAGE_TYPES.D_IVI_CONTROL_REQUEST.label, choices=[message_type.label for message_type in message_type_enum],  help='Message Type')

    # # Add IFT ID and IFT Type based on service ID
    # ift_id_enum = SERVICE_IFT_ID_MAP[service_enum]
    # first_ift_id_member = next(iter(ift_id_enum))
    # parser.add_argument('--ift_id', default=first_ift_id_member.label, choices=[ift_id.label for ift_id in ift_id_enum], help='IFT ID')

    # # Add IFT Type based on IFT ID
    # args, _ = parser.parse_known_args()
    # selected_ift_id = next(ift_id for ift_id in IFTID if ift_id.label == args.ift_id)
    # ift_type_enum = IFT_TYPE_MAP[selected_ift_id]
    # first_ift_type_member = next(iter(ift_type_enum))
    # parser.add_argument('--ift_type', default=first_ift_type_member.label, choices=[ift_type.label for ift_type in ift_type_enum], help='IFT Type')
    
    # parser.add_argument('--send_data', default=b"1234567890", help='Payload Data')
    # parser.add_argument('--send_count', type=int, default=0, help='perioc test sending')
    # parser.add_argument('--debug_level', default=LOG_LEVEL, help='Debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    # parser.add_argument('--debug_devlop', action='store_true')

    args = parser.parse_args()
    main(args)
    
# python3 D-IVI.py --dest_ip_addr='192.168.8.196' 
# python3 D-IVI.py --dest_ip_addr='192.168.10.103' --test_sending=10
# python3 D-IVI.py --test_sending=10