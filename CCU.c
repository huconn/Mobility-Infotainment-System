#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <errno.h>
#include <pthread.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>

#define PROTOCOL_LEN 128
#define MAX_PAYLOAD_LEN 65535

char udp_client_ip[INET_ADDRSTRLEN];
char tcp_client_ip[INET_ADDRSTRLEN];

void tcp_server(int argc, char *argv[]);
void udp_server(int argc, char *argv[]);
void tcp_client(const char *data, int port);
void udp_client(const char *data, int port);

struct Args {
    const char *ip_addr;
    int udp_port;
    int tcp_port;
};

struct ThreadArgs {
    const char *ip_addr;
    int tcp_port;
    int udp_port;
};

typedef struct {
    uint8_t source_id;
    uint8_t dest_id;
    uint16_t service_id;
    uint16_t message_type;
    uint16_t data_length;
    char *payload_data; 
} Message;


// 구조체 정의
typedef struct {
    const char *name;
    uint16_t value;
} MessageType;

typedef struct {
    const char *name;
    uint16_t value;
} ServiceID;

typedef struct {
    const char *name;
    uint8_t value;
} SourceDestID;

// 메시지 타입 초기화
MessageType LAST_VEHICLE_MESSAGE_TYPES[] = {
    {"Last Vehicle Information", 0x0000},
};

MessageType P_IVI_CONTROL_MESSAGE_TYPES[] = {
    {"P-IVI Control Request", 0x0000},
    {"P-IVI Control Response", 0x0001},
};

MessageType OTT_LOGIN_MESSAGE_TYPES[] = {
    {"OTT Login Request", 0x0000},
    {"OTT Login Response", 0x0001},
};

MessageType BLOCKCHAIN_MESSAGE_TYPES[] = {
    {"Blockchain Authentication Request", 0x0000},
    {"Blockchain Authentication Response", 0x0001}
};

MessageType MESSAGE_TYPES[] = {
    {"Last Vehicle Information", 0x0000},
    {"P-IVI Control Request", 0x0000},
    {"P-IVI Control Response", 0x0001},
    {"OTT Login Request", 0x0000},
    {"OTT Login Response", 0x0001},
    {"Blockchain Authentication Request", 0x0000},
    {"Blockchain Authentication Response", 0x0001}
};

// 서비스 ID 초기화
ServiceID SERVICE_IDS[] = {
    {"Vehicle Information", 0x0000},
    {"P-IVI Control", 0x0001},
    {"OTT", 0x0002},
    {"Blockchain Authentication", 0x0003}
};

// Source/Dest ID 초기화
SourceDestID SOURCE_DEST_IDS[] = {
    {"CCU", 0x00},
    {"D-IVI", 0x05},
    {"P-IVI1", 0x06},
    {"P-IVI2", 0x07}
};

void log_message(const char *protocol, const char *action, const char *message) {
    printf("[%s] %s: %s\n", protocol, action, message);
}

void handle_error(const char* error_msg) {
    log_message("", "Error: ", error_msg);
}

