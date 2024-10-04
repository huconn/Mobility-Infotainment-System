# pip install python-can
import can
import subprocess
import socket
import json
from logger import Logger 
from packet import *

# UDP transmission settings
CCU_IP_ADDR = '127.0.0.1'
CCU_PORT = 5001
DIVI_IP_ADDR = '127.0.0.1'
DIVI_PORT = 5002
PIVI1_IP_ADDR = '127.0.0.1'
PIVI1_PORT = 5003
PIVI2_IP_ADDR = '127.0.0.1'
PIVI2_PORT = 5004
PIVI3_IP_ADDR = '127.0.0.1'
PIVI3_PORT = 5005
CLOUDE_IP_ADDR = '127.0.0.1'
CLOUDE_PORT = 5006

LTE_IP_ADDR = '127.0.0.1'
LTE_PORT = 5012
CAN_IP_ADDR = '127.0.0.1'
CAN_PORT = 5013
WAVE_IP_ADDR = '127.0.0.1'
WAVE_PORT = 5014

# Set up CAN bus
def setup_can(interface='can0', bitrate=500000):
    try:
        # Set up the CAN interface using system commands
        print("Setting up CAN interface...")
        subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'type', 'can', 'bitrate', str(bitrate)], check=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], check=True)
        print("CAN interface setup complete.")

        # Initialize the CAN bus
        bus = can.interface.Bus(channel='can0', interface='socketcan')
        return bus

    except subprocess.CalledProcessError as e:
        print(f"Failed to set up CAN interface: {e}")

        # Retry: bring the interface down and reset it
        try:
            print("Retrying CAN interface setup...")
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'down'], check=True)

            # Set up CAN interface again
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'type', 'can', 'bitrate', str(bitrate)], check=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], check=True)
            print("CAN interface reset and setup complete.")

            # Initialize the CAN bus
            bus = can.interface.Bus(channel=interface, interface='socketcan')
            return bus

        except subprocess.CalledProcessError as e:
            print(f"Failed to reset and set up CAN interface: {e}")
            return None

    except Exception as e:
        print(f"CAN bus error: {e}")
        return None

# Set up UDP socket
def setup_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock
    except socket.error as e:
        print(f"Socket error: {e}")
        return None

def send_udp_message(sock, message, server_ip, server_port):
    """Send message via UDP socket"""
    try:
        print(f"IP: {server_ip}, Port: {server_port}")
        sock.sendto(message, (server_ip, server_port))
    except Exception as e:
        print(f"Failed to send message: {e}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="CAN Data Sender")
    parser.add_argument('--interface', type=str, default='can0', help="CAN interface (default: can0)")
    parser.add_argument('--bitrate', type=int, default=500000, help="CAN bitrate (default: 500000)")
    parser.add_argument('--server', type=str, default=CCU_IP_ADDR, 
                        help="Server IP address (default: {CCU_IP_ADDR})")
    parser.add_argument('--port', type=int, default=CCU_PORT, help="Server port (default: {CCU_PORT})")
    return parser.parse_args()

def main(interface, bitrate, server_ip, server_port):
    can = setup_can(interface, bitrate)
    if can is None:
        print("Can bus not available, exiting program.")
        return

    sock = setup_socket()
    if sock is None:
        print("Socket not available, exiting program.")
        return

    print("Receive CAN messages from the CAN0 interface and send them via UDP")
    print("Listening for CAN messages...")

    while True:
        # Receive CAN message
        msg = can.recv()
        if msg:
            # Convert CAN message to JSON format
            if msg.arbitration_id == 0x111:
                print(f"0x111) Received CAN message: {msg}")
                
                can_message = {
                    "id": hex(msg.arbitration_id),  # hex format for ID
                    "speed Gauge": int(msg.data[0]),    # 0 ~ 180
                    "RPM Gauge": int((msg.data[1] << 8) + msg.data[2]),  # 0 ~ 3000
                    "Torque Gauge": int(msg.data[3]),    # 0 ~2
                    "Fuel Gauge": int(msg.data[4]),      # 0 ~ 100
                    "Battery Gauge": int(msg.data[5]),   # 0 ~ 100
                    "timestamp": msg.timestamp
                }
            elif msg.arbitration_id == 0x222:
                print(f"0x222) Received CAN message: {msg}")
                
                can_message = {
                    "id": hex(msg.arbitration_id),  # hex format for ID
                    "Brake Signal": int(msg.data[0]),        # 1(On), 0(Off)
                    "Overheat Signal": int(msg.data[1]),     # 1(On), 0(Off)
                    "Engine Signal": int(msg.data[2]),       # 1(On), 0(Off)
                    "Left Signal": int(msg.data[4]),         # 1(Left), 0(Off)
                    "Right Signal": int(msg.data[5]),        # 1(Right), 0(Off)
                    "battery Signal": int(msg.data[6]),      # 1(On), 0(Off)
                    "Seatbelt Signal": int(msg.data[3]),     # 1(On), 0(Off)
                    "Gear Signal": int(msg.data[7]),         # 1(P), 2(R), 4(N), 8(D)
                    "timestamp": msg.timestamp
                }
            else:
                print(f"Received CAN message: {msg}")
                
                can_message = {
                    "id": hex(msg.arbitration_id),  # ID in hex
                    "data": [hex(byte) for byte in msg.data],  # data as hex values
                    "timestamp": msg.timestamp
                }
            
            # Convert to JSON string and encode to bytes
            json_message = json.dumps(can_message).encode('utf-8')

            data_length = len(json_message)
            
            # Pack the header fields into a byte sequence
            header = struct.pack(
                '>BBHHHHH',                             # Format: Big-endian, 2x 1-byte, 5x 2-byte
                SourceDestID.CAN.value,                 # 1 byte (source_id)
                SourceDestID.CCU.value,                 # 1 byte (destination_id)
                ServiceID.VEHICLE_INFORMATION.value,    # 2 bytes (service_id)
                VEHICLE_MESSAGE_TYPES.LAST_VEHICLE_INFORMATION.value,  # 2 bytes (message_type)
                0x0012,                                 # 2 bytes (ift_id)
                0x0001,                                 # 2 bytes (ift_type)
                data_length                             # 2 bytes (data_length)
            )

            # Combine the header and the JSON message (both in bytes)
            full_message = header + json_message

            print(f"Sending Full message: {full_message}")
            
            # Send full message via UDP
            send_udp_message(sock, full_message, server_ip, server_port)

if __name__ == "__main__":
    try:
        args = parse_arguments()
        print(f"CAN Interface: {args.interface}, CAN Bitrage: {args.bitrate}, Server IP: {args.server}, Port: {args.port}")
        main(args.interface, args.bitrate, args.server, args.port)
    except KeyboardInterrupt:
        print("Program interrupted.")