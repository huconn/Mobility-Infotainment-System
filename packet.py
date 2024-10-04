# packet.py
# Description: This file contains the ProtocolPacket class which is used to create, pack, and unpack protocol packets.

from logger import Logger 
import struct
from enum import Enum
import argparse
import json

# Define the global variables
PROTOCOL_LEN = 8
MAX_PAYLOAD_LEN = 65535


# Define the source and destination IDs
class LabeledEnum(Enum):
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj

    def __str__(self):
        return self.label
    
    @classmethod
    def convert(cls, input_value):
        if isinstance(input_value, str):
            return cls.get_value_by_label(input_value)
        elif isinstance(input_value, int):
            return cls.get_label_by_value(input_value)
        else:
            raise ValueError(f"Unsupported input type: {type(input_value)}")

    @classmethod
    def L2V(cls, label):
        print(f"Label: {label}")
        for member in cls:
            if member.label == label:
                return member.value
        raise ValueError(f"No matching enum found for label: {label}")

    @classmethod
    def V2L(cls, value):
        for member in cls:
            if member.value == value:
                return member.label
        raise ValueError(f"No matching enum found for value: {value}")
    

class SourceDestID(LabeledEnum):
    CCU = (0x00, "CCU")
    LTE = (0x01, "LTE")
    CAN = (0x02, "CAN")
    WAVE = (0x03, "WAVE")
    D_IVI = (0x05, "D-IVI")
    P_IVI_1 = (0x06, "P-IVI-1")
    P_IVI_2 = (0x07, "P-IVI-2 RSE_LEFT")
    P_IVI_3 = (0x08, "P-IVI-3 RSE_RIGHT")
    CLOUD = (0x09, "Cloud")

# Define the service IDs
class ServiceID(LabeledEnum):
    VEHICLE_INFORMATION = (0x0000, "Vehicle Information")
    D_IVI_CONTROL = (0x0001, "D-IVI Control")
    P_IVI_CONTROL = (0x0002, "P-IVI Control")
    OTT_CONTROL = (0x0003, "OTT Control")
    BLOCKCHAIN_AUTHENTICATION = (0x0004, "Blockchain Authentication")
    
# Define the message types for each service
class VEHICLE_MESSAGE_TYPES(LabeledEnum):
    LAST_VEHICLE_INFORMATION = (0x0000, "Last Vehicle Information")
    
class D_IVI_CONTROL_MESSAGE_TYPES(LabeledEnum):
    D_IVI_CONTROL_REQUEST = (0x0000, "D-IVI Control Request")
    D_IVI_CONTROL_RESPONSE = (0x0001, "D-IVI Control Response")
    
class P_IVI_CONTROL_MESSAGE_TYPES(LabeledEnum):
    P_IVI_CONTROL_REQUEST = (0x0000, "P-IVI Control Request")
    P_IVI_CONTROL_RESPONSE = (0x0001, "P-IVI Control Response")
    
class OTT_LOGIN_MESSAGE_TYPES(LabeledEnum):
    OTT_LOGIN_REQUEST = (0x0000, "OTT Login Request")
    OTT_LOGIN_RESPONSE = (0x0001, "OTT Login Response")
    
class BLOCKCHAIN_MESSAGE_TYPES(LabeledEnum):
    BLOCKCHAIN_AUTHENTICATION_REQUEST = (0x0000, "Blockchain Authentication Request")
    BLOCKCHAIN_AUTHENTICATION_RESPONSE = (0x0001, "Blockchain Authentication Response")
    

# Define the IFT IDs
class IFTID(LabeledEnum):
    IFT_12_01 = (0x0001, "D-IVI에서 P-IVI RSE 미디어 제어 (콘텐츠 실행)")
    IFT_12_02 = (0x0002, "D-IVI에서 P-IVI RSE 미디어 제어 (사운드 mute)")
    IFT_12_03 = (0x0003, "D-IVI에서 P-IVI & RSE에 운전자 졸음/부주의 운전 경고 등 DMS 관련 메시지 출력")
    IFT_12_04 = (0x0004, "D-IVI에서 P-IVI & RSE에 운전자 상태 긴급 경고 메시지 출력 (긴급상태: 졸도 등 의식불명 상태)")
    IFT_12_05 = (0x0005, "위치기반 서비스")
    IFT_13_01 = (0x0006, "D-IVI에서 Cloud에 차량 정보를 제공")
    IFT_13_02 = (0x0007, "D-IVI에서 Cloud에 운전자 정보를 제공 (운전자 정보: 이름, 프로필 이미지, 이메일, 전화번호, 기타)")
    IFT_13_03 = (0x0007, "D-IVI에서 Cloud에 차량의 주행 정보를 제공")
    IFT_13_04 = (0x0008, "D-IVI에서 Cloud에 DSM 상태 정보를 제공")
    IFT_13_05 = (0x0009, "D-IVI에서 Cloud에 차량 진단/상태 정보 제공")
    IFT_13_06 = (0x000A, "D-IVI에서 Cloud에 운전자 긴급 상황 정보 제공")
    IFT_23_01 = (0x000B, "P-IVI에서 Cloud에 사용자 정보를 제공")
    IFT_23_02 = (0x000C, "P-IVI에서 Cloud에 미디어 정보를 제공")
    IFT_23_03 = (0x000D, "P-IVI에서 Cloud에 시스템 정보를 제공")

