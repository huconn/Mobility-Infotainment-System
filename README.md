# Mobility-Infotainment-System

Test code for response time authentication.

# Install virtual environment
python3 -m venv .test-code-env
source .test-code-env/bin/activate
pip3 install -r requirements.txt


# Start GPS Information
python3 MIS_GPSInfo.py

# Start CAN Information
python3 MIS_CANInfo.py