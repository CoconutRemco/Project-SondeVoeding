import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, PWM, ADC
import urandom

# Network configuration
WIFI_SSID = 'BRIE'
WIFI_PASSWORD = 'Welkom01'

TOPIC = b'test2'  # Convert to bytes
Connected = False  # global variable for the state of the connection
broker_address = "test.local"  # Broker address
port = 1883  # Broker port
user = "remco"  # Connection username
password = "remco"  # Connection password
client_id = "pi_pico_2"
# Client ID must be different per device

# Pin configuration for LED and servo
LED_PIN = 2  # Replace with the GPIO pin connected to the LED
SERVO_PIN = 3  # Replace with the GPIO pin connected to the servo
led = Pin(LED_PIN, Pin.OUT)
servo_pin = Pin(SERVO_PIN)

# Create PWM object for servo
servo_pwm = PWM(servo_pin)
servo_pwm.freq(50)  # Set frequency to 50Hz

# Initialize ADC (Analog to Digital Converter) for microphone
MIC_PIN = 26  # GPIO pin connected to the microphone
adc = ADC(Pin(MIC_PIN))

def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)  # create station interface to connect to
    wlan.active(True)  # activate the interface

    while not wlan.isconnected():  # check if the station is connected to an AP
        print('Connecting to network...')
        led.on()  # Turn on LED while connecting
        time.sleep(0.5)  # Blink duration
        led.off()
        time.sleep(0.5)  # Blink duration
        wlan.connect(ssid, password)  # connect to the specified SSID with the provided password
        for _ in range(30):  # try connecting for up to 30 seconds
            if wlan.isconnected():  # check if connection established
                break
            time.sleep(1)
        else:
            print('Failed to connect to network. Retrying...')

    print('Network config:', wlan.ifconfig())
    led.on()  # Turn on LED once connected

def set_servo_angle(angle):
    # Convert angle (0-180 degrees) to pulse width (500-2500 microseconds)
    pulse_width = (angle / 180) * 2000 + 500
    # Set duty cycle based on pulse width
    servo_pwm.duty_ns(int(pulse_width * 1000))

def on_message(topic, message):
    print(message.decode("utf-8"))
    if message == b'servo':
        # Set servo angle to 10 degrees
        set_servo_angle(120)
        time.sleep(1)  # Adjust delay time as needed

        # Return servo to 10 degrees
        set_servo_angle(70)
        
        # Return to 180 degrees
        time.sleep(1)
        
        set_servo_angle(120)

connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

client = MQTTClient(client_id, broker_address, port=port, user=user, password=password)
client.set_callback(on_message)

client.connect()  # connect to broker
client.subscribe(TOPIC)

try:
    while True:
        client.check_msg()  # Check for new messages

        # Read analog value from microphone
        audio_level = adc.read_u16()
    
        # Check if audio level is over 7500
        if audio_level > 7500:
            client.publish(b'beep_detection2', b'beep detected')
            time.sleep(0.3)  # Adjust the sleep time as needed

except KeyboardInterrupt:
    print("exiting")
    client.disconnect()
    led.off()  # Turn off LED before exiting script

