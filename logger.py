# Log.py: Logging module for CCU-IVI Control Service
# This file contains the Logger class which is used to log messages for the CCU-IVI Control service
# The class contains the following attributes:
# - debug_level: The debug level for the service
# - protocol: The protocol used by the service
# - log_file: The file to which the logs are written

import inspect
import time
from datetime import datetime

DEBUG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}

class Logger:
    def __init__(self, debug_level='INFO', system=None, protocol='UDP', debug_devlop=False, log_console=True, log_file=None):
        self.debug_level = debug_level
        self.system = system
        self.protocol = protocol
        self.log_file = log_file
        self.log_console = log_console
        self.debug_devlop = debug_devlop
        self.message(debug_level, protocol, f"Debug level: {self.debug_level}:{self.debug_devlop}")

    def set_debug_level(self, debug_level):
        self.debug_level = debug_level

    def message(self, debug, operation, data):
        # Get current timestamp (nanoseconds)
        #timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        #timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f".{datetime.now().microsecond:06d}{time.time_ns() % 1000:03d}"
        timestamp = time.time_ns()

        message = f"[{timestamp}:{self.system.upper()}:{operation.upper()}:{self.protocol}]-{data}"

        if DEBUG_LEVELS.get(debug, 1) >= DEBUG_LEVELS.get(self.debug_level, 1):
            if self.debug_devlop is True:
                # file name, function name, line number
                frame = inspect.currentframe()
                caller_frame = frame.f_back
                file_name = caller_frame.f_code.co_filename
                function_name = caller_frame.f_code.co_name
                line_number = caller_frame.f_lineno
                message = f"[{timestamp}] [{file_name}][{function_name}][{line_number}] {debug.upper()} {self.protocol} : {data}"

            if self.log_console is True:
                print(message)

            if self.log_file is not None:
                with open(self.log_file, 'a') as file:
                    file.write(message + '\n')
