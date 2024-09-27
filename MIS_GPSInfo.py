import serial
import time
import requests
from datetime import datetime, timedelta
import socket
import argparse
import json

# Serial port configuration
ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=1)

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Function to send AT command and read response
def send_at_command(command):
    ser.write((command + '\r\n').encode())
    time.sleep(1)
    response = ''
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode()
    return response.strip()

# GPS initial setup
def setup_gps():
    commands = [
        'AT+QGPS=1',
        'AT+QGPS?',
        'AT+QGPSCFG="gnssconfig"',
        'AT+QGPSCFG="gpsnmeatype",1'
    ]
    for cmd in commands:
        response = send_at_command(cmd)
        print(f"Command: {cmd}\nResponse: {response}\n")

# Get GPS location information
def get_gps_location():
    response = send_at_command('AT+QGPSLOC?')
    return response

# Send data to server
def send_to_server(data, server_ip, server_port):
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
    parser.add_argument('--server', type=str, default='localhost', 
                        help="Server IP address (default: localhost)")
    parser.add_argument('--port', type=int, default=5001, help="Server port (default: 5001)")
    parser.add_argument('--interval', type=int, default=30, help="Sending interval in seconds (default: 30)")
    return parser.parse_args()

def main(server_ip, server_port, interval):
    setup_gps()
    
    try:
        while True:
            gps_data = get_gps_location()
            parsed_data = parse_gps_data(gps_data)
            print(parsed_data)
            
            send_to_server(parsed_data, server_ip, server_port)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        ser.close()
        sock.close()
        print("Serial port and UDP socket closed")

if __name__ == "__main__":
    args = parse_arguments()
    main(args.server, args.port, args.interval)