void parse_message(const char *data) {
    uint8_t source_id = data[0];
    uint8_t dest_id = data[1];
    uint16_t service_id = (data[2] << 8) | data[3];
    uint16_t message_type = (data[4] << 8) | data[5];
    uint16_t data_length_value = (data[6] << 8) | data[7];
    uint8_t *payload_data = data + 8;

    char source_id_name[50];
    char dest_id_name[50];
    char service_id_name[50];
    char message_type_name[50];

    // Find source ID name
    for (size_t i = 0; i < sizeof(SOURCE_DEST_IDS) / sizeof(SourceDestID); i++) {
        if (SOURCE_DEST_IDS[i].value == source_id) {
            strcpy(source_id_name, SOURCE_DEST_IDS[i].name);
            break;
        }
    }
    // Find dest ID name
    for (size_t i = 0; i < sizeof(SOURCE_DEST_IDS) / sizeof(SourceDestID); i++) {
        if (SOURCE_DEST_IDS[i].value == dest_id) {
            strcpy(dest_id_name, SOURCE_DEST_IDS[i].name);
            break;
        }
    }
    // Find service ID name
    for (size_t i = 0; i < sizeof(SERVICE_IDS) / sizeof(ServiceID); i++) {
        if (SERVICE_IDS[i].value == service_id) {
            strcpy(service_id_name, SERVICE_IDS[i].name);
            break;
        }
    }
    // Find message type name
    if (service_id == 0x0000) {
        for (size_t i = 0; i < sizeof(LAST_VEHICLE_MESSAGE_TYPES) / sizeof(MessageType); i++) {
            if (LAST_VEHICLE_MESSAGE_TYPES[i].value == message_type) {
                strcpy(message_type_name, LAST_VEHICLE_MESSAGE_TYPES[i].name);
                break;
            }
        }
    } else if (service_id == 0x0001) {
        for (size_t i = 0; i < sizeof(P_IVI_CONTROL_MESSAGE_TYPES) / sizeof(MessageType); i++) {
            if (P_IVI_CONTROL_MESSAGE_TYPES[i].value == message_type) {
                strcpy(message_type_name, P_IVI_CONTROL_MESSAGE_TYPES[i].name);
                break;
            }
        }
    } else if (service_id == 0x0002) {
        for (size_t i = 0; i < sizeof(OTT_LOGIN_MESSAGE_TYPES) / sizeof(MessageType); i++) {
            if (OTT_LOGIN_MESSAGE_TYPES[i].value == message_type) {
                strcpy(message_type_name, OTT_LOGIN_MESSAGE_TYPES[i].name);
                break;
            }
        }
    } else if (service_id == 0x0003) {
        for (size_t i = 0; i < sizeof(BLOCKCHAIN_MESSAGE_TYPES) / sizeof(MessageType); i++) {
            if (BLOCKCHAIN_MESSAGE_TYPES[i].value == message_type) {
                strcpy(message_type_name, BLOCKCHAIN_MESSAGE_TYPES[i].name);
                break;
            }
        }
    } else {
        strcpy(message_type_name, "Unknown");
    }

    // log_message 함수 호출 (이 함수는 이미 정의되어 있다고 가정)
    printf("Source ID: 0x%02X (%s)\n", source_id, source_id_name);
    printf("Dest ID: 0x%02X (%s)\n", dest_id, dest_id_name);
    printf("Service ID: 0x%04X (%s)\n", service_id, service_id_name);
    printf("Message Type: 0x%04X (%s)\n", message_type, message_type_name);
    printf("Data Length: 0x%04X\n", data_length_value);

    if (payload_data == NULL) {
        printf("Payload Data: None\n");
    } else {
        // payload_data 처리 (여기서는 출력만 함)
        printf("Payload Data: "); 
        for (size_t i = 0; i < data_length_value; i++) {
            printf("%02X ", payload_data[i]);
        }
        printf("\n");
    }
    printf("--------------------------------------------------------------------------------\n");
}

void udp_client(const char *data, int port) {
    struct sockaddr_in server_addr;
    int udp_sock, sent_bytes;

    // 소켓 생성
    udp_sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_sock == -1) {
        perror("Socket creation failed");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, tcp_client_ip, &server_addr.sin_addr);

    // 데이터 전송
    sent_bytes = sendto(udp_sock, data, strlen(data), 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
    if (sent_bytes < 0) {
        perror("Sendto failed");
    } else {
        log_message("UDP", "send", data);
    }

    close(udp_sock);
}

