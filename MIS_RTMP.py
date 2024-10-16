# MIS_RTMP_UDP.py: RTMP (Real-Time Monitoring Proxy) for MIS (Monitoring Information System) using UDP
import socket
import threading

class Proxy:
    def __init__(self, client_host, client_port, server_host, server_port):
        self.client_host = client_host
        self.client_port = client_port
        self.server_host = server_host
        self.server_port = server_port

    def handle_client(self):
        # 클라이언트와 서버 간 데이터 전송 (바이패스)
        client_to_server = threading.Thread(target=self.forward_data, args=(self.client_host, self.client_port, self.server_host, self.server_port))
        #server_to_client = threading.Thread(target=self.forward_data, args=(self.server_host, self.server_port, self.client_host, self.client_port))

        client_to_server.start()
        #server_to_client.start()

        client_to_server.join()
        #server_to_client.join()

    def forward_data(self, source_host, source_port, dest_host, dest_port):
        try:
            # 소스 소켓 생성
            source_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            source_socket.bind((source_host, source_port))
            print(f"{source_host}, {source_port}")

            # 데이터를 수신하고 목적지로 전송
            while True:
                data, addr = source_socket.recvfrom(4096)
                if len(data) == 0:
                    break
                print(f"데이터 전달 중: {data[:50]}...")  # 데이터 일부 출력

                # 목적지 소켓을 통해 데이터 전송
                dest_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                dest_socket.sendto(data, (dest_host, dest_port))
        except Exception as e:
            print(f"데이터 전달 중 오류: {e}")
        finally:
            source_socket.close()

    def start(self):
        print(f"UDP 바이패스 디바이스가 {self.client_host}:{self.client_port}에서 시작되었습니다.")
        self.handle_client()

if __name__ == "__main__":
    server_host = input("타겟 IP 주소를 입력하세요 (기본값: 127.0.0.1): ") or "127.0.0.1"
    server_port = int(input("타겟 포트를 입력하세요 (기본값: 12345): ") or 12345)
    client_host = input("프록시 IP 주소를 입력하세요 (기본값: 127.0.0.1): ") or "127.0.0.1"
    client_port = int(input("프록시 포트를 입력하세요 (기본값: 54321): ") or 54321)

    proxy = Proxy(client_host, client_port, server_host, server_port)
    proxy.start()
