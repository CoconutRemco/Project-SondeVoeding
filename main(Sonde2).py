import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, PWM, ADC
import json

# Network configuration
WIFI_SSID = 'AP_Saturnus'
WIFI_PASSWORD = 'OperationGraduation'

broker_address = "asvz.local"
port = 1883
user = "sonde1"
password = "sonde1"
client_id = "pi_pico_1"

# Pin configuration for LED and servo
LED_PIN = 2
SERVO_PIN = 3
led = Pin(LED_PIN, Pin.OUT)
servo_pin = Pin(SERVO_PIN)

# Create PWM object for servo
servo_pwm = PWM(servo_pin)
servo_pwm.freq(50)

# Initialize ADC (Analog to Digital Converter) for microphone
MIC_PIN = 26
adc = ADC(Pin(MIC_PIN))

last_sent_time = 0

def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while not wlan.isconnected():
        print('Connecting to network...')
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
        wlan.connect(ssid, password)
        for _ in range(30):
            if wlan.isconnected():
                break
            time.sleep(1)
        else:
            print('Failed to connect to network. Retrying...')
    print('Network config:', wlan.ifconfig())
    led.on()

def set_servo_angle(angle):
    pulse_width = (angle / 180) * 2000 + 500
    servo_pwm.duty_ns(int(pulse_width * 1000))

def publish_device_info():
    device_info = "who is here" + {
        'device_id': client_id,
        'topics': {
            'listening': ['sonde1', 'available_devices'],
            'sending': ['beep_detection', 'available_devices']
        }
    }
    client.publish(b'available_devices', json.dumps(device_info))

def on_message(topic, message):
    print(message.decode("utf-8"))
    if message == b'who_is_here':
        publish_device_info()
    elif message == b'servo':
        set_servo_angle(120)
        time.sleep(1)
        set_servo_angle(85)
        time.sleep(1.2)
        set_servo_angle(120)

connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

client = MQTTClient(client_id, broker_address, port=port, user=user, password=password)
client.set_callback(on_message)

client.connect()
client.subscribe(b'sonde1')
client.subscribe(b'available_devices')

try:
    while True:
        client.check_msg()
        audio_level = adc.read_u16()
        current_time = time.time()

        if audio_level > 3300 and current_time - last_sent_time > 10:
            client.publish(b'beep_detection', b'beep detected1')
            last_sent_time = current_time
            time.sleep(0.3)

except KeyboardInterrupt:
    print("Exiting")
    client.disconnect()
    led.off()

