import subprocess
import sys

def execute_command(command):
    print(f"Executing: {command}")
    try:
        subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Success: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Failed: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)  # Exit the program with error code 1

commands = [
    "sudo ip link set wlan0 down",
    "sudo ip link set wwan0 down",
    "echo 'Y' | sudo tee /sys/class/net/wwan0/qmi/raw_ip",
    "sudo ip link set wwan0 up",
    "sudo qmicli -p -d /dev/cdc-wdm0 --device-open-net='net-raw-ip|net-no-qos-header' --wds-start-network=\"apn='internet.lguplus.co.kr',ip-type=4\" --client-no-release-cid",
    "sudo udhcpc -i wwan0"
]

for command in commands:
    execute_command(command)

print("All commands have been executed.")