# Define the IFT types
class IFT_12_01_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] 콘텐츠 선택 버튼 입력 (고정된 콘텐츠 사용 유무 협의)")
    TYPE_0002 = (0x0002, "[R] 콘텐츠 선택 완료")
    TYPE_0003 = (0x0003, "[D] 콘텐츠 실행/일시정지/종료 입력")
    TYPE_0004 = (0x0004, "[R] 해당 콘텐츠 실행/일시정지/종료 수행")
    TYPE_0005 = (0x0005, "[R] 실행 콘텐츠 정보 D-IVI에 송신")
    TYPE_0006 = (0x0006, "[D] D에서 P, R 화면 터치, 버튼 on/off 제어 ( P/R의 콘텐츠 제어권 통제 )")

class IFT_12_02_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] P/R의 자체 오디오 출력 MUTE 버튼 입력")
    TYPE_0002 = (0x0002, "[P, R]의 자체 오디오 음소거 및 음소거 알림 표시 출력")
    TYPE_0003 = (0x0003, "[P, R] 자체 오디오 음소거 해제 및 음소거 해제 알림 표시 출력")

class IFT_12_03_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] 운전자 상태 인식 판단 저장")
    TYPE_0002 = (0x0002, "[D] 운전자 상태 경고 메시지 송신")
    TYPE_0003 = (0x0003, "[P, R] 운전 상태 경고 알림 표시 출력")
    TYPE_0004 = (0x0004, "[D] 운전자 상태 경고 해제 메시지 송신")
    TYPE_0005 = (0x0005, "[P, R] 운전 상태 경고 해제 알림 표시 출력")

class IFT_12_04_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] 운전자 상태 긴급 상황 인식 판단")
    TYPE_0002 = (0x0002, "[D] 운전자 상태 긴급 상황 경고 메시지 송신")
    TYPE_0003 = (0x0003, "[P, R] 운전자 긴급 상황 경고 알림 표시 출력")
    TYPE_0004 = (0x0004, "[D] 운전자 상태 긴급 상황 경고 해제 메시지 송신")
    TYPE_0005 = (0x0005, "[P, R] 운전자 상태 긴급 상황 경고 해제 알림 표시 출력")

class IFT_12_05_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] 위치정보 송신")
    TYPE_0002 = (0x0002, "[P] 세차 정비소 관련 서비스 수행")

class IFT_13_01_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[B] USB에 차량에 대한 정보를 운전자 정보와 매칭해서 저장(DID로 관리)")
    TYPE_0002 = (0x0002, "[B] 차량 정보를 VP 형식으로 변환")
    TYPE_0003 = (0x0003, "[D] 차량 정보를 송신")
    TYPE_0004 = (0x0004, "[B] 차량 정보 복호화")
    TYPE_0005 = (0x0005, "[C] 차량 정보를 수신하여 서비스 수행 - 차량 정보 표출 서비스")
    TYPE_0006 = (0x0006, "[C] 수집된 차량 정보 기반으로 차량에 대한 셀프 체크 메시지 & 경고 메시지 송신")

class IFT_13_02_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[B] USB에 운전자 정보 저장 및 DID 발급 (운전자 정보는 협의 필요)")
    TYPE_0002 = (0x0002, "[B] 운전자 정보를 VP 형식으로 변환")
    TYPE_0003 = (0x0003, "[D] 운전자 정보를 송신")
    TYPE_0004 = (0x0004, "[B] 운전자 정보 복호화")
    TYPE_0005 = (0x0005, "[C] 운전자 정보를 수신하여 서비스 수행 - 운전자 정보 표출 서비스")

