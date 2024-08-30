# udp.py 
# The udp.py file contains a class called UDP that is used to send and receive UDP messages. 

import socket
import struct
import argparse
import threading
import time
from time import sleep
import netifaces
import netaddr
from packet import *

class UDP_Control:
    def __init__(self, system, src_ip_addr, src_port, logger):
        self.system = system
        self.src_ip_addr = src_ip_addr
        self.src_port = src_port
        self.logger = logger
        self.previous_time = time.time()

        self.logger.message("INFO", "UDP", f"Source IP Address: {self.src_ip_addr}")
        self.logger.message("INFO", "UDP", f"Source Port: {self.src_port}")

    def handle_error(self, error_msg):
        self.logger.message("ERROR", "error", f"Error: {error_msg}")

    def get_default_interface(self):
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

    # Set UDP server
    def udp_server(self, message_handler=None):
        try:

            host = self.src_ip_addr
            port = self.src_port

            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_sock.bind((host, port))

            self.logger.message("INFO", "server", f"{self.system}: {host}:{port}")
            
            while True:
                received_data, addr = udp_sock.recvfrom(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
                udp_client_ip = addr[0]
                
                # current_time = time.time()
                # elapsed_time = current_time - self.previous_time
                # self.previous_time = current_time
                #self.logger.message("INFO", "Received", f"[{self.previous_time:.6f}:{elapsed_time:.6f}] ({udp_client_ip}): {received_data}")
                #self.logger.message("INFO", "Received", f"[E:{elapsed_time:.6f}:{udp_client_ip}] {received_data}")
                self.logger.message("INFO", "Received", f"[{udp_client_ip}] {received_data}")

                if message_handler:
                    message_handler(received_data)
                elif message_handler is None:
                    self.logger.message("INFO", "Received", "No message handler provided.")

        except ConnectionRefusedError:
            print(f"Connection to {host}:{port} refused.")
        except Exception as e:
            print(f"An error occurred while receiving the UDP message: {e}")


    # Set UDP Client ===========================================================================================================================
    def udp_client(self, dest_ip_addr, dest_port, data=None):
        try:
            self.logger.message("INFO", "send", f"[{dest_ip_addr}:{dest_port}] {data}")

            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.sendto(data, (dest_ip_addr, dest_port))
        except ConnectionRefusedError:
            print(f"Connection to {dest_ip_addr}:{dest_port} refused.")
        except Exception as e:
            print(f"An error occurred while sending the UDP message: {e}")
        finally:
            udp_sock.close()

    # Set UDP Sender ===========================================================================================================================
    def udp_sender(self, dest_ip_addr, dest_port, send_data, send_count):
        self.logger.message("INFO", "SEND", f"send after 1ms {dest_ip_addr}:{dest_port}")

        count = 0
        while send_data is not None:
            try:
                self.udp_client(dest_ip_addr, dest_port, send_data)
                if send_count > 0:
                    count += 1
                    if count >= send_count:
                        break

                sleep(0.001)
            except Exception as e:
                self.handle_error(str(e))