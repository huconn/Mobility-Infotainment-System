import socket
import struct
import argparse
import threading
import time

PROTOCOL_LEN = 8
MAX_PAYLOAD_LEN = 65535


# MESSAGE TYPES
MESSAGE_TYPES_SERVICE_IDS = {
    'Last Vehicle Information': {
        'service_id': 0x0000,
        'message_type': 0x0000
    },
    'P-IVI Control Request': {
        'service_id': 0x0001,
        'message_type': 0x0000
    },
    'P-IVI Control Response': {
        'service_id': 0x0001,
        'message_type': 0x0001
    },
    'OTT Login Request': {
        'service_id': 0x0002,
        'message_type': 0x0000
    },
    'OTT Login Response': {
        'service_id': 0x0002,
        'message_type': 0x0001
    },
    'Blockchain Authentication Request': {
        'service_id': 0x0003,
        'message_type': 0x0000
    },
    'Blockchain Authentication Response': {
        'service_id': 0x0003,
        'message_type': 0x0001
    }
}

LAST_VEHICLE_MESSAGE_TYPES = {
    'Last Vehicle Information': 0x0000,
}

P_IVI_CONTROL_MESSAGE_TYPES = {
    'P-IVI Control Request': 0x0000,
    'P-IVI Control Response': 0x0001,
}

OTT_LOGIN_MESSAGE_TYPES = {
    'OTT Login Request': 0x0000,
    'OTT Login Response': 0x0001,
}

BLOCKCHAIN_MESSAGE_TYPES = {
    'Blockchain Authentication Request': 0x0000,
    'Blockchain Authentication Response': 0x0001
}

MESSAGE_TYPES = {
    'Last Vehicle Information': 0x0000,
    'P-IVI Control Request': 0x0000,
    'P-IVI Control Response': 0x0001,
    'OTT Login Request': 0x0000,
    'OTT Login Response': 0x0001,
    'Blockchain Authentication Request': 0x0000,
    'Blockchain Authentication Response': 0x0001
}

# Service ID
SERVICE_IDS = {
    'Vehicle Information': 0x0000,
    'P-IVI Control': 0x0001,
    'OTT': 0x0002,
    'Blockchain Authentication': 0x0003
}

# Source/Dest ID 
SOURCE_DEST_IDS = {
    'CCU': 0x00,
    'D-IVI': 0x05,
    'P-IVI1': 0x06,
    'P-IVI2': 0x07
}

udp_client_ip = None
tcp_client_ip = None

def log_message(protocol, direction, data, output_to_console=True, output_to_file=False):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')  
    message = f"[{timestamp}] {direction.upper()} {protocol} : {data}"

    if output_to_console:
        print(message)

    if output_to_file:
        filename = f"{protocol}_logs_{timestamp}.txt"
        with open(filename, "a") as f:
            f.write(message)

def handle_error(error_msg):
    log_message("", "error", f"Error: {error_msg}")

# Set Packet processing ===========================================================================================================================
def parse_message(data):
    source_id, dest_id, service_id, message_type, data_length = struct.unpack('!BBHHH', data[:8])
    payload_data = data[8:]

    source_id_name = {v: k for k, v in SOURCE_DEST_IDS.items()}.get(source_id, f"Unknown ID: {source_id}")
    dest_id_name = {v: k for k, v in SOURCE_DEST_IDS.items()}.get(dest_id, f"Unknown ID: {dest_id}")
    service_id_name = {v: k for k, v in SERVICE_IDS.items()}.get(service_id, f"Unknown ID: {service_id}")   
    message_type_name = {v: k for k, v in MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   


    log_message("", "Parse", f"Source ID: 0x{source_id:02X} ({source_id_name})")
    log_message("", "Parse", f"Dest ID: 0x{dest_id:02X} ({dest_id_name})")
    log_message("", "Parse", f"Service ID: 0x{service_id:04X} ({service_id_name})")
    
    message_type_name = "n/a"    
    if service_id == SERVICE_IDS['Vehicle Information']:
        message_type_name = {v: k for k, v in LAST_VEHICLE_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['P-IVI Control']:
        message_type_name = {v: k for k, v in P_IVI_CONTROL_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['OTT']:
        message_type_name = {v: k for k, v in OTT_LOGIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['Blockchain Authentication']:
        message_type_name = {v: k for k, v in BLOCKCHAIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    log_message("", "Parse",  f"Message Type: 0x{message_type:04X} ({message_type_name})")

    log_message("", "Parse", f"Data Length: 0x{data_length:04X}")
    if payload_data is None:
        log_message("", "Parse", f"Payload Data: None")
    else:
        log_message("", "Parse", f"Payload Data: {payload_data}")
    log_message("", "Parse", "--------------------------------------------------------------------------------")

# Set UDP Server ===========================================================================================================================
def udp_server(host, port, tcp_port):
    global udp_client_ip
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((host, port))

    while True:
        log_message("UDP", "listening", f"UDP server listening on {host}:{port}")
        received_data, addr = udp_sock.recvfrom(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
        udp_client_ip = addr[0]
        log_message("UDP", "Received", f"Received from UDP client({udp_client_ip}): {received_data}")

        parse_message(received_data)

        if tcp_client_ip is not None:
            try:
                tcp_client(received_data, tcp_port)
                log_message("UDP", "sent", f"{tcp_client_ip}: {received_data}")
            except Exception as e:
                handle_error(str(e))

# Set TCP Server 
def tcp_server(host, port, udp_port):
    global tcp_client_ip
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((host, port))
    tcp_sock.listen(1)

    while True:
        log_message("TCP", "listening", f"TCP server listening on {host}:{port}")
        conn, addr = tcp_sock.accept()
        tcp_client_ip = addr[0]
        received_data = conn.recv(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
        log_message("TCP", "Received", f"Received from UDP client({tcp_client_ip}): {received_data}")

        parse_message(received_data)

        if udp_client_ip is not None:
            try:
                udp_client(received_data, udp_port)
                log_message("UDP", "sent", f"{udp_client_ip}: {received_data}")

            except Exception as e:
                handle_error(str(e))

# Set TCP Client ===========================================================================================================================
def tcp_client(data, port):
    global udp_client_ip
    log_message("TCP", "send", f"{udp_client_ip}:{port}: {data}")
    log_message("TCP", "send", f"=============================================================================")

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((udp_client_ip, port))
    tcp_sock.sendall(data)
    tcp_sock.close()

# Set UDP Client
def udp_client(data, port):
    global tcp_client_ip
    log_message("UDP", "send", f"{tcp_client_ip}:{port}: {data}")
    log_message("UDP", "send", f"=============================================================================")

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.sendto(data, (tcp_client_ip, port))
    udp_sock.close()

def main(args):

    udp_thread = threading.Thread(target=udp_server, args=(args.ip_addr, args.udp_port, args.tcp_port))
    tcp_thread = threading.Thread(target=tcp_server, args=(args.ip_addr, args.tcp_port, args.udp_port))
    udp_thread.start()
    tcp_thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CCU Packet Relay')
    parser.add_argument('--ip_addr', default='127.0.0.1', help='IP Address')
    parser.add_argument('--udp_port', default=50000, help='UDP Port')
    parser.add_argument('--tcp_port', default=50001, help='TCO Port')

    args = parser.parse_args()
    main(args)

#python3 CCU.py --ip_addr=192.168.8.121