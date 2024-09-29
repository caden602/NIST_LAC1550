import serial
import struct
import commands
import registers

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
def send_message(serial_conn, destination, source, command):
    # Create the message body
    body = bytearray([destination, source, command, 0x00])

    # Calculate the CRC-16/XMODEM checksum
    crc = checksum(body)

    # Append the checksum to the message body
    body += struct.pack('>H', crc)

    # Escape special characters
    # escaped_body = escape(body)

    # # Wrap the message body in SOT and EOT
    # message = SOT + escaped_body + EOT

    # Send the message over the serial connection
    serial_conn.write(body)

# Define a function to receive a message
def receive_message(serial_conn):
    # Read the message from the serial connection
    message = serial_conn.readline()

    # Check if any data was received
    if not message:
        raise ValueError("No data received")

    # Strip SOT and EOT
    message = message.strip(SOT + EOT)

    # Unescape special characters
    unescaped_message = unescape(message)

    # Check the CRC-16/XMODEM checksum
    crc = checksum(unescaped_message[:-2])
    if crc != 0:
        raise ValueError("CRC error")

    # Extract the message body
    body = unescaped_message[:-2]

    # Check if the body has enough elements
    if len(body) < 3:
        raise ValueError("Invalid message body")

    # Extract the destination, source, command, and data
    destination = body[0]
    source = body[1]
    command = body[2]
    data = body[3:]

    return destination, source, command, data

# Define a function to send a NACK command
def send_nack(serial_conn, destination, source, read_write, register, error_code):
    command = 0x00  # NACK command
    data = bytearray([read_write, register, error_code])
    send_message(serial_conn, destination, source, command, data)

# Define a function to read a NACK command
def read_nack(serial_conn):
    try:
        destination, source, command, data = receive_message(serial_conn)
    except ValueError as e:
        print(f"Error reading NACK: {e}")
        return None

    if command != 0x00:
        print("Expected NACK command")
        return None

    if len(data) < 3:
        print("Invalid NACK data")
        return None

    read_write = data[0]
    register = data[1]
    error_code = data[2]
    return read_write, register, error_code

# [ser] [HID] [DID] [command] [address] [msbCRC] [lsbCRC]
# def write_command(ser, HID, DID, command, address):
#     data = bytearray([ser, HID, DID, command, address])
#     CRC = checksum(data)

# Open the serial connection
serial_conn = serial.Serial('COM14', 115200, timeout=1)

hex_string = "0d425e51040f0694c00a"
byte_array = bytearray.fromhex(hex_string)
received = serial_conn.write(byte_array)

# Send a ECHO command
destination = 0x01
source = 0xBB
# address = 0x04
# send_message(serial_conn, destination, source, commands.PROTO_CMD_ECHO)
# received = receive_message(serial_conn)
print("Received: ", received)

# Send a NACK command
# destination = 0x01
# source = 0xBB
# read_write = 0x01  # Read operation
# register = 0x03
# error_code = 0x04
# send_nack(serial_conn, destination, source, read_write, register, error_code)

# # Read a NACK command
# result = read_nack(serial_conn)
# if result:
#     read_write, register, error_code = result
#     print(f"Received NACK: read_write={read_write}, register={register}, error_code={error_code}")
# else:
#     print("Failed to read NACK")

# Close the serial connection
serial_conn.close()