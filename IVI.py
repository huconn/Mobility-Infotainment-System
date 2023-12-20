import os
import socket
import struct
import argparse
import threading
from time import sleep

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

def log_message(protocol, direction, data, output_to_console=True, output_to_file=True):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')  
    message = f"[{timestamp}] {direction.upper()} {protocol} : {data}"

    if output_to_console:
        print(message)

    if output_to_file:
        filename = f"{protocol}_logs_{timestamp}.txt"
        with open(filename, "a") as f:
            f.write(message)


def handle_error(error_msg):
    print(f"Error: {error_msg}")

# Check GPIO State
def check_gpio_state():
    return "LOW" # GPIO.HIGH or GPIO.LOW

def switch_setup(pin):
    # Check if the GPIO pin is already exported
    if not os.path.exists(f'/sys/class/gpio/gpio{pin}'):
        with open('/sys/class/gpio/export', 'w') as export_file:
            export_file.write(str(pin))

    with open(f'/sys/class/gpio/gpio{pin}/direction', 'w') as direction_file:
        direction_file.write("in")

def gpio_unexport(pin):
    # Check if the GPIO pin is exported
    if os.path.exists(f'/sys/class/gpio/gpio{pin}'):
        with open('/sys/class/gpio/unexport', 'w') as unexport_file:
            unexport_file.write(str(pin))
    else:
        print(f"GPIO pin {pin} is not exported.")