void udp_server(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <host> <port> <udp_port>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    int tcp_port = atoi(argv[3]);

    int udp_sock;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

    udp_sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_sock < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr(host);
    server_addr.sin_port = htons(port);

    if (bind(udp_sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    while (1) {
        log_message("UDP", "listening", "UDP server listening");

        char received_data[PROTOCOL_LEN + MAX_PAYLOAD_LEN];
        ssize_t bytes_received = recvfrom(udp_sock, received_data, sizeof(received_data) - 1, 0,
                                           (struct sockaddr *)&client_addr, &client_len);
        if (bytes_received < 0) {
            perror("recvfrom");
            continue;
        }

        received_data[bytes_received] = '\0';
        inet_ntop(AF_INET, &client_addr.sin_addr, udp_client_ip, sizeof(udp_client_ip));
        log_message("UDP", "Received", received_data);

        // Parse received data
        parse_message(received_data);

        // Send data to TCP client
        if (tcp_client_ip[0] != '\0') {
            tcp_client(received_data, tcp_port);
            log_message("UDP", "sent", received_data);
        }
    }

    close(udp_sock);
}

void tcp_client(const char *data, int port) {
    struct sockaddr_in server_addr;
    int tcp_sock, sent_bytes;

    // 소켓 생성
    tcp_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_sock == -1) {
        perror("Socket creation failed");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, udp_client_ip, &server_addr.sin_addr);

    // 연결
    if (connect(tcp_sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Connection failed");
        close(tcp_sock);
        return;
    }

    // 데이터 전송
    sent_bytes = send(tcp_sock, data, strlen(data), 0);
    if (sent_bytes < 0) {
        perror("Send failed");
    } else {
        log_message("TCP", "send", data);
    }

    close(tcp_sock);
}

void tcp_server(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <host> <port> <udp_port>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    int udp_port = atoi(argv[3]);

    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

    int tcp_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_sock < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr(host);
    server_addr.sin_port = htons(port);

    if (bind(tcp_sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(tcp_sock, 1) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    while (1) {
        log_message("TCP", "listening", "TCP server listening");
        
        int conn_sock = accept(tcp_sock, (struct sockaddr *)&client_addr, &client_len);
        if (conn_sock < 0) {
            perror("accept");
            continue;
        }

        inet_ntop(AF_INET, &client_addr.sin_addr, tcp_client_ip, sizeof(tcp_client_ip));
        char received_data[PROTOCOL_LEN + MAX_PAYLOAD_LEN];
        ssize_t bytes_received = recv(conn_sock, received_data, sizeof(received_data) - 1, 0);
        if (bytes_received < 0) {
            perror("recv");
            close(conn_sock);
            continue;
        }

        received_data[bytes_received] = '\0';
        log_message("TCP", "Received", received_data);

        // Parse received data
        parse_message(received_data);


        // Send data to TCP client
        if (udp_client_ip[0] != '\0') {
            udp_client(received_data, udp_port);
            log_message("UDP", "sent", received_data);
        }
    }

    close(tcp_sock);
}


void parse_args(int argc, char *argv[], struct Args *args) {

    if (argc < 4) {
        fprintf(stderr, "Usage: %s <IP Address> <UDP Port> <TCP Port>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    args->ip_addr = "127.0.0.1";
    args->udp_port = 50000;
    args->tcp_port = 50001;

    // 명령행 인자 처리
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--ip_addr") == 0 && i + 1 < argc) {
            args->ip_addr = argv[++i];
        } else if (strcmp(argv[i], "--udp_port") == 0 && i + 1 < argc) {
            args->udp_port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--tcp_port") == 0 && i + 1 < argc) {
            args->tcp_port = atoi(argv[++i]);
        }
    }
}

int main(int argc, char* argv[]) {
    struct Args args;
    parse_args(argc, argv, &args);

    printf("IP Address: %s\n", args.ip_addr);
    printf("UDP Port: %d\n", args.udp_port);
    printf("TCP Port: %d\n", args.tcp_port);


    struct ThreadArgs targs;
    targs.ip_addr = args.ip_addr;
    targs.tcp_port = args.tcp_port;
    targs.udp_port = args.udp_port;

    pthread_t tcp_thread, udp_thread;

    pthread_create(&tcp_thread, NULL, (void *(*)(void *))tcp_server, (void *)&targs);
    pthread_create(&udp_thread, NULL, (void *(*)(void *))udp_server, (void *)&targs);

    pthread_join(tcp_thread, NULL);
    pthread_join(udp_thread, NULL);

    return 0;
}