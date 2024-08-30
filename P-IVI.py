import argparse
import threading
from logger import Logger 
from udpControl import UDP_Control
from tcpControl import TCP_Control
from packet import *

# Global variables
SYSTEM = 'P-IVI'
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

class P_IVI_Control:
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

        # 1 receive message from D-IVI
        # 2 Process the message
        # 3 Send message to D-IVI
        # 4 Send message to CCU

        # check source id
        if source_id == SourceDestID.D_IVI.value:
            print("Received D-IVI Message")
            # check service id
            if service_id == ServiceID.P_IVI_CONTROL.value:
                print("Received P-IVI Control Message")
                # check message type
                if message_type == P_IVI_CONTROL_MESSAGE_TYPES.P_IVI_CONTROL_REQUEST.value:
                    print("Received P-IVI Control Request")
                    # check ift id and ift type
                    ift_type_map = {
                        IFTID.IFT_12_01.value: {
                            IFT_12_01_Type.TYPE_0001.value: IFT_12_01_Type.TYPE_0002.value,
                            IFT_12_01_Type.TYPE_0003.value: IFT_12_01_Type.TYPE_0004.value,
                            IFT_12_01_Type.TYPE_0005.value: IFT_12_01_Type.TYPE_0006.value,
                        },
                        IFTID.IFT_12_02.value: {
                            IFT_12_02_Type.TYPE_0001.value: IFT_12_02_Type.TYPE_0002.value,
                            IFT_12_02_Type.TYPE_0003.value: IFT_12_02_Type.TYPE_0004.value,
                        },
                        IFTID.IFT_12_03.value: {
                            IFT_12_03_Type.TYPE_0001.value: IFT_12_03_Type.TYPE_0002.value,
                            IFT_12_03_Type.TYPE_0003.value: IFT_12_03_Type.TYPE_0004.value,
                            IFT_12_03_Type.TYPE_0005.value: IFT_12_03_Type.TYPE_0006.value,
                        },
                        IFTID.IFT_12_04.value: {
                            IFT_12_04_Type.TYPE_0001.value: IFT_12_04_Type.TYPE_0002.value,
                            IFT_12_04_Type.TYPE_0003.value: IFT_12_04_Type.TYPE_0004.value,
                            IFT_12_04_Type.TYPE_0005.value: IFT_12_04_Type.TYPE_0006.value,
                        },
                        IFTID.IFT_12_05.value: {
                            IFT_12_05_Type.TYPE_0001.value: IFT_12_05_Type.TYPE_0002.value,
                        }
                    }
                    message_type = P_IVI_CONTROL_MESSAGE_TYPES.P_IVI_CONTROL_RESPONSE.value
                                
                    if ift_id in ift_type_map:
                        if ift_type in ift_type_map[ift_id]:
                            self.ift_type = ift_type_map[ift_id][ift_type]
                            self.ift_id = ift_id
                            # create packet message
                            # Parse payload_data ?
                            self.logger.message("INFO", "SEND", f"Send P-IVI Control Response")
                            packet = ProtocolPacket(self.source_id, source_id, service_id, message_type, ift_id, ift_type, data_length, payload_data)
                            self.packet_data = packet.pack()
                            self.udpControl.udp_client(DIVI_IP_ADDR, DIVI_PORT, self.packet_data)
                            self.logger.message("INFO", "SEND", f"Packet : b{self.packet_data}")

                        else:
                            raise ValueError("IFT Type does not exist for the specified IFT ID.")
                    else:
                        raise ValueError("IFT ID does not exist.")

def main(args):

    # Set logger
    logger = Logger(args.debug_level, SYSTEM, args.protocol, args.debug_devlop)
    logger.message("INFO", "Start", f"{SYSTEM} Control Service")

    if args.mode == 0:
        pIviControl = P_IVI_Control(logger, args.mode, args.protocol, src_ip_addr=args.src_ip_addr, src_port=args.src_port, \
                    dest_ip_addr=args.dest_ip_addr, dest_port=args.dest_port, source_id=args.source_id, dest_id=args.dest_id, \
                        service_id=args.service_id, message_type=args.message_type, ift_id=args.ift_id, ift_type=args.ift_type, \
                            send_data=args.send_data)
    elif args.mode == 1:
        pIviControl = P_IVI_Control(logger, args.mode, args.protocol, \
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
        parser.add_argument('--src_ip_addr', default=PIVI1_IP_ADDR, help='Src IP Address')
        parser.add_argument('--src_port', default=PIVI1_PORT, help='Src Port')
    parser.add_argument('--dest_ip_addr', default=PIVI1_IP_ADDR, help='Dest IP Address')
    parser.add_argument('--dest_port', default=PIVI1_PORT, help='Dest Port')    
    parser.add_argument('--source_id', default=0x06, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Source ID')
    parser.add_argument('--dest_id', default=0x05, choices=['0x00: CCU', '0x05: D-IVI', '0x06: P-IVI1', '0x07: P-IVI2'], help='Destination ID')
    parser.add_argument('--service_id', default=0x0001, choices=[service.value for service in ServiceID], help='Service ID')
    parser.add_argument('--message_type', default=0x0000, help='Message Type')
    parser.add_argument('--ift_id', default=0x0001, help='IFT ID')
    parser.add_argument('--ift_type', default=0x0001, help='IFT Type')
    parser.add_argument('--send_data', default=b"0987654321", help='Payload Data')
    parser.add_argument('--send_count', type=int, default=0, help='perioc test sending')


    args = parser.parse_args()
    main(args)

# python3 P-IVI.py --dest_ip_addr='192.168.8.196'
# python3 P-IVI.py --dest_ip_addr='192.168.10.103' --test_sending=10
# python3 P-IVI.py --test_sending=10