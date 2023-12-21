import os
import socket
import struct
import argparse
import threading
import time
from time import sleep
import netifaces
import netaddr

# Configurations
SWITCH_PIN = 82
PROTOCOL_LEN = 8
MAX_PAYLOAD_LEN = 65535

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

# message type
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
    'Blockchain Authentication Response': 0x0001, 
    'None': 0xffff
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
    print(f"Error: {error_msg}")

# Check GPIO State
def check_gpio_state():
    return "LOW" # GPIO.HIGH or GPIO.LOW

def switch_setup(pin):
    try:
        # Check if the GPIO pin is already exported
        if not os.path.exists(f'/sys/class/gpio/gpio{pin}'):
            with open('/sys/class/gpio/export', 'w') as export_file:
                export_file.write(str(pin))

        with open(f'/sys/class/gpio/gpio{pin}/direction', 'w') as direction_file:
            direction_file.write("in")
        return True
    except Exception as e:
        print(f"An error occurred while reading GPIO {pin}: {e}")
        return False

def gpio_unexport(pin):
    try:
        # Check if the GPIO pin is exported
        if os.path.exists(f'/sys/class/gpio/gpio{pin}'):
            with open('/sys/class/gpio/unexport', 'w') as unexport_file:
                unexport_file.write(str(pin))
        else:
            print(f"GPIO pin {pin} is not exported.")
    except Exception as e:
        print(f"An error occurred while reading GPIO {pin}: {e}")

def read_switch_state(pin):
    try:
        with open(f"/sys/class/gpio/gpio{pin}/value", "r") as file:
            value_str = file.read().strip()  
            return int(value_str) if value_str else 0
    except Exception as e:
        #print(f"An error occurred while reading GPIO {pin}: {e}")
        log_message("DEBUG", "", "GPIO", f"An error occurred {pin}: {e}")
        return 1

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
def create_message(source_id, dest_id, service_id, message_type, data=None):
    if data is None:
        data_length = 0
        return struct.pack('!BBHHH', source_id, dest_id, service_id, message_type, data_length)
    
    data_length = len(data)
    return struct.pack('!BBHHH{}s'.format(data_length), source_id, dest_id, service_id, message_type, data_length, data)

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
    log_message("DEBUG", "", "Parse", f"Message Type: 0x{message_type:04X} ({message_type_name})")

    print(f"Data Length: 0x{data_length:04X}")
    if payload_data is None:
        log_message("DEBUG", "", "Parse", f"Payload Data: None")
    else:
        log_message("DEBUG", "", "Parse", f"Payload Data: {payload_data}")
    log_message("DEBUG", "", "Parse", "--------------------------------------------------------------------------------")

    return source_id, dest_id, service_id, message_type, data_length, payload_data

# Set TCP Packet processing ===========================================================================================================================
def send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, message_type, data):
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message = create_message(source_id, dest_id, service_id, message_type, data)
        tcp_sock.connect((dest_ip_addr, dest_port))
        tcp_sock.sendall(message)
        log_message("INFO", "TCP", "SEND", f"{message} to {dest_ip_addr}:{dest_port}")
    except ConnectionRefusedError:
        print(f"Connection to {dest_ip_addr}:{dest_port} refused.")
    except Exception as e:
        print(f"An error occurred while sending the TCP message: {e}")
    finally:
        tcp_sock.close()

# Set TCP Sender
def tcp_sender(dest_ip_addr, dest_port, source_id, dest_id, service_id):
    log_message("INFO", "TCP", "SEND", f"Ready to send after GPIO check 1ms {dest_ip_addr}:{dest_port}")

    while True:
        try:
            state = read_switch_state(SWITCH_PIN)
            log_message("DEBUG", "", "GPIO", f"State: {state}")
            
            # "LOW" means the switch is pressed
            if state == 0 :
                send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, MESSAGE_TYPES['P-IVI Control Request'], b"P-IVI Control Request through TCP")

            sleep(0.001)
        
        except Exception as e:
            print(f"Error reading GPIO state: {e}")
            sleep(1)  # Wait for a bit before retrying)

