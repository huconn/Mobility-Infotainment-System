import serial
import time
import requests
from datetime import datetime, timedelta
import socket
import argparse
import json
from logger import Logger 
from packet import *

# UDP transmission settings
CCU_IP_ADDR = '192.168.10.103'  #'127.0.0.1'
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

# Serial port configuration
def setup_serial():
    try:
        ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=1)
        return ser
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
        return None

# Create UDP socket
def setup_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock
    except socket.error as e:
        print(f"Socket error: {e}")
        return None

# Function to send AT command and read response
def send_at_command(ser, command):
    ser.write((command + '\r\n').encode())
    time.sleep(1)
    response = ''
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode()
    return response.strip()

# GPS initial setup
def setup_gps(ser):
    commands = [
        'AT+QGPS=1',
        'AT+QGPS?',
        'AT+QGPSCFG="gnssconfig"',
        'AT+QGPSCFG="gpsnmeatype",1'
    ]
    for cmd in commands:
        response = send_at_command(ser, cmd)
        print(f"Command: {cmd}\nResponse: {response}\n")

# Get GPS location information
def get_gps_location(ser):
    response = send_at_command(ser, 'AT+QGPSLOC?')
    return response

# Send data to server
def send_to_server(sock, data, server_ip, server_port):
    try:
        message = str(data)
        sock.sendto(message.encode(), (server_ip, server_port))
        print(f"Data sent to server {server_ip}:{server_port}: {message}")
    except Exception as e:
        print(f"Failed to send data to server: {e}")

def parse_gps_data(gps_data):
    default_json = {
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "latitude": 0.0,
        "longitude": 0.0,
        "error": "GPS data error"
    }

    parts = gps_data.split('+QGPSLOC: ')
    if len(parts) < 2:
        return json.dumps(default_json)
    
    data = parts[1].split(',')
    if len(data) < 10:  # Changed from 3 to 10 to ensure we have the date field
        return json.dumps(default_json)
    
    try:
        time_str = data[0]
        latitude = data[1]
        longitude = data[2]
        date_str = data[9]
        
        # Convert UTC time to KST
        utc_time = datetime.strptime(f"{date_str} {time_str}", "%d%m%y %H%M%S.%f")
        kst_time = utc_time + timedelta(hours=9)
        
        # Convert latitude and longitude to decimal degrees
        lat_deg = float(latitude[:2]) + float(latitude[2:-1])/60
        lat_direction = latitude[-1]
        lon_deg = float(longitude[:3]) + float(longitude[3:-1])/60
        lon_direction = longitude[-1]
        
        # Add minus sign for South and West
        if lat_direction == 'S':
            lat_deg = -lat_deg
        if lon_direction == 'W':
            lon_deg = -lon_deg
        
        gps_json = {
            "time": kst_time.strftime('%Y-%m-%d %H:%M:%S'),
            "latitude": round(lat_deg, 6),
            "longitude": round(lon_deg, 6)
        }
        
        return json.dumps(gps_json)
    except Exception as e:
        default_json["error"] = f"GPS data parsing error: {str(e)}"
        return json.dumps(default_json)

def parse_arguments():
    parser = argparse.ArgumentParser(description="GPS Data Sender")
    parser.add_argument('--server', type=str, default=CCU_IP_ADDR, 
                        help="Server IP address (default: {CCU_IP_ADDR})")
    parser.add_argument('--port', type=int, default=CCU_PORT, help="Server port (default: {CCU_PORT})")
    parser.add_argument('--interval', type=int, default=30, help="Sending interval in seconds (default: 30)")
    return parser.parse_args()

def main(server_ip, server_port, interval):
    ser = setup_serial()
    if ser is None:
        print("Serial port not available, exiting program.")
        return

    sock = setup_socket()
    if sock is None:
        print("Socket not available, exiting program.")
        ser.close()
        return

    setup_gps(ser)
    
    try:
        while True:
            gps_data = get_gps_location(ser)
            parsed_data = parse_gps_data(gps_data)
            print(parsed_data)
            
            # Convert to JSON string and encode to bytes
            json_message = json.dumps(parsed_data).encode('utf-8')
            data_length = len(json_message)

            # Pack the header fields into a byte sequence
            header = struct.pack(
                '>BBHHHHH',                             # Format: Big-endian, 2x 1-byte, 5x 2-byte
                SourceDestID.CAN.value,                 # 1 byte (source_id)
                SourceDestID.LTE.value,                 # 1 byte (destination_id)
                ServiceID.VEHICLE_INFORMATION.value,    # 2 bytes (service_id)
                VEHICLE_MESSAGE_TYPES.LAST_VEHICLE_INFORMATION.value,  # 2 bytes (message_type)
                0x0011,                                 # 2 bytes (ift_id)
                0x0001,                                 # 2 bytes (ift_type)
                data_length                             # 2 bytes (data_length)
            )

            # Combine the header and the JSON message (both in bytes)
            full_message = header + json_message

            print(f"Sending Full message: {full_message}")


            send_to_server(sock, full_message, server_ip, server_port)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        ser.close()
        sock.close()
        print("Serial port and UDP socket closed")

if __name__ == "__main__":
    args = parse_arguments()
    print(f"Server IP: {args.server}, Port: {args.port}, Interval: {args.interval}")
    main(args.server, args.port, args.interval)