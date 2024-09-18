import serial
import time

# Open the serial port
def open_serial_port(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Serial port {port} opened successfully.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None

# Send data to the device
def send_data(ser, data):
    try:
        ser.write(data.encode())
        print(f"Sent: {data}")
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

# Receive data from the device
def receive_data(ser):
    try:
        data = ser.readline().decode()
        print(f"Received: {data}")
        return data
    except serial.SerialException as e:
        print(f"Error receiving data: {e}")
        return None

# Main program
def main():
    # Replace with your serial port name and baudrate
    port = "COM3"
    baudrate = 9600

    # Open the serial port
    ser = open_serial_port(port, baudrate)
    if ser is None:
        return

    # Send and receive data
    while True:
        # Send data to the device
        send_data(ser, "Hello from Python!")

        # Receive data from the device
        data = receive_data(ser)
        if data is not None:
            print(f"Received data: {data}")

        # Wait for 1 second before sending the next data
        time.sleep(1)

    # Close the serial port
    ser.close()

if __name__ == "__main__":
    main()