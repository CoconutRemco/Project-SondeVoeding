import utime
import network
import time
from umqtt.simple import MQTTClient
from machine import Pin

# Network configuration
WIFI_SSID = 'BRIE'
WIFI_PASSWORD = 'Welkom01'

TOPIC_SERVO1 = b'test2'  # Servo topic for beep_detection
TOPIC_SERVO2 = b'test'   # Servo topic for beep_detection2
TOPIC_BEEP1 = b'beep_detection'
TOPIC_BEEP2 = b'beep_detection2'
broker_address = "test.local"  # Broker address
port = 1883  # Broker port
user = "remco"  # Connection username
password = "remco"  # Connection password
client_id = "pi_pico_touch"

# Set up the touch sensor pin
TOUCH_PIN = Pin(5, Pin.IN)

# Set up the buzzer pin
BUZZER_PIN = 1
buzzer = Pin(BUZZER_PIN, Pin.OUT)

# Set up the LED pin
LED_PIN = 3
led = Pin(LED_PIN, Pin.OUT)

# Variables for tracking beep detection and servo message sending
last_beep_time = 0
beep_valid_duration = 10  # Duration in seconds for which a beep detection is valid
servo_sent = False  # Flag to track if servo message has been sent
current_servo_topic = TOPIC_SERVO1  # Default servo topic

# Function to connect to Wi-Fi
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)  # Create station interface
    wlan.active(True)  # Activate the interface
    
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)  # Connect to the specified SSID with the provided password

        # Blink LED while attempting to connect
        retry_count = 0
        while not wlan.isconnected() and retry_count < 30:
            print(f'Attempt {retry_count + 1}: Connecting...')
            led.on()
            time.sleep(0.5)
            led.off()
            time.sleep(0.5)
            retry_count += 1

        if not wlan.isconnected():
            print('Failed to connect to network after 30 attempts.')
            return False

    print('Connected to network')
    print('Network config:', wlan.ifconfig())
    led.on()  # Turn on LED when connected
    return True

# Callback function to handle MQTT messages
def on_message(topic, message):
    global last_beep_time, servo_sent, current_servo_topic
    print("Received message:", message)
    if message == b'beep detected':
        # Activate the buzzer
        buzzer.on()
        utime.sleep(0.5)  # Beep duration
        buzzer.off()
        # Update last beep time
        last_beep_time = utime.time()
        # Reset servo_sent flag
        servo_sent = False
        # Set the appropriate servo topic based on the beep topic
        if topic == TOPIC_BEEP1:
            current_servo_topic = TOPIC_SERVO1
        elif topic == TOPIC_BEEP2:
            current_servo_topic = TOPIC_SERVO2

# Connect to Wi-Fi
if connect_to_wifi(WIFI_SSID, WIFI_PASSWORD):
    try:
        # Create MQTT client instance
        client = MQTTClient(client_id, broker_address, port=port, user=user, password=password)
        client.set_callback(on_message)

        # Connect to MQTT broker
        client.connect()
        client.subscribe(TOPIC_BEEP1)
        client.subscribe(TOPIC_BEEP2)

        # Variables for debounce mechanism
        last_touch_state = -1
        last_touch_time = 0
        debounce_duration = 0.5  # Debounce duration in seconds

        # Main loop
        while True:
            # Check for incoming MQTT messages
            client.check_msg()
            
            # Read touch sensor value
            touch_state = TOUCH_PIN.value()
            
            # Check for change in touch sensor state
            if touch_state != last_touch_state:
                current_time = utime.time()
                if current_time - last_touch_time > debounce_duration:
                    last_touch_state = touch_state
                    last_touch_time = current_time
                    # Check if the touch sensor is activated and beep was detected recently
                    if touch_state == 0 and (current_time - last_beep_time <= beep_valid_duration) and not servo_sent:
                        client.publish(current_servo_topic, b'servo')  # Publish MQTT message to move servo
                        servo_sent = True  # Set flag to indicate servo message has been sent

            utime.sleep(0.1)  # Wait for a short time to avoid unnecessary CPU load

    except Exception as e:
        print("An error occurred:", e)
        # Blink LED quickly to indicate a failure
        while True:
            led.on()
            time.sleep(0.1)
            led.off()
            time.sleep(0.1)
else:
    print("Unable to establish Wi-Fi connection.")
    # Blink LED quickly to indicate a failure
    while True:
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

