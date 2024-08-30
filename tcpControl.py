# tcp.py
# The tcp.py file contains a class called TCP that is used to send and receive TCP messages.

import socket
import struct
import argparse
import time
from time import sleep
import netifaces
import netaddr
from packet import *

class TCP_Control:
    def __init__(self, system, src_ip_addr, src_port, logger):
        self.system = system
        self.src_ip_addr = src_ip_addr
        self.src_port = src_port
        self.logger = logger

        self.logger.message("INFO", "TCP", f"Source IP Address: {self.src_ip_addr}")
        self.logger.message("INFO", "TCP", f"Source Port: {self.src_port}")

    def handle_error(self, error_msg):
        self.logger.message("ERROR", "error", f"Error: {error_msg}")

    def get_default_interface(self):
        routes = netifaces.gateways()
        
        if 'default' in routes and netifaces.AF_INET in routes['default']:
            return routes['default'][netifaces.AF_INET][1] 

        return None

    def get_interface_ip(self, interface_name):
        addresses = netifaces.ifaddresses(interface_name)
        if netifaces.AF_INET in addresses:
            for link in addresses[netifaces.AF_INET]:
                return link['addr']
        return None

    # Set TCP Server ===========================================================================================================================
    def tcp_server(self, message_handler=None):
        try:

            host = self.src_ip_addr
            port = self.src_port

            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_sock.bind((host, port))
            tcp_sock.listen(1)

            self.logger.message("INFO", "server", f"{self.system}: {host}:{port}")
            
            while True:
                conn, addr = tcp_sock.accept()
                received_data = conn.recv(PROTOCOL_LEN + MAX_PAYLOAD_LEN)
                tcp_client_ip = addr[0]
                self.logger.message("INFO", "Received", f"TCP client({tcp_client_ip}): {received_data}")

                if message_handler:
                    message_handler(received_data)
                elif message_handler is None:
                    self.logger.message("INFO", "Received", "No message handler provided.")

        except ConnectionRefusedError:
            print(f"Connection to {self.src_ip_addr}:{self.src_port} refused.")
        except Exception as e:
            print(f"An error occurred while sending the TCP message: {e}")

    # Set TCP Client ===========================================================================================================================
    def tcp_client(self, dest_ip_addr, dest_port, data):
        try:
            self.logger.message("INFO", "send", f"{dest_ip_addr}:{dest_port}: {data}")

            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.connect((dest_ip_addr, dest_port))
            tcp_sock.sendall(data.encode('utf-8'))
        except ConnectionRefusedError:
            print(f"Connection to {dest_ip_addr}:{dest_port} refused.")
        except Exception as e:
            print(f"An error occurred while sending the TCP message: {e}")
        finally:
            tcp_sock.close()

    # Set TCP Sender ===========================================================================================================================
    def tcp_sender(self, dest_ip_addr, dest_port, send_data, send_count):
        self.logger.message("INFO", "SEND", f"send after 1ms {dest_ip_addr}:{dest_port}")

        count = 0
        while send_data is not None:
            try:
                self.tcp_client(dest_ip_addr, dest_port, send_data)
                if send_count > 0:
                    count += 1
                    if count >= send_count:
                        break

                sleep(0.001)            
            except Exception as e:
                self.handle_error(str(e))