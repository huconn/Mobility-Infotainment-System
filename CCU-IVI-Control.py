import argparse
import threading
from logger import Logger 
from udpControl import UDP_Control
from tcpControl import TCP_Control
from packet import *


# Global variables
SYSTEM = 'CCU-IVI-CONTROL'
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

class CCU_IVI_Control:  
    def __init__(self, logger, mode, protocol, **kwargs):
        self.logger = logger    
        self.mode = mode    
        self.protocol = protocol

        operation = "Init"

        if self.mode == 0:
            self.src_ip_addr = kwargs.get('src_ip_addr')
            self.src_port = kwargs.get('src_port')
            self.divi_ip_addr = kwargs.get('divi_ip_addr')
            self.divi_port = kwargs.get('divi_port')
            self.pivi1_ip_addr = kwargs.get('pivi1_ip_addr')
            self.pivi1_port = kwargs.get('pivi1_port')
            self.pivi2_ip_addr = kwargs.get('pivi2_ip_addr')
            self.pivi2_port = kwargs.get('pivi2_port')

            # Start TCP server thread
            if self.protocol == 'TCP':
                self.tcpControl = TCP_Control(SYSTEM, self.src_ip_addr, self.src_port, self.logger)
                tcp_server_thread = threading.Thread(target=self.tcpControl.tcp_server, args=(self.process_message,))
                tcp_server_thread.start()

            # Start UDP server thread
            if self.protocol == 'UDP':
                self.udpControl = UDP_Control(SYSTEM, self.src_ip_addr, self.src_port, self.logger)
                udp_server_thread = threading.Thread(target=self.udpControl.udp_server, args=(self.process_message,))
                udp_server_thread.start()

            self.logger.message("INFO", operation, f"Source IP Address: {self.src_ip_addr}")
            self.logger.message("INFO", operation, f"Source Port: {self.src_port}")
            self.logger.message("INFO", operation, f"D-IVI IP Address: {self.divi_ip_addr}")
            self.logger.message("INFO", operation, f"D-IVI Port: {self.divi_port}")
            self.logger.message("INFO", operation, f"P-IVI1 IP Address: {self.pivi1_ip_addr}")
            self.logger.message("INFO", operation, f"P-IVI1 Port: {self.pivi1_port}")
            self.logger.message("INFO", operation, f"P-IVI2 IP Address: {self.pivi2_ip_addr}")
            self.logger.message("INFO", operation, f"P-IVI2 Port: {self.pivi2_port}")

        elif self.mode == 1 or self.mode == 2:
            self.divi_ip_addr = kwargs.get('divi_ip_addr')
            self.divi_port = kwargs.get('divi_port')
            self.source_id = kwargs.get('source_id')
            self.dest_id = kwargs.get('dest_id')
            self.service_id = kwargs.get('service_id')
            self.message_type = kwargs.get('message_type')
            self.ift_id = kwargs.get('ift_id')
            self.ift_type = kwargs.get('ift_type')
            self.send_data = kwargs.get('send_data')

            self.logger.message("INFO", operation, f"Dest IP Address: {self.divi_ip_addr}")
            self.logger.message("INFO", operation, f"Dest Port: {self.divi_port}")
            self.logger.message("INFO", operation, f"Source ID: {self.source_id}")
            self.logger.message("INFO", operation, f"Dest ID: {self.dest_id}")
            self.logger.message("INFO", operation, f"Service ID: {self.service_id}")
            self.logger.message("INFO", operation, f"Message Type: {self.message_type}")
            self.logger.message("INFO", operation, f"IFT ID: {self.ift_id}")
            self.logger.message("INFO", operation, f"IFT Type: {self.ift_type}")
            self.logger.message("INFO", operation, f"Send Data: b{self.send_data}")

            # create packet and send
            packet = ProtocolPacket(self.source_id, self.dest_id, self.service_id, \
                                        self.message_type, self.ift_id, self.ift_type, len(self.send_data), self.send_data)
            self.packet_data = packet.pack()

            self.logger.message("INFO", "SEND", f"DEST:{self.divi_ip_addr}:{self.divi_port}-Packet:{self.packet_data}")    
            if self.protocol == 'TCP':
                UDP_Control.tcp_client(self, self.divi_ip_addr, self.divi_port, self.packet_data)
            elif self.protocol == 'UDP':
                UDP_Control.udp_client(self, self.divi_ip_addr, self.divi_port, self.packet_data)

    # process received message
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
        operation = "process"

        # Log the received message
        self.logger.message("INFO", operation, f"SRC:{SourceDestID(source_id)}:DEST:{SourceDestID(dest_id)}:SID:{ServiceID(service_id)}")

        message_type_enum = SERVICE_MESSAGE_TYPE_MAP.get(ServiceID(service_id))
        self.logger.message("INFO", operation, f"message_type : {message_type_enum(message_type)}")

        ift_type_enum = IFT_TYPE_MAP.get(IFTID(ift_id))
        self.logger.message("INFO", operation, f"service_ift_id : {IFTID(ift_id)}")
        self.logger.message("INFO", operation, f"service_ift_type : {ift_type_enum(ift_type)}")
        self.logger.message("INFO", operation, f"service_data_length : {data_length}")
        self.logger.message("INFO", operation, f"service_payload_data : {payload_data}")
    
    # Send message
    def send_message(self):
        # create packet and send
        packet = ProtocolPacket(self.source_id, self.dest_id, self.service_id, \
                                    self.message_type, self.ift_id, self.ift_type, len(self.send_data), self.send_data)
        self.packet_data = packet.pack()

        self.logger.message("INFO", "SEND", f"DEST:{self.divi_ip_addr}:{self.divi_port}-Packet:{self.packet_data}")    
        if self.protocol == 'TCP':
            UDP_Control.tcp_client(self, self.divi_ip_addr, self.divi_port, self.packet_data)
        elif self.protocol == 'UDP':
            UDP_Control.udp_client(self, self.divi_ip_addr, self.divi_port, self.packet_data)

    # Test mode
    def test_mode(self):
        # Packet Format
            # 1)Source ID: 2)Dest ID: 3)Service ID: 4)Message Type: 5)IFT ID: 6)IFT Type: 7)Data Length: 8)Payload Data
        # Service ID
        for service_id in ServiceID:
            # Vehicle Information 
            self.logger.message("INFO", "SEND", f"=============================================================================")
            self.logger.message("INFO", "SEND", f"Service ID: {service_id}")
            self.logger.message("INFO", "SEND", f"=============================================================================")
            if service_id == ServiceID.VEHICLE_INFORMATION:
                # Source ID: CCU to D-IVI
                source_id = SourceDestID.CCU.value
                dest_id = SourceDestID.D_IVI.value
                service_id = service_id.value
                message_type = VEHICLE_MESSAGE_TYPES.LAST_VEHICLE_INFORMATION.value
                self.logger.message("INFO", "SEND", f"1) {VEHICLE_MESSAGE_TYPES.LAST_VEHICLE_INFORMATION.label}")
                self.logger.message("INFO", "SEND", f"source_id:{source_id}, dest_id:{dest_id}, service_id:{service_id}, message_type:{message_type}")

                packet = ProtocolPacket(source_id, dest_id, service_id, message_type)
                packet_data = packet.pack()
                UDP_Control.udp_client(self, DIVI_IP_ADDR, DIVI_PORT, packet_data)
                self.logger.message("INFO", "SEND", f"---------------------------------------------------------------------------------")
            # D-IVI Control
            elif service_id == ServiceID.D_IVI_CONTROL:
                source_id = SourceDestID.CCU.value
                dest_id = SourceDestID.D_IVI.value
                service_id_val = service_id.value
                message_type_enum = SERVICE_MESSAGE_TYPE_MAP.get(ServiceID(service_id))
                message_type = message_type_enum(0).value
                self.logger.message("INFO", "SEND", f"1) {message_type_enum(0).label}")
                if service_id in SERVICE_IFT_ID_MAP:
                    ift_id_list = SERVICE_IFT_ID_MAP[service_id]
                    for ift_id in ift_id_list:
                        ift_type_list = IFT_TYPE_MAP[IFTID(ift_id)]
                        self.logger.message("INFO", "SEND", f"2) {IFTID(ift_id).label}")
                        self.logger.message("INFO", "SEND", f"=============================================================================")

                        for ift_type in ift_type_list:
                            if (ift_id.value == 0x0001 and (ift_type.value == 0x0001 or ift_type.value == 0x0003 or ift_type.value == 0x0006)) or \
                               (ift_id.value == 0x0002 and (ift_type.value == 0x0001)) or \
                               (ift_id.value == 0x0003 and (ift_type.value == 0x0001 or ift_type.value == 0x0002 or ift_type.value == 0x0004)) or \
                               (ift_id.value == 0x0004 and (ift_type.value == 0x0001 or ift_type.value == 0x0002 or ift_type.value == 0x0004)) or \
                               (ift_id.value == 0x0005 and (ift_type.value == 0x0001)):
                                # Send D-IVI Control Request
                                self.logger.message("INFO", "SEND", f"3) {ift_type.label}")
                                self.logger.message("INFO", "SEND", f"source_id:{source_id}, dest_id:{dest_id}, service_id:{service_id_val}, message_type:{message_type}, ift_id:{ift_id.value}, ift_type:{ift_type.value}")
                                packet = ProtocolPacket(source_id, dest_id, service_id_val, message_type, ift_id.value, ift_type.value)
                                packet_data = packet.pack()
                                UDP_Control.udp_client(self, DIVI_IP_ADDR, DIVI_PORT, packet_data)
                                self.logger.message("INFO", "SEND", f"---------------------------------------------------------------------------------")
                            
            # P-IVI Control
            elif service_id == ServiceID.P_IVI_CONTROL:
                source_id = SourceDestID.CCU.value
                dest_id = SourceDestID.P_IVI_1.value
                service_id_val = service_id.value
                message_type_enum = SERVICE_MESSAGE_TYPE_MAP.get(ServiceID(service_id))
                message_type = message_type_enum(0).value
                self.logger.message("INFO", "SEND", f"1) {message_type_enum(0).label}")
                if service_id in SERVICE_IFT_ID_MAP:
                    ift_id_list = SERVICE_IFT_ID_MAP[service_id]
                    for ift_id in ift_id_list:
                        ift_type_list = IFT_TYPE_MAP[IFTID(ift_id)]
                        self.logger.message("INFO", "SEND", f"2) {IFTID(ift_id).label}")
                        self.logger.message("INFO", "SEND", f"=============================================================================")

                        for ift_type in ift_type_list:
                            # Send D-IVI Control Request
                            self.logger.message("INFO", "SEND", f"3) {ift_type.label}")
                            self.logger.message("INFO", "SEND", f"source_id:{source_id}, dest_id:{dest_id}, service_id:{service_id_val}, message_type:{message_type}, ift_id:{ift_id.value}, ift_type:{ift_type.value}")
                            packet = ProtocolPacket(source_id, dest_id, service_id_val, message_type, ift_id.value, ift_type.value)
                            packet_data = packet.pack()
                            UDP_Control.udp_client(self, PIVI1_IP_ADDR, PIVI1_PORT, packet_data)
                            self.logger.message("INFO", "SEND", f"---------------------------------------------------------------------------------")
           
            # OTT Control
            elif service_id == ServiceID.OTT_CONTROL:
                source_id = SourceDestID.CCU.value
                dest_id = SourceDestID.CLOUD.value
                service_id = service_id.value
                message_type_enum = SERVICE_MESSAGE_TYPE_MAP.get(ServiceID(service_id))
                message_type = OTT_LOGIN_MESSAGE_TYPES.OTT_LOGIN_REQUEST.value
                self.logger.message("INFO", "SEND", f"1) {OTT_LOGIN_MESSAGE_TYPES.OTT_LOGIN_REQUEST.label}")
                #print(f"source_id:{source_id}, dest_id:{dest_id}, service_id:{service_id}, message_type:{message_type}")

            # Blockchain Authentication
            elif service_id == ServiceID.BLOCKCHAIN_AUTHENTICATION:
                # Source ID: CCU to Cloud
                source_id = SourceDestID.CCU.value
                dest_id = SourceDestID.CLOUD.value
                service_id = service_id.value
                message_type = BLOCKCHAIN_MESSAGE_TYPES.BLOCKCHAIN_AUTHENTICATION_REQUEST.value
                self.logger.message("INFO", "SEND", f"1) {BLOCKCHAIN_MESSAGE_TYPES.BLOCKCHAIN_AUTHENTICATION_REQUEST.label}")
                #print(f"source_id:{source_id}, dest_id:{dest_id}, service_id:{service_id}, message_type:{message_type}")

