import socket
import struct
import argparse
import threading
import time
import netifaces
import netaddr

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

DEBUG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}

debug_level = 'INFO'

def log_message(debug, protocol, direction, data, output_to_console=True, output_to_file=False):
    global debug_level

    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')  
    message = f"[{timestamp}] {direction.upper()} {protocol} : {data}"

    if DEBUG_LEVELS.get(debug, 1) >= DEBUG_LEVELS.get(debug_level):

        if output_to_console:
            print(message)
        '''
        if output_to_file:
            filename = f"{protocol}_logs_{timestamp}.txt"
            with open(filename, "a") as f:
                f.write(message)
        '''

def handle_error(error_msg):
    log_message("", "error", f"Error: {error_msg}")

def get_default_interface():
    routes = netifaces.gateways()
    
    if 'default' in routes and netifaces.AF_INET in routes['default']:
        return routes['default'][netifaces.AF_INET][1] 

    return None

def get_interface_ip(interface_name):
    addresses = netifaces.ifaddresses(interface_name)
    if netifaces.AF_INET in addresses:
        for link in addresses[netifaces.AF_INET]:
            return link['addr']
    return None

# Set Packet processing ===========================================================================================================================
def parse_message(data):
    source_id, dest_id, service_id, message_type, data_length = struct.unpack('!BBHHH', data[:8])
    payload_data = data[8:]

    source_id_name = {v: k for k, v in SOURCE_DEST_IDS.items()}.get(source_id, f"Unknown ID: {source_id}")
    dest_id_name = {v: k for k, v in SOURCE_DEST_IDS.items()}.get(dest_id, f"Unknown ID: {dest_id}")
    service_id_name = {v: k for k, v in SERVICE_IDS.items()}.get(service_id, f"Unknown ID: {service_id}")   

    log_message("DEBUG", "", "Parse", f"Source ID: 0x{source_id:02X} ({source_id_name})")
    log_message("DEBUG", "", "Parse", f"Dest ID: 0x{dest_id:02X} ({dest_id_name})")
    log_message("DEBUG", "", "Parse", f"Service ID: 0x{service_id:04X} ({service_id_name})")
    
    message_type_name = "n/a"    
    if service_id == SERVICE_IDS['Vehicle Information']:
        message_type_name = {v: k for k, v in LAST_VEHICLE_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['P-IVI Control']:
        message_type_name = {v: k for k, v in P_IVI_CONTROL_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['OTT']:
        message_type_name = {v: k for k, v in OTT_LOGIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['Blockchain Authentication']:
        message_type_name = {v: k for k, v in BLOCKCHAIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    log_message("DEBUG", "", "Parse",  f"Message Type: 0x{message_type:04X} ({message_type_name})")

    log_message("DEBUG", "", "Parse", f"Data Length: 0x{data_length:04X}")
    if payload_data is None:
        log_message("DEBUG", "", "Parse", f"Payload Data: None")
    else:
        log_message("DEBUG", "", "Parse", f"Payload Data: {payload_data}")
    log_message("DEBUG", "", "Parse", "--------------------------------------------------------------------------------")

    return source_id, dest_id, service_id, message_type, data_length, payload_data

# Set TCP Server ===========================================================================================================================
def tcp_server(args):
    try:
        src_ip_addr = args.src_ip_addr
        src_port = args.src_port
        divi_ip_addr = args.divi_ip_addr
        divi_port = args.divi_port
        pivi_ip_addr = args.pivi_ip_addr
        pivi_port = args.pivi_port

        if src_ip_addr is None:
            default_interface = get_default_interface()
            print(f"Default Interface: {default_interface}")
            src_ip_addr = get_interface_ip(default_interface)

        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind((src_ip_addr, src_port))
        tcp_sock.listen(1)

        while True:
            log_message("INFO", "TCP", "listening", f"TCP server listening on {src_ip_addr}:{src_port}")
            conn, addr = tcp_sock.accept()
            received_data = conn.recv(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
            tcp_client_ip = addr[0]
            log_message("INFO", "TCP", "Received", f"Received from TCP client({tcp_client_ip}): {received_data}")

            parsed_response = parse_message(received_data)
            source_id = parsed_response[0]
            dest_id = parsed_response[1]

            if dest_id == SOURCE_DEST_IDS['D-IVI']:
                try:
                    if divi_ip_addr is not None:
                        udp_client(received_data, divi_ip_addr, divi_port)
                        log_message("INFO", "UDP", "sent", f"{divi_ip_addr}-{divi_port}: {received_data}")

                except Exception as e:
                    handle_error(str(e))
            elif dest_id == SOURCE_DEST_IDS['P-IVI1'] or dest_id == SOURCE_DEST_IDS['P-IVI2']:
                try:
                    if pivi_ip_addr is not None:
                        tcp_client(received_data, pivi_ip_addr, pivi_port)
                        log_message("INFO", "TCP", "sent", f"{pivi_ip_addr}-{pivi_port}: {received_data}")

                except Exception as e:
                    handle_error(str(e))

    except ConnectionRefusedError:
        print(f"Connection to {src_ip_addr}:{src_port} refused.")
    except Exception as e:
        print(f"An error occurred while sending the TCP message: {e}")

# Set TCP Client ===========================================================================================================================
def tcp_client(data, dest_ip_addr, dest_port):
    try:
        log_message("INFO", "TCP", "send", f"{dest_ip_addr}:{dest_port}: {data}")
        log_message("INFO", "TCP", "send", f"=============================================================================")

        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((dest_ip_addr, dest_port))
        tcp_sock.sendall(data)
    except ConnectionRefusedError:
        print(f"Connection to {dest_ip_addr}:{dest_port} refused.")
    except Exception as e:
        print(f"An error occurred while sending the TCP message: {e}")
    finally:
        tcp_sock.close()

# Set UDP Client ===========================================================================================================================
def udp_client(data, dest_ip_addr, dest_port):
    try:
        log_message("INFO", "UDP", "send", f"{dest_ip_addr}:{dest_port}: {data}")
        log_message("INFO", "UDP", "send", f"=============================================================================")

        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.sendto(data, (dest_ip_addr, dest_port))
    except ConnectionRefusedError:
        print(f"Connection to {dest_ip_addr}:{dest_port} refused.")
    except Exception as e:
        print(f"An error occurred while sending the UDP message: {e}")
    finally:
        udp_sock.close()

def main(args):
    global debug_level
    debug_level = args.debug_level
    log_message("INFO", "", "", f"Debug level: {debug_level}")

    tcp_thread = threading.Thread(target=tcp_server, args=(args,))
    tcp_thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CCU TCP-IVI Control Service Relay')
    #parser.add_argument('--src_ip_addr', default='10.0.0.2', help='Src IP Address')
    parser.add_argument('--src_ip_addr', help='Src IP Address')
    parser.add_argument('--src_port', default=50000, help='TCP Port')
    parser.add_argument('--divi_ip_addr', default='10.0.0.5', help='D-IVI IP Address')
    parser.add_argument('--divi_port', default=50000, help='D-IVI UDP Port')
    parser.add_argument('--pivi_ip_addr', default='10.0.0.6', help='P-IVI IP Address')
    parser.add_argument('--pivi_port', default=50001, help='P-IVI TCP Port')
    parser.add_argument('--debug_level', default='INFO', choices=DEBUG_LEVELS.keys(), help='Debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')

    args = parser.parse_args()
    main(args)

#python3 CCU.py --ip_addr=192.168.8.121