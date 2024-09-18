import serial
import time

# Define the message structure constants
SOT = 0x0D  # Start of Transmission
EOT = 0x0A  # End of Transmission
ACK = 0x03  # Ack command
X_ON = 0x11
X_OFF = 0x13
ECC = 0x40
SOE = 0x5E

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
    for byte in [message.header.destination, message.header.source, message.command.command] + message.data.data:
        if byte in [EOT, SOT, X_ON, X_OFF, ECC, SOE]:
            encoded_message.append(SOE)
            encoded_message.append(byte + 64)
        else:
            encoded_message.append(byte)
    crc = checksum([message.header.destination, message.header.source, message.command.command] + message.data.data)
    crc_msb = (crc >> 8) & 0xFF
    crc_lsb = crc & 0xFF
    for byte in [crc_msb, crc_lsb]:
        if byte in [EOT, SOT, X_ON, X_OFF, ECC, SOE]:
            encoded_message.append(SOE)
            encoded_message.append(byte + 64)
        else:
            encoded_message.append(byte)
    encoded_message.append(EOT)
    return encoded_message

def decode_message(encoded_message):
    decoded_message = bytearray()
    i = 1
    while i < len(encoded_message) - 1:
        if encoded_message[i] == SOE:
            decoded_message.append(encoded_message[i + 1] - 64)
            i += 2
        else:
            decoded_message.append(encoded_message[i])
            i += 1
    return Message(
        Header(decoded_message[0], decoded_message[1]),
        Command(decoded_message[2]),
        Data(decoded_message[3:-2]),
        CRC16((decoded_message[-2] << 8) | decoded_message[-1])
    )

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
        return receive_message(ser)
    except serial.SerialException as e:
        print(f"Error sending message: {e}")

# Receive a message over the serial port
def receive_message(ser):
    try:
        encoded_message = ser.readline()
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
    

def get_ack(ser):
    data = [0x01, 0x02, 0x00]
    crc = checksum(data)
    message = Message(Header(0x01, 0x02), Command(0x00), Data([]), CRC16(crc))
    response = send_message(ser, message)
    print("response", response)
    if response and response.command.command == 0x06:  # ACK
        print("Received ACK from device")
        return True
    else:
        print("No ACK received from device")
        return False

# Main program
def main():
    # Replace with your serial port name and baudrate
    port = "COM14"
    baudrate = 115200

    # Open the serial port
    ser = open_serial_port(port, baudrate)
    if ser is None:
        return
    
    ack_received = get_ack(ser)
    if not ack_received:
        print("Error communicating with device")

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
    if response is None:
        print("No response received from device")
    else:
        print(f"Received message: {response.header.destination}, {response.header.source}, {response.command.command}, {response.data.data}, {response.crc.msb}, {response.crc.lsb}")

    # Close the serial port
    ser.close()

if __name__ == "__main__":
    main()