class IFT_13_03_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[C] 현재의 주행 정보를 전송")
    TYPE_0002 = (0x0002, "[C] 차량 주행 정보 그룹 1")
    TYPE_0003 = (0x0003, "[C] 차량 주행 정보 그룹 2")
    TYPE_0004 = (0x0004, "[B] 차량 주행 정보를 USB 내 키로 암호화")
    TYPE_0005 = (0x0005, "[B] 차량 주행 정보를 송신")
    TYPE_0006 = (0x0006, "[B] 차량 주행 정보 복호화")
    TYPE_0007 = (0x0007, "[C] 주행 정보를 수신하여 서비스 수행 - 주행 정보 표시 - 주행 경로 이탈 분석 및 알림 제공 - 배송위치 이탈 경고, 배송시간 누락 경고")

class IFT_13_04_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] DMS 상태 정보 미리 저장 (DMS 상태 정보는 협의 필요)")
    TYPE_0002 = (0x0002, "[B] DMS 정보 USB 내 키로 암호화")
    TYPE_0003 = (0x0003, "[D] DMS 상태 정보를 송신")
    TYPE_0004 = (0x0004, "[B] DMS 정보 복호화")
    TYPE_0005 = (0x0005, "[C] DMS 상태 정보를 수신하여 서비스 수행 - 안내말 및 상태메시지 알림제공")

class IFT_13_05_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[D] 차량 시동시 초기 진단 실시 그룹1")
    TYPE_0002 = (0x0002, "[D] 차량 시동시 초기 진단 실시 그룹2")
    TYPE_0003 = (0x0003, "[D] 차량 초기 진단 결과 메시지 저장 그룹1")
    TYPE_0004 = (0x0004, "[D] 차량 초기 진단 결과 메시지 저장 그룹2")
    TYPE_0005 = (0x0005, "[B] 차량 초기 진단 정보를 USB 내 키로 암호화")
    TYPE_0006 = (0x0006, "[D] 차량 초기 진단 정보를 송신")
    TYPE_0007 = (0x0007, "[B] 차량 진단 정보 복호화")
    TYPE_0008 = (0x0008, "[C] 차량 초기 정보를 수신하여 서비스 수행 - 차량 상태 이력 관리 - 차량 진단상태 분석 후 알림 제공 - 운전자 맞춤형 관리서비스")

class IFT_13_06_Type(LabeledEnum):
    TYPE_0010 = (0x0010, "[D] 주행중 차량 진단/경고등 정보 취득 그룹1")
    TYPE_0011 = (0x0011, "[D] 주행중 차량 진단/경고등 정보 취득 그룹2")
    TYPE_0012 = (0x0012, "[D] 차량 주행중/진단/경고 메시지 저장 그룹1")
    TYPE_0013 = (0x0013, "[D] 차량 주행중/진단/경고 메시지 저장 그룹2")
    TYPE_0014 = (0x0014, "[B] 차량 주행중 진단 정보를 USB 내 키로 암호화")
    TYPE_0015 = (0x0015, "[B] 차량 주행중 진단 정보를 송신")
    TYPE_0016 = (0x0016, "[B] 차량 주행중 진단 정보 복호화")
    TYPE_0017 = (0x0017, "[C] 차량 주행중 진단 정보를 수신하여 서비스 수행 - 연료상태 점검 및 알림 - 점검 주기 알림 및 예약 - 주행 진단에 따른 연비 향상 방안 제공")

class IFT_23_01_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[B] USB에 사용자 정보 저장 및 DID 발급 (사용자 정보는 협의 필요)")
    TYPE_0002 = (0x0002, "[B] 사용자 정보를 VP 형식으로 변환")
    TYPE_0003 = (0x0003, "[P] 사용자 정보를 송신")
    TYPE_0004 = (0x0004, "[B] 사용자 정보 복호화")
    TYPE_0005 = (0x0005, "[C] 사용자 정보 수신하여 서비스 수행 - 동승자별 추천 컨텐츠 my pick 정보 제공")

class IFT_23_02_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[B] 사용자 정보를 USB 내 키로 암호화")
    TYPE_0002 = (0x0002, "[P] 미디어 사용 정보를 송신")
    TYPE_0003 = (0x0003, "[B] 사용자 정보 복호화")
    TYPE_0004 = (0x0004, "[C] 미디어 사용 정보 수신하여 서비스 수행 - 동승자 추천 컨텐츠 Top10정보 제공")

