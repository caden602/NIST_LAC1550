import serial

# Define the message structure
class Message:
    def __init__(self, destination, source, command, data):
        self.destination = destination
        self.source = source
        self.command = command
        self.data = data

    def calculate_crc16(self):
        crc = 0
        for byte in self.destination.to_bytes(1, byteorder='little') + \
                   self.source.to_bytes(1, byteorder='little') + \
                   self.command.to_bytes(1, byteorder='little') + self.data:
            crc = crc << 8 | crc >> 8
            crc ^= byte
            crc ^= (crc & 0xff) >> 4
            crc ^= crc << 12
            crc ^= (crc & 0xff) << 5
            crc &= 0xffff
        return crc.to_bytes(2, byteorder='big')

    def escape_special_characters(self, data):
        escaped_data = bytearray()
        for byte in data:
            if byte in [10, 13, 17, 19, 94]:
                escaped_data.append(94)  # SOE
                escaped_data.append(byte + 64)
            else:
                escaped_data.append(byte)
        return bytes(escaped_data)

    def construct_message(self):
        header = self.destination.to_bytes(1, byteorder='little') + self.escape_special_characters(self.source.to_bytes(1, byteorder='little'))
        body = header + self.command.to_bytes(1, byteorder='little') + self.data
        crc = self.calculate_crc16()
        message = body + crc
        return b'\r' + message + b'\n'

# Define the serial connection
ser = serial.Serial('COM14', 115200, timeout=1)

# Define the message
destination = 0x42
source = 0x11
command = 0x04
data = b'\x0f\x06'

message = Message(destination, source, command, data)
constructed_message = message.construct_message()

# Send the message
ser.write(constructed_message)

# Receive the response
response = ser.readline()

# Unescape special characters
unescape_response = bytearray()
escape_sequence = False
for byte in response:
    if byte == 94:  # SOE
        escape_sequence = True
    elif escape_sequence:
        unescape_response.append(byte - 64)
        escape_sequence = False
    else:
        unescape_response.append(byte)

# Strip SOT/EOT
stripped_response = bytes(unescape_response)[1:-1]

# Check CRC16
crc = 0
for byte in stripped_response:
    crc = crc << 8 | crc >> 8
    crc ^= byte
    crc ^= (crc & 0xff) >> 4
    crc ^= crc << 12
    crc ^= (crc & 0xff) << 5
    crc &= 0xffff
if crc == 0:
    print("CRC16 check passed")
else:
    print("CRC16 check failed")

# Parse the response
if stripped_response[0] == 0x5e and stripped_response[1] == 0x51:  # Source
    if stripped_response[2] == 0x42:  # Destination
        if stripped_response[3] == 0x08:  # Command
            if stripped_response[4] == 0x0f:  # Top-level node
                date_day = stripped_response[5]
                date_month = stripped_response[6]
                date_year = stripped_response[7]
                print(f"DATE.day: {date_day}")
                print(f"DATE.month: {date_month}")
                print(f"DATE.year: {date_year}")
            else:
                print("Unknown top-level node")
        else:
            print("Unknown command")
    else:
        print("Unknown destination")
else:
    print("Unknown source")