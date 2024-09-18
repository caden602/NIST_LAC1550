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
    def __init__(self, destination, source, header, command, data, crc):
        self.destination = destination
        self.source = source
        self.header = header
        self.command = command
        self.data = data
        self.crc = crc

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
    encoded_message.append(message.destination)
    encoded_message.append(message.source)
    encoded_message.append(message.header)
    encoded_message.append(message.command)
    encoded_message.extend(message.data)
    encoded_message.extend([message.crc >> 8, message.crc & 0xFF])
    return encoded_message

def decode_message(encoded_message):
    destination = encoded_message[0]
    source = encoded_message[1]
    header = encoded_message[2]
    command = encoded_message[3]
    data = encoded_message[4:-2]
    crc = (encoded_message[-2] << 8) | encoded_message[-1]
    return Message(destination, source, header, command, data, crc)

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
    encoded_message = bytearray()
    while True:
        byte = ser.read(1)
        if not byte:
            break
        encoded_message.extend(byte)
        if len(encoded_message) >= 6 and encoded_message[-1] == EOT:  # Adjust the length and EOT byte as needed
            break
    return decode_message(encoded_message)
    

def get_ack(ser):
    destination = 0x01
    source = 0x02
    header = 0x00
    command = 0x00
    data = bytearray()
    crc = 0x0000  # Replace with actual CRC calculation
    message = Message(destination, source, header, command, data, crc)
    response = send_message(ser, message)
    if response and response.command == 0x06:  # ACK
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