class IFT_23_03_Type(LabeledEnum):
    TYPE_0001 = (0x0001, "[P] USB에 시스템 정보 저장 및 사용자 DID 연계 (시스템 정보 필요)")
    TYPE_0002 = (0x0002, "[B] 시스템 정보를 VP 형식으로 변환")
    TYPE_0003 = (0x0003, "[P] 시스템 정보를 송신")
    TYPE_0004 = (0x0004, "[B] 시스템 정보 복호화")
    TYPE_0005 = (0x0005, "[C] 시스템 정보 수신하여 서비스 수행 - 시스템 및 펌웨어 버전 확인 및 OTA 업데이트 알림 제공")

#  Map the IFT IDs to their corresponding IFT types
IFT_TYPE_MAP = {
    IFTID.IFT_12_01: IFT_12_01_Type,
    IFTID.IFT_12_02: IFT_12_02_Type,
    IFTID.IFT_12_03: IFT_12_03_Type,
    IFTID.IFT_12_04: IFT_12_04_Type,
    IFTID.IFT_12_05: IFT_12_05_Type,
    IFTID.IFT_13_01: IFT_13_01_Type,
    IFTID.IFT_13_02: IFT_13_02_Type,
    IFTID.IFT_13_03: IFT_13_03_Type,
    IFTID.IFT_13_04: IFT_13_04_Type,
    IFTID.IFT_13_05: IFT_13_05_Type,
    IFTID.IFT_13_06: IFT_13_06_Type,
    IFTID.IFT_23_01: IFT_23_01_Type,
    IFTID.IFT_23_02: IFT_23_02_Type,
    IFTID.IFT_23_03: IFT_23_03_Type
}

# service id to message type map
SERVICE_MESSAGE_TYPE_MAP = {
    ServiceID.VEHICLE_INFORMATION: VEHICLE_MESSAGE_TYPES,
    ServiceID.D_IVI_CONTROL: D_IVI_CONTROL_MESSAGE_TYPES,
    ServiceID.P_IVI_CONTROL: P_IVI_CONTROL_MESSAGE_TYPES,
    ServiceID.OTT_CONTROL: OTT_LOGIN_MESSAGE_TYPES,
    ServiceID.BLOCKCHAIN_AUTHENTICATION: BLOCKCHAIN_MESSAGE_TYPES
}

# service id to ift id map
SERVICE_IFT_ID_MAP = {
    ServiceID.D_IVI_CONTROL: [
        IFTID.IFT_12_01,
        IFTID.IFT_12_02,
        IFTID.IFT_12_03,
        IFTID.IFT_12_04,
        IFTID.IFT_12_05,
        IFTID.IFT_13_01,
        IFTID.IFT_13_02,
        IFTID.IFT_13_03,
        IFTID.IFT_13_04,
        IFTID.IFT_13_05,
        IFTID.IFT_13_06
    ],
    ServiceID.P_IVI_CONTROL: [
        IFTID.IFT_23_01,
        IFTID.IFT_23_02,
        IFTID.IFT_23_03
    ]
}

# ift id to service id map
IFT_ID_SERVICE_ID_MAP = {
    IFTID.IFT_12_01: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_12_02: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_12_03: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_12_04: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_12_05: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_01: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_02: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_03: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_04: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_05: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_13_06: ServiceID.D_IVI_CONTROL,
    IFTID.IFT_23_01: ServiceID.P_IVI_CONTROL,
    IFTID.IFT_23_02: ServiceID.P_IVI_CONTROL,
    IFTID.IFT_23_03: ServiceID.P_IVI_CONTROL
}

# Service ProtocolPacket
# Source ID: 1byte
# Dest ID: 1byte
# Service ID: 2byte
# Message Type: 2byte
# IFT ID : 2byte
# IFT Type : 2byte
# Data Length : 2byte
# Payload Data: 0~65535   

