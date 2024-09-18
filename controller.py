import serial
import time

# Define the message structure constants
SOT = 0x01  # Start of Transmission
EOT = 0x04  # End of Transmission
ACK = 0x03  # Ack command

# Define the HEADER structure
class Header:
    def __init__(self, destination, source):
        self.destination = destination  # byte
        self.source = source  # byte

# Define the COMMAND structure
class Command:
    def __init__(self, command):
        self.command = command  # byte

# Define the DATA structure
class Data:
    def __init__(self, data):
        self.data = data  # byte or byte array

# Define the CRC16 structure
class CRC16:
    def __init__(self, crc):
        self.msb = (crc >> 8) & 0xFF  # byte
        self.lsb = crc & 0xFF  # byte

# Define the MESSAGE structure
class Message:
    def __init__(self, header, command, data, crc):
        self.header = header  # Header
        self.command = command  # Command
        self.data = data  # Data
        self.crc = crc  # CRC16

# Function to calculate CRC-16/XMODEM checksum
def checksum(v):
    """ Calculate CRC-16/XMODEM checksum.
    Appending the checksum to the data MSB first and calculating the checksum again
    will result to 0.
    :param list[int] v: Data
    :return: 16-bit checksum (CRC-16/XMODEM)
    :rtype: int
    """
    crc = 0
    for i in v:
        crc = crc << 8 | crc >> 8
        crc ^= i
        crc ^= (crc & 0xff) >> 4
        crc ^= crc << 12
        crc ^= (crc & 0xff) << 5
        crc &= 0xffff  # make sure to only keep the lower 16 bits
        crc = int(crc)
    return crc

# Function to create a message
def create_message(destination, source, command, data):
    header = Header(destination, source)
    command = Command(command)
    data = Data(data)
    crc_data = [header.destination, header.source, command.command] + data.data
    crc = checksum(crc_data)
    return Message(header, command, data, CRC16(crc))

# Function to encode a message into bytes
def encode_message(message):
    encoded_message = bytearray()
    encoded_message.append(SOT)
    encoded_message.append(message.header.destination)
    if message.header.source == 0x11:
        encoded_message.append(0x5e)
        encoded_message.append(0x51)
    else:
        encoded_message.append(message.header.source)
    encoded_message.append(message.command.command)
    encoded_message.extend(message.data.data)
    encoded_message.append(message.crc.msb)
    encoded_message.append(message.crc.lsb)
    encoded_message.append(EOT)
    return encoded_message

# Function to decode a message from bytes
def decode_message(encoded_message):
    if encoded_message[0] != SOT or encoded_message[-1] != EOT:
        return None
    message = Message(
        Header(encoded_message[1], encoded_message[2]),
        Command(encoded_message[3]),
        Data(encoded_message[4:-3]),
        CRC16((encoded_message[-3] << 8) | encoded_message[-2])
    )
    return message

# Open the serial port
def open_serial_port(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=3)
        print(f"Serial port {port} opened successfully.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None

# Send a message over the serial port
def send_message(ser, message):
    try:
        encoded_message = encode_message(message)
        ser.write(encoded_message)
        print(f"Sent: {encoded_message}")
    except serial.SerialException as e:
        print(f"Error sending message: {e}")

# Receive a message over the serial port
def receive_message(ser, timeout=5):
    try:
        start_time = time.time()
        encoded_message = bytearray()
        while True:
            if time.time() - start_time > timeout:
                print("Error: Timeout waiting for response")
                return None
            packet = ser.readline()
            if not packet:
                continue
            encoded_message.extend(packet)
            # Check if the message is complete (e.g., check for EOT byte)
            if encoded_message[-1] == EOT:
                break
        print(f"Received: {encoded_message}")
        # Check if the message is long enough
        if len(encoded_message) < 3:
            print("Error: Received message is too short")
            return None
        # Unescape the source address
        if len(encoded_message) > 3 and encoded_message[2] == 0x5e and encoded_message[3] == 0x51:
            encoded_message = encoded_message[:2] + bytearray([0x11]) + encoded_message[4:]
        return decode_message(encoded_message)
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None

# Main program
def main():
    # Replace with your serial port name and baudrate
    port = "COM14"
    baudrate = 115200

    # Open the serial port
    ser = open_serial_port(port, baudrate)
    if ser is None:
        return

    # Create an Ack message
    destination = 0x42
    source = 0x11
    command = ACK
    data = []
    message = create_message(destination, source, command, data)

    # Send the Ack message
    send_message(ser, message)

    # Receive the response
    response = receive_message(ser)
    if response is not None:
        print(f"Received message: {response.header.destination}, {response.header.source}, {response.command.command}, {response.data.data}, {response.crc.msb}, {response.crc.lsb}")

    # Close the serial port
    ser.close()

if __name__ == "__main__":
    main()