def tcp_test_sender(dest_ip_addr, dest_port, source_id, dest_id, service_id, test_sending):
    log_message("INFO", "TCP", "SEND", f"Send {test_sending} times at 1-second intervals {dest_ip_addr}:{dest_port}")

    count = 0  # Initialize the counter
    while count < test_sending:
        try:
            send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, MESSAGE_TYPES['P-IVI Control Request'], b"P-IVI Control Request through TCP")
            log_message("INFO", "TCP", "SEND", f"Send {count} times {dest_ip_addr}:{dest_port}")
            sleep(1)
        except Exception as e:
            print(f"Error reading GPIO state: {e}")
            sleep(1)
        count += 1
        
# Set TCP Server
def tcp_server(host, port, dest_port):
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind((host, port))
        tcp_sock.listen(1)
        log_message("INFO", "TCP", "listening", f"{host}:{port}, TCP Client port: {dest_port}")

        while True:
            conn, addr = tcp_sock.accept()
            tcp_client_ip = addr[0]
            received_data = conn.recv(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
            log_message("INFO", "TCP", "Received", f"client({tcp_client_ip}): {received_data}")
            parsed_response = parse_message(received_data)

            # Process received message
            source_id = parsed_response[0]
            dest_id = parsed_response[1]
            service_id = parsed_response[2]
            message_type = parsed_response[3]

            if service_id == SERVICE_IDS['Vehicle Information']:
                if message_type == MESSAGE_TYPES['Last Vehicle Information']:
                    # Display 'Last Vehicle Information' message
                    print(f"Last Vehicle Information : ", end="")
                    for byte in payload_data[:data_length]:
                        print(f"{byte:02X} ", end="")
                    print()
            elif service_id == SERVICE_IDS['P-IVI Control']:
                if message_type == MESSAGE_TYPES['P-IVI Control Request']:
                    # Create 'P-IVI Control Response' message
                    send_tcp_message(tcp_client_ip, dest_port, dest_id, source_id, service_id, MESSAGE_TYPES['P-IVI Control Response'], b"P-IVI Control Response")
                    log_message("DEBUG", "", "", f"Send 'P-IVI Control Response' to TCP client({tcp_client_ip})")
            elif service_id == SERVICE_IDS['OTT']:
                if message_type == MESSAGE_TYPES['OTT Login Request']:
                    # Create 'P-IVI Control Response' message
                    send_tcp_message(tcp_client_ip, dest_port, dest_id, source_id, service_id, MESSAGE_TYPES['OTT Login Response'], b"OTT Login Response")
                    log_message("DEBUG", "", "", f"Send 'OTT Login Response' to TCP client({tcp_client_ip})")
            elif service_id == SERVICE_IDS['Blockchain Authentication']:
                if message_type == MESSAGE_TYPES['Blockchain Authentication Request']:
                    # Create 'Blockchain Authentication Response' message
                    send_tcp_message(tcp_client_ip, dest_port, dest_id, source_id, service_id, MESSAGE_TYPES['Blockchain Authentication Response'], b"Blockchain Authentication Response")
                    log_message("DEBUG", "", "", f"Send 'Blockchain Authentication Response' to TCP client({tcp_client_ip})")

    except ConnectionRefusedError:
        print(f"Connection to {host}:{port} refused.")
    except Exception as e:
        print(f"An error occurred while sending the TCP message: {e}")

def main(args):
    global debug_level

    debug_level = args.debug_level   
    test_sending = args.test_sending     
    source_ip_addr = args.src_ip_addr
    dest_ip_addr = args.dest_ip_addr
    src_port = args.src_port
    dest_port = args.dest_port
    source_id = SOURCE_DEST_IDS[args.source_id]
    dest_id = SOURCE_DEST_IDS[args.dest_id]
    service_id = SERVICE_IDS[args.service_id]
    message_type = MESSAGE_TYPES[args.message_type]

    if source_ip_addr is None:
        default_interface = get_default_interface()
        print(f"Default Interface: {default_interface}")
        source_ip_addr = get_interface_ip(default_interface)
    
    log_message("INFO", "UDP", "", f"Test Sending: {test_sending}")
    log_message("INFO", "TCP", "", f"Debug level: {debug_level}")
    log_message("INFO", "TCP", "", f"Source IP Address: {source_ip_addr}")
    log_message("INFO", "TCP", "", f"Destination IP Address: {dest_ip_addr}")
    log_message("INFO", "TCP", "", f"Source Port: {src_port}")
    log_message("INFO", "TCP", "", f"Destination Port: {dest_port}")

    #print(f"Sending({source_ip_addr}-TCP:{src_port}) to {dest_ip_addr}-TCP:{dest_port}")
    log_message("INFO", "TCP", "", f"Source ID: 0x{source_id:02X} ({args.source_id})")
    log_message("INFO", "TCP", "", f"Dest ID: 0x{dest_id:02X} ({args.dest_id})")
    log_message("INFO", "TCP", "", f"Service ID: 0x{service_id:04X} ({args.service_id})")
    log_message("INFO", "TCP", "", f"Message Type: 0x{message_type:04X} ({args.message_type})")

    if args.data is not None:
        data = args.data.encode('utf-8')
        log_message("INFO", "TCP", "", f"Data Length: 0x{len(data):04X}")
    
    # Initiate Hello Message        
    #send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, message_type, b"D-IVI Hello Message through TCP")

    # Initiate TCP Receiver Thread
    tcp_server_thread = threading.Thread(target=tcp_server, args=(source_ip_addr, src_port, dest_port))
    tcp_server_thread.start()

    # Initiate TCP Sender Thread
    if switch_setup(SWITCH_PIN):
        tcp_sender_thread = threading.Thread(target=tcp_sender, args=(dest_ip_addr, dest_port, source_id, dest_id, service_id))
        tcp_sender_thread.start()

    if test_sending > 0:
        test_tcp_sender_thread = threading.Thread(target=tcp_test_sender, args=(dest_ip_addr, dest_port, source_id, dest_id, service_id, test_sending))
        test_tcp_sender_thread.start()

if __name__ == "__main__":
    try:
        # Setup GPIO
        switch_setup(SWITCH_PIN)

        parser = argparse.ArgumentParser(description='P-IVI TCP Message Sender/Receiver')
        #parser.add_argument('--src_ip_addr', default='10.0.0.6', help='Src IP Address')
        parser.add_argument('--src_ip_addr', help='Src IP Address')
        parser.add_argument('--dest_ip_addr', default='10.0.0.2', help='Dest IP Address')
        parser.add_argument('--src_port', default=50001, help='TCP Port')
        parser.add_argument('--dest_port', default=50000, help='TCP Port')    
        parser.add_argument('--source_id', default='P-IVI1', choices=['CCU', 'D-IVI', 'P-IVI1', 'P-IVI2'], help='Source ID')
        parser.add_argument('--dest_id', default='D-IVI', choices=['CCU', 'D-IVI', 'P-IVI1', 'P-IVI2'], help='Destination ID')
        parser.add_argument('--service_id', default='P-IVI Control', choices=SERVICE_IDS.keys(), help='Service ID')
        parser.add_argument('--message_type', default='None', choices=MESSAGE_TYPES.keys(), help='Message Type')
        parser.add_argument('--data', help='Payload Data')
        parser.add_argument('--debug_level', default='INFO', choices=DEBUG_LEVELS.keys(), help='Debug level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
        parser.add_argument('--test_sending', type=int, default=0, help='Test sending UDP message')
        args = parser.parse_args()
        main(args)

    # Stop program when 'Ctrl+C' is pressed
    except (KeyboardInterrupt, Exception) as e:
        print(f"An error occurred: {e}")
        gpio_unexport(SWITCH_PIN)


# TCP <-> TCP
# python3 P-IVI.py --dest_ip_addr='192.168.8.196'
# python3 P-IVI.py --dest_ip_addr='192.168.8.196' --test_sending=10