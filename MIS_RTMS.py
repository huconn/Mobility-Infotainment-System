# MIS_RTMS.py: RTMC (Real-Time Monitoring Server) for MIS (Monitoring Information System)

import socket
import time
import statistics

class UDPServer:
    def __init__(self, host='localhost', port=12345, num_messages=5, decimal_places=2):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.num_messages = num_messages  
        self.decimal_places = decimal_places  
        self.reset_measurements()  

    def reset_measurements(self):
        self.last_message_time = None
        self.response_times = []

    def start(self):
        print(f"서버 {self.host}:{self.port} 시작")
        self.receive_messages()

    def receive_messages(self):
        while True:
            message_count = 0
            while message_count < self.num_messages:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    current_time = time.time()
                    message = data.decode('utf-8')
                    
                    # 현재 시간을 마이크로초 단위로 표시
                    microseconds = int((current_time - int(current_time)) * 1000000)
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
                    time_str += f".{microseconds:06d}"  
                    
                    print(f"{addr}로부터 메시지 수신 - 사이즈: {len(message)}, 데이터: {message[:50]}...")
                    print(f"수신 시간(μs): {time_str}")
                    
                    if self.last_message_time is not None:
                        response_time = (current_time - self.last_message_time) * 1000 
                        self.response_times.append(response_time)
                        # 소수점 자릿수에 맞게 응답 시간 출력
                        print(f"응답 시간 계산: {response_time:.{self.decimal_places}f} ms")
                        
                    self.last_message_time = current_time
                    message_count += 1
                    
                except Exception as e:
                    print(f"메시지 수신 중 오류 발생: {str(e)}")
                    
            self.calculate_statistics()

    def calculate_statistics(self):
        # 수신된 메시지의 평균 응답 시간과 표준편차 출력
        if self.response_times:
            print("\n메세지 수집 공식: ====================================================")
            print("응답시간 수집 = Array(이전 메시지 수신시간 - 현재 메세지 수신시간)")
            print(f"총 {self.num_messages}개의 메시지 수신")
            print(f"총 {len(self.response_times)}개의 응답시간(μs) 수집")        
            for i in range(0, len(self.response_times), 10):
                chunk = self.response_times[i:i+10]
                print(chunk)

            print("\n평균 응답 공식: ====================================================")
            print("평균 응답시간 = ( Σ 응답시간_i ) / N")
            print(f"  Σ = 모든 응답시간의 합 {sum(self.response_times)}")
            print(f"  N = 응답시간 데이터의 개수 {len(self.response_times)}")
            average_response_time = sum(self.response_times) / len(self.response_times)
            average_response_time = round(average_response_time, decimal_places)
            print(f"평균 응답 시간: {average_response_time:.{self.decimal_places}f} ms")

            print("\n표준편차 공식: ====================================================")
            print("σ = √( Σ (xi - μ)² / N )")
            print("  σ = 표준편차 (Standard Deviation)")
            print("  Σ = 모든 데이터 값들의 합 (Summation)")
            print("  xi = 각 데이터 값 (Data points)")
            print("  μ = 평균 (Mean)")
            print("  N = 데이터의 개수 (Number of data points)")                
            response_time_stdev = statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0.0  # 표준편차 계산
            response_time_stdev = round(response_time_stdev, decimal_places)
            print(f"응답 시간의 표준편차: {response_time_stdev:.{self.decimal_places}f} ms")

            print(f"\n표준편차 백분율: ====================================================")
            print("표준편차 백분율 = ( 표준편차 / 평균 응답시간 ) * 100")
            stdev_percentage = (response_time_stdev / average_response_time) * 100 if average_response_time > 0 else 0.0
            stdev_percentage = round(stdev_percentage, decimal_places)
            print(f"표준편차 백분율: {stdev_percentage:.{self.decimal_places}f}%")

            print(f"\n===================================================================")
            print(f"평균 응답 시간: {average_response_time:.{self.decimal_places}f} ms")
            print(f"응답 시간의 표준편차: {response_time_stdev:.{self.decimal_places}f} ms")
            print(f"표준편차 백분율: {stdev_percentage:.{self.decimal_places}f}%")
            print(f"===================================================================\n")

        # 응답 시간 측정 변수 초기화
        self.reset_measurements()
            

