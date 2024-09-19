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
        header = self.destination.to_bytes(1, byteorder='little') + self.source.to_bytes(1, byteorder='little')
        body = header + self.command.to_bytes(1, byteorder='little') + self.data
        crc = self.calculate_crc16()
        message = body + crc
        escaped_message = self.escape_special_characters(message)
        return b'\r' + escaped_message + b'\n'

# Define the serial connection
ser = serial.Serial('COM14', 115200, timeout=1)

# Define the message
destination = 0xFF  # Broadcast address
source = 0x01
command = 0x01
data = b'\x01\x02\x03\x04'  # Example data

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

# Print the response
print("Response:", stripped_response)