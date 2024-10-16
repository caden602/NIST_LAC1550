import serial

# Define constants
SOT = b'\r'  # Start of Transmission
EOT = b'\n'  # End of Transmission
XON = 0x11   # Transmission on
XOFF = 0x13  # Transmission off
SOE = 0x5E   # Start of Escape sequence
CRC16_POLY = 0x1021  # CRC-16/XMODEM polynomial

# Define a function to calculate the CRC-16/XMODEM checksum
def checksum(data):
    crc = 0
    for byte in data:
        crc = crc << 8 | crc >> 8
        crc ^= byte
        crc ^= (crc & 0xff) >> 4
        crc ^= crc << 12
        crc ^= (crc & 0xff) << 5
        crc &= 0xffff
    crc = int(crc)
    return crc

# Define a function to escape special characters
def escape(data):
    escaped_data = bytearray()
    for byte in data:
        if byte in [SOT, EOT, SOE]:
            escaped_data.append(SOE)
            escaped_data.append(byte | 0x40)
        else:
            escaped_data.append(byte)
    return bytes(escaped_data)

# Define a function to unescape special characters
def unescape(data):
    unescaped_data = bytearray()
    escape_seq = False
    for byte in data:
        if byte == SOE:
            escape_seq = True
        elif escape_seq:
            unescaped_data.append(byte & 0x3F)
            escape_seq = False
        else:
            unescaped_data.append(byte)
    return bytes(unescaped_data)

# Define a function to send a message
def send_message(serial_conn, message, address):
    # Create the message body
    hex_string = "4211"+message+"0f06"
    body = bytearray.fromhex(hex_string)
    # body = bytearray(["0d", "42", "5e", "51", message, "0f", "06"])

    # Calculate the CRC-16/XMODEM checksum
    crc = checksum(body)
    crc = format(crc, 'x')
    print("Checksum: ", crc)
    hex_string += crc

    # Escape special characters
    hex_string = "425e51"+message+"0f06"+crc

    # # Wrap the message body in SOT and EOT
    # message = SOT + escaped_body + EOT
    hex_string = "0d"+hex_string+"0a"
    print("HexString: ", hex_string)

    byte_array = bytearray.fromhex(hex_string)
    print("Sent: ", body)

    # Send the message over the serial connection
    return serial_conn.write(byte_array)
    
"""
Message structure:

?? destination source(escaped1) source(escaped2) message address1 address2 ?? ?? ??
[HID][DID][04][ADDRESS bytes][CRC msb][CRC lsb]

"""


################ MAIN ################
serial_conn = serial.Serial('COM14', 115200, timeout=1)

# message = "04"
# address = "0f06"

message = "00"
address = "0f05:05"

send_message(serial_conn, message, address)

response = serial_conn.read(1024).hex()

print("Received: ", response)