class TCPServer:
    def __init__(self, host='localhost', port=12345, num_messages=5, decimal_places=2):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)  # 1개의 연결 대기
        self.num_messages = num_messages
        self.decimal_places = decimal_places
        self.reset_measurements()

    def reset_measurements(self):
        self.last_message_time = None
        self.response_times = []

    def start(self):
        print(f"TCP 서버 {self.host}:{self.port} 시작")
        self.receive_messages()

    def receive_messages(self):
        conn, addr = self.sock.accept()  # 클라이언트의 연결 수락
        print(f"클라이언트 {addr} 연결됨")

        message_count = 0
        while message_count < self.num_messages:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                current_time = time.time()
                message = data.decode('utf-8')

                microseconds = int((current_time - int(current_time)) * 1000000)
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
                time_str += f".{microseconds:06d}"

                print(f"{addr}로부터 메시지 수신 - 사이즈: {len(message)}, 데이터: {message[:50]}...")
                print(f"수신 시간(μs): {time_str}")

                if self.last_message_time is not None:
                    response_time = (current_time - self.last_message_time) * 1000
                    self.response_times.append(response_time)
                    print(f"응답 시간 계산: {response_time:.{self.decimal_places}f} ms")

                self.last_message_time = current_time
                message_count += 1

            except Exception as e:
                print(f"메시지 수신 중 오류 발생: {str(e)}")

        self.calculate_statistics()
        conn.close()

    def calculate_statistics(self):
        if self.response_times:
            print("\n메세지 수집 공식: ====================================================")
            print("응답시간 수집 = Array(이전 메시지 수신시간 - 현재 메세지 수신시간)")
            print(f"총 {self.num_messages}개의 메시지 수신")
            print(f"총 {len(self.response_times)}개의 응답시간(μs) 수집")        
            for i in range(0, len(self.response_times), 10):
                chunk = self.response_times[i:i+10]
                print(chunk)

            print("\n평균 응답 공식: ====================================================")
            print("평균 응답시간 = ( Σ 응답시간_i ) / N")
            print(f"  Σ = 모든 응답시간의 합 {sum(self.response_times)}")
            print(f"  N = 응답시간 데이터의 개수 {len(self.response_times)}")
            average_response_time = sum(self.response_times) / len(self.response_times)
            average_response_time = round(average_response_time, decimal_places)
            print(f"평균 응답 시간: {average_response_time:.{self.decimal_places}f} ms")

            print("\n표준편차 공식: ====================================================")
            print("σ = √( Σ (xi - μ)² / N )")
            print("  σ = 표준편차 (Standard Deviation)")
            print("  Σ = 모든 데이터 값들의 합 (Summation)")
            print("  xi = 각 데이터 값 (Data points)")
            print("  μ = 평균 (Mean)")
            print("  N = 데이터의 개수 (Number of data points)")                
            response_time_stdev = statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0.0  # 표준편차 계산
            response_time_stdev = round(response_time_stdev, decimal_places)
            print(f"응답 시간의 표준편차: {response_time_stdev:.{self.decimal_places}f} ms")

            print(f"\n표준편차 백분율: ====================================================")
            print("표준편차 백분율 = ( 표준편차 / 평균 응답시간 ) * 100")
            stdev_percentage = (response_time_stdev / average_response_time) * 100 if average_response_time > 0 else 0.0
            stdev_percentage = round(stdev_percentage, decimal_places)
            print(f"표준편차 백분율: {stdev_percentage:.{self.decimal_places}f}%")

            print(f"\n===================================================================")
            print(f"평균 응답 시간: {average_response_time:.{self.decimal_places}f} ms")
            print(f"응답 시간의 표준편차: {response_time_stdev:.{self.decimal_places}f} ms")
            print(f"변동 계수: {stdev_percentage:.{self.decimal_places}f}%")
            print(f"===================================================================\n")
        self.reset_measurements()

if __name__ == "__main__":
    protocol = input("사용할 프로토콜을 선택하세요 (UDP/TCP, 기본값: UDP): ").upper() or 'UDP'
    host = input("서버 IP 주소를 입력하세요 (기본값: localhost): ") or 'localhost'
    port = int(input("서버 포트 번호를 입력하세요 (기본값: 12345): ") or 12345)
    num_messages = int(input("응답시간에 수집할 메시지 갯수를 입력하세요 (기본값: 5): ") or 5)
    decimal_places = int(input("응답시간(ms) 추가 지표 소수점(μs) 자릿수를 입력하세요 (기본값: 0 ): ") or 0)

    if protocol == 'TCP':
        server = TCPServer(host, port, num_messages, decimal_places)
    else:
        server = UDPServer(host, port, num_messages, decimal_places)

    server.start()