def main(args):
    # Set logger
    logger = Logger(args.debug_level, SYSTEM, args.protocol, args.debug_devlop)
    logger.message("INFO", "Start", f"{SYSTEM} Control Service")

    if args.mode == 0:
        ccuIviControl = CCU_IVI_Control(logger, args.mode, args.protocol,
                    src_ip_addr=args.src_ip_addr, src_port=args.src_port,
                        divi_ip_addr=args.divi_ip_addr, divi_port=args.divi_port,
                            pivi1_ip_addr=args.pivi1_ip_addr, pivi1_port=args.pivi1_port,
                                pivi2_ip_addr=args.pivi2_ip_addr, pivi2_port=args.pivi2_port)
    elif args.mode == 1 or args.mode == 2:
        ccuIviControl = CCU_IVI_Control(logger, args.mode, args.protocol,
                    divi_ip_addr=args.dest_ip_addr, divi_port=args.dest_port,
                        source_id=args.source_id, dest_id=args.dest_id,
                            service_id=args.service_id, message_type=args.message_type,
                                ift_id=args.ift_id, ift_type=args.ift_type, send_data=args.send_data)
        if args.mode == 2:
            ccuIviControl.test_mode()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CCU IVI Control Service')
    parser.add_argument('--mode', default=0, type=int, choices=[0, 1, 2], help='0: Server mode, 1: Client mode, 2: Test mode')
    parser.add_argument('--protocol', default=PROTOCOL, choices=['UDP', 'TCP'], help='Protocol (TCP or UDP)')
    parser.add_argument('--debug_level', default=LOG_LEVEL, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--debug_devlop', action='store_true')

    args, _ = parser.parse_known_args()
    if args.mode == 0:
        parser.add_argument('--src_ip_addr', default=CCU_IP_ADDR, help='Src IP Address')
        parser.add_argument('--src_port', default=CCU_PORT, help='Src Port')
        parser.add_argument('--divi_ip_addr', default=CCU_IP_ADDR, help='D-IVI IP Address')
        parser.add_argument('--divi_port', default=CCU_PORT, help='D-IVI Port')
        parser.add_argument('--pivi1_ip_addr', default=PIVI1_IP_ADDR, help='P-IVI IP Address')
        parser.add_argument('--pivi1_port', default=PIVI1_PORT, help='P-IVI1 Port')
        parser.add_argument('--pivi2_ip_addr', default=PIVI2_IP_ADDR, help='P-IVI IP Address')
        parser.add_argument('--pivi2_port', default=PIVI2_PORT, help='P-IVI2 Port') 
    elif args.mode == 1 or args.mode == 2:
        parser.add_argument('--dest_ip_addr', default=CCU_IP_ADDR, help='Dest IP Address')
        parser.add_argument('--dest_port', default=CCU_PORT, help='Dest Port')
        parser.add_argument('--source_id', default=0x00, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Source ID')
        parser.add_argument('--dest_id', default=0x00, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Destination ID')
        parser.add_argument('--service_id', default=0x0001, choices=[service.value for service in ServiceID], help='Service ID')
        parser.add_argument('--message_type', default=0x0000, help='Message Type')
        parser.add_argument('--ift_id', default=0x0001, help='IFT ID')
        parser.add_argument('--ift_type', default=0x0001, help='IFT Type')
        parser.add_argument('--send_data', default="", help='Payload Data')

    args = parser.parse_args()
    main(args)

# python3 CCU-IVI-Control.py  --divi_ip_addr='192.168.10.103' --pivi_ip_addr='192.168.10.103'