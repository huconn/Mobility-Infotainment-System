import socket
import time
import random
import string  

class UDPClient:
    def __init__(self, server_host='localhost', server_port=12345, message_size=64, count_input=1, delay_ms=1000):
        self.server_host = server_host
        self.server_port = server_port
        self.message_size = message_size  
        self.count = count_input
        self.delay_ms = delay_ms  
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        print(f"{self.server_host}:{self.server_port}의 서버에 연결")
        self.send_messages()

    def generate_random_message(self, size):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

    def send_messages(self):
        for i in range(self.count):
            try:
                message_to_send = self.generate_random_message(self.message_size)
                message_info = f"Message {i+1}/{self.count} (size: {self.message_size} bytes)"
                self.sock.sendto(message_to_send.encode('utf-8'), (self.server_host, self.server_port))
                print(f"{message_info}: {message_to_send[:50]}...")
                time.sleep(self.delay_ms / 1000) 
            except Exception as e:
                print(f"Error: {str(e)}")

        print("Complete the all message sending")
        self.sock.close()

if __name__ == "__main__":
    server_host = input("서버 IP 주소를 입력하세요 (기본값: localhost): ") or 'localhost'
    server_port = int(input("서버 포트 번호를 입력하세요 (기본값: 12345): ") or 12345)
    count_input = int(input("전송할 메시지 갯수를 입력하세요 (1-100, 기본값: 5): ") or 5)
    message_size = int(input("전송할 메시지 크기를 입력하세요 (1-1024(byte), 기본값: 64): ") or 64)
    delay_ms = int(input("전송 간격을 밀리초(ms) 단위로 입력하세요 (기본값: 3ms): ") or 3)

    client = UDPClient(server_host, server_port, message_size, count_input, delay_ms)
    client.start()