def read_switch_state(pin):
    try:
        with open(f"/sys/class/gpio/gpio{pin}/value", "r") as file:
            value_str = file.read().strip()  
            return int(value_str) if value_str else 0
    except FileNotFoundError:
        print(f"GPIO {pin} is not exported.")
        return None
    except ValueError:
        print(f"Invalid value read from GPIO {pin}.")
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

    print("Received Response:")
    print(f"Source ID: 0x{source_id:02X} ({source_id_name})")
    print(f"Dest ID: 0x{dest_id:02X} ({dest_id_name})")
    print(f"Service ID: 0x{service_id:04X} ({service_id_name})")
    
    message_type_name = "n/a"    
    if service_id == SERVICE_IDS['Vehicle Information']:
        message_type_name = {v: k for k, v in LAST_VEHICLE_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['P-IVI Control']:
        message_type_name = {v: k for k, v in P_IVI_CONTROL_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['OTT']:
        message_type_name = {v: k for k, v in OTT_LOGIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    elif service_id == SERVICE_IDS['Blockchain Authentication']:
        message_type_name = {v: k for k, v in BLOCKCHAIN_MESSAGE_TYPES.items()}.get(message_type, f"Unknown ID: {message_type}")   
    print(f"Message Type: 0x{message_type:04X} ({message_type_name})")

    print(f"Data Length: 0x{data_length:04X}")
    if payload_data is None:
        print("Payload Data: None")
    else:
        print("Payload Data:", payload_data)
    print("--------------------------------------------------------------------------------")

    return source_id, dest_id, service_id, message_type, data_length, payload_data

# Set UDP Packet processing ===========================================================================================================================
def send_udp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, message_type, data):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = create_message(source_id, dest_id, service_id, message_type, data)
    udp_sock.sendto(message, (dest_ip_addr, dest_port))
    print(f"Sent UDP Message: message={message} to {dest_ip_addr}:{dest_port}")
    udp_sock.close()


# Set UDP Sender
def udp_sender(dest_ip_addr, dest_port, source_id, dest_id, service_id):
    print(f"UDP client sending to {dest_ip_addr}:{dest_port}")

    while True:
        state = read_switch_state(SWITCH_PIN)
        print(f"GPIO State: {state}")

        # "LOW" means the switch is pressed
        if state == 0 :
            send_udp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, MESSAGE_TYPES['P-IVI Control Request'], b"P-IVI Control Request through UDP")
        sleep(1)

# Set UDP Receiver
def udp_receiver(host, port):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((host, port))
    print(f"UDP server listening on {host}:{port}")
    
    while True:
        received_data, addr = udp_sock.recvfrom(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
        udp_client_ip = addr[0]
        print(f"Received from UDP client({udp_client_ip}): {received_data}")
        parsed_response = parse_message(received_data)

        # Process received message
        source_id = parsed_response[0]
        dest_id = parsed_response[1]
        service_id = parsed_response[2]
        message_type = parsed_response[3]
        data_length = parsed_response[4]
        payload_data = parsed_response[5]

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
                send_udp_message(udp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['P-IVI Control Response'], b"P-IVI Control Response")
                print(f"Send 'P-IVI Control Response' to UDP client({udp_client_ip})")
        elif service_id == SERVICE_IDS['OTT']:
            if message_type == MESSAGE_TYPES['OTT Login Request']:
                # Create 'OTT Login Response' message
                send_udp_message(udp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['OTT Login Response'], b"OTT Login Response")
                print(f"Send 'OTT Login Response' to UDP client({udp_client_ip})")
        elif service_id == SERVICE_IDS['Blockchain Authentication']:
            if message_type == MESSAGE_TYPES['Blockchain Authentication Request']:
                # Create 'Bloackchain Authntication Responsee' message
                send_udp_message(udp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['Bloackchain Authntication Response'], b"Bloackchain Authntication Response")
                print(f"Send 'Bloackchain Authntication Response' to UDP client({udp_client_ip})")


# Set TCP Packet processing ===========================================================================================================================
def send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, message_type, data):
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    message = create_message(source_id, dest_id, service_id, message_type, data)
    tcp_sock.connect((dest_ip_addr, dest_port))
    tcp_sock.sendall(message)
    print(f"Sent TCP Message: message={message} to {dest_ip_addr}:{dest_port}")
    tcp_sock.close()

# Set TCP Sender
def tcp_sender(dest_ip_addr, dest_port, source_id, dest_id, service_id):
    print(f"TCP client sending to {dest_ip_addr}:{dest_port}")

    while True:
        state = read_switch_state(SWITCH_PIN)
        print(f"GPIO State: {state}")
        
        # "LOW" means the switch is pressed
        if state == 0 :
            send_tcp_message(dest_ip_addr, dest_port, source_id, dest_id, service_id, MESSAGE_TYPES['P-IVI Control Request'], b"P-IVI Control Request through TCP")

        sleep(1) 

# Set TCP Server
def tcp_server(host, port):
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((host, port))
    tcp_sock.listen(1)
    print(f"TCP server listening on {host}:{port}")

    while True:
        conn, addr = tcp_sock.accept()
        tcp_client_ip = addr[0]
        received_data = conn.recv(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
        print(f"Received from TCP client({tcp_client_ip}): {received_data}")
        parsed_response = parse_message(received_data)

        # Process received message
        source_id = parsed_response[0]
        dest_id = parsed_response[1]
        service_id = parsed_response[2]
        message_type = parsed_response[3]

        if service_id == SERVICE_IDS['Vehicle Information']:
            if message_type == MESSAGE_TYPES['Last Vehicle Information']:
                # Create 'Last Vehicle Information' message
                send_tcp_message(tcp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['Last Vehicle Information'], b"Last Vehicle Information")
                print(f"Send 'Last Vehicle Information' to TCP client({tcp_client_ip})")
        elif service_id == SERVICE_IDS['P-IVI Control']:
            if message_type == MESSAGE_TYPES['P-IVI Control Request']:
                # Create 'P-IVI Control Response' message
                send_tcp_message(tcp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['P-IVI Control Response'], b"P-IVI Control Response")
                print(f"Send 'P-IVI Control Response' to TCP client({tcp_client_ip})")
        elif service_id == SERVICE_IDS['OTT']:
            if message_type == MESSAGE_TYPES['OTT Login Request']:
                # Create 'P-IVI Control Response' message
                send_tcp_message(tcp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['OTT Login Response'], b"OTT Login Response")
                print(f"Send 'OTT Login Response' to TCP client({tcp_client_ip})")
        elif service_id == SERVICE_IDS['Blockchain Authentication']:
            if message_type == MESSAGE_TYPES['Blockchain Authentication Request']:
                # Create 'Blockchain Authentication Response' message
                send_tcp_message(tcp_client_ip, port, dest_id, source_id, service_id, MESSAGE_TYPES['Blockchain Authentication Response'], b"Blockchain Authentication Response")
                print(f"Send 'Blockchain Authentication Response' to TCP client({tcp_client_ip})")

def main(args):
    source_ip_addr = args.src_ip_addr
    dest_ip_addr = args.dest_ip_addr
    udp_port = args.udp_port
    tcp_port = args.tcp_port
    source_id = SOURCE_DEST_IDS[args.source_id]
    dest_id = SOURCE_DEST_IDS[args.dest_id]
    service_id = SERVICE_IDS[args.service_id]
    message_type = MESSAGE_TYPES[args.message_type]

    print(f"Sending({source_ip_addr}) UDP message to {dest_ip_addr} - UDP:{udp_port}, TCP:{tcp_port}")
    print(f"Source ID: 0x{source_id:02X} ({args.source_id})")
    print(f"Dest ID: 0x{dest_id:02X} ({args.dest_id})")
    print(f"Service ID: 0x{service_id:04X} ({args.service_id})")
    print(f"Message Type: 0x{message_type:04X} ({args.message_type})")
    if args.data is not None:
        data = args.data.encode('utf-8')
        print(f"Data Length: 0x{len(data):04X}")
    
    if args.source_id == 'D-IVI':
        # Initiate Hello Message        
        send_udp_message(dest_ip_addr, udp_port, source_id, dest_id, service_id, message_type, b"D-IVI Hello Message through UDP")
        # Initiate UDP Receiver Thread
        udp_receiver_thread = threading.Thread(target=udp_receiver, args=(source_ip_addr, udp_port))
        # Initiate UDP Sender Thread
        udp_sender_thread = threading.Thread(target=udp_sender, args=(dest_ip_addr, udp_port, source_id, dest_id, service_id))
        udp_receiver_thread.start()
        udp_sender_thread.start()

    elif args.source_id == 'P-IVI1':
        # Initiate Hello Message        
        send_tcp_message(dest_ip_addr, tcp_port, source_id, dest_id, service_id, message_type, b"D-IVI Hello Message through TCP")
        # Initiate TCP Receiver Thread
        tcp_server_thread = threading.Thread(target=tcp_server, args=(source_ip_addr, tcp_port))
        # Initiate TCP Sender Thread
        tcp_sender_thread = threading.Thread(target=tcp_sender, args=(dest_ip_addr, tcp_port, source_id, dest_id, service_id))
        tcp_server_thread.start()
        tcp_sender_thread.start()

    elif args.source_id == 'D-P-IVI':
        print("Boosting D-IVI and P-IVI1")
    else:
        print("Unknown Source ID")
        return

if __name__ == "__main__":
    try:
        # Setup GPIO
        switch_setup(SWITCH_PIN)

        parser = argparse.ArgumentParser(description='D-IVI UDP Message Sender/Receiver')
        parser.add_argument('--src_ip_addr', default='127.0.0.1', help='Src IP Address')
        parser.add_argument('--dest_ip_addr', default='127.0.0.1', help='Dest IP Address')
        parser.add_argument('--udp_port', default=50000, help='UDP Port')
        parser.add_argument('--tcp_port', default=50001, help='TCP Port')    
        parser.add_argument('--source_id', default='D-IVI', choices=['CCU', 'D-IVI', 'P-IVI1', 'P-IVI2'], help='Source ID')
        parser.add_argument('--dest_id', default='P-IVI1', choices=['CCU', 'D-IVI', 'P-IVI1', 'P-IVI2'], help='Destination ID')
        parser.add_argument('--service_id', default='P-IVI Control', choices=SERVICE_IDS.keys(), help='Service ID')
        parser.add_argument('--message_type', default='None', choices=MESSAGE_TYPES.keys(), help='Message Type')
        parser.add_argument('--data', help='Payload Data')
        
        args = parser.parse_args()
        main(args)

    # Stop program when 'Ctrl+C' is pressed
    except (KeyboardInterrupt, Exception) as e:
        print(f"An error occurred: {e}")
        gpio_unexport(SWITCH_PIN)


# UDP
# python DIVI.py --src_ip_addr='192.168.10.103' --dest_ip_addr='192.168.8.121' --source_id='D-IVI' --dest_id='P-IVI1'
# TCP
# python DIVI.py --src_ip_addr='192.168.10.103' --dest_ip_addr='192.168.8.121' --source_id='P-IVI1' --dest_id='D-IVI'