# Protocol Packet Class
class ProtocolPacket:
    def __init__(self, source_id, dest_id, service_id, message_type, ift_id=0, ift_type=0, data_length=0, payload_data=None):
        # self.source_id = SourceDestID.L2V(source_id)       # 1 bytes
        # self.dest_id = SourceDestID.L2V(dest_id)           # 1 byte
        # self.service_id = ServiceID.L2V(service_id)        # 2 bytes
        self.source_id = source_id      # 1 bytes
        self.dest_id = dest_id          # 1 bytes
        self.service_id = service_id    # 1 bytes

        #message_type_enum = SERVICE_MESSAGE_TYPE_MAP[self.service_id]
        #self.message_type = message_type_enum.L2V(message_type)
        self.message_type = message_type # 2 bytes
        self.ift_id = ift_id             # 2 bytes
        self.ift_type = ift_type         # 2 bytes
        self.data_length = data_length   # 2 bytes
        self.payload_data = payload_data # 0~65535 bytes

    def add_payload_data(self, data):
        """Add or update payload data."""
        if isinstance(data, str):
            self.payload_data = data.encode('utf-8')  # 문자열은 바이트로 변환
        else:
            self.payload_data = data
        self.data_length = len(self.payload_data)

    def pack(self):
        """Pack the header and payload into a binary format."""
        header = struct.pack('!BBHHHHH', 
                             self.source_id,
                             self.dest_id,
                             self.service_id,
                             self.message_type,
                             self.ift_id,
                             self.ift_type,
                             self.data_length)
        
        # payload_data가 문자열이면 바이트로 변환
        if isinstance(self.payload_data, str):
            payload_data = self.payload_data.encode('utf-8')
        else:
            payload_data = self.payload_data

        if self.data_length > 0:
            return header + payload_data
        else:
            return header
    
    def to_json(self):
        payload_data = None
        if self.payload_data:
            try:
                payload_data = json.loads(self.payload_data.decode('utf-8'))
            except json.JSONDecodeError:
                payload_data = self.payload_data.decode('utf-8')

        return {
            "source_id": self.source_id,
            "dest_id": self.dest_id,
            "service_id": self.service_id,
            "message_type": self.message_type,
            "ift_id": self.ift_id,
            "ift_type": self.ift_type,
            "data_length": self.data_length,
            "payload_data": payload_data
        }

    @staticmethod
    def unpack(packet_data):
        # struct.unpack
        header = packet_data[:12]
        payload_data = packet_data[12:]
        unpacked_data = struct.unpack('!BBHHHHH', header)

        # get source id
        # source_id = SourceDestID(unpacked_data[0])
        source_id = unpacked_data[0]
        
        # get dest id
        #dest_id = SourceDestID(unpacked_data[1])
        dest_id = unpacked_data[1]

        # get service id
        #service_id = ServiceID(unpacked_data[2])
        service_id = unpacked_data[2]

        # get message type
        #message_type = ProtocolPacket.get_message_type(service_id, unpacked_data[3])
        message_type = unpacked_data[3]

        # get ift id
        #ift_id = ProtocolPacket.get_ift_id(unpacked_data[2])
        ift_id = unpacked_data[4]

        # get ift type
        #ift_type = ProtocolPacket.get_ift_type(ift_id)
        ift_type = unpacked_data[5]
        
        # get data length
        data_length = unpacked_data[6]

        packet = ProtocolPacket(source_id, 
                              dest_id, 
                              service_id, 
                              message_type,
                              ift_id, 
                              ift_type, 
                              data_length, 
                              payload_data)
        return packet.to_json()
    
    def get_message_type(service_id, message_type):
        if service_id in SERVICE_MESSAGE_TYPE_MAP:
            message_types = SERVICE_MESSAGE_TYPE_MAP[service_id]
            if message_type in message_types:
                return message_types[message_type]
            else:
                raise ValueError("Message Type does not exist for the specified Service ID.")
        else:
            raise ValueError("Service ID does not have a corresponding Message Type mapping.")

    def get_ift_id(id):
        if id in IFTID:
            return IFTID(id)
        else:
            raise ValueError("IFT ID does not exist.")

    def get_ift_type(ift_id):
            if ift_id in IFT_TYPE_MAP:
                return IFT_TYPE_MAP[ift_id]
            else:
                raise ValueError("IFT ID does not have a corresponding IFT Type mapping.")

    def __str__(self):
        return f"Source ID: {self.source_id}, Dest ID: {self.dest_id}, Service ID: {self.service_id}, Message Type: {self.message_type}, IFT ID: {self.ift_id}, IFT Type: {self.ift_type}, Data Length: {self.data_length}, Payload Data: {self.payload_data}"


# Set Packet processing ===========================================================================================================================
# send ift type 
def send_ift_type(ift_id, ift_type, logger):
    logger.message("INFO", "IFT", f"Sending IFT Type: {ift_type.name} ({ift_type.value}) for IFT ID: {ift_id.name} ({ift_id.value})")

