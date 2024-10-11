import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, PWM, ADC
import json
import array
import math

# Network configuration
WIFI_SSID = 'AP_Saturnus'
WIFI_PASSWORD = 'OperationGraduation'

broker_address = "asvz.local"
port = 1883
user = "asvz"
password = "asvz"
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

# Beep pattern detection configuration
recording_duration = 1.0  # Duration to record audio in seconds
sample_rate = 8000  # Sample rate for recording
reference_samples = array.array('H', [0] * int(sample_rate * recording_duration))  # Buffer for reference audio
reference_set = False  # Flag to check if reference has been set

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
    device_info = {
        'device_id': client_id, 'device_name': 'sonde1'
    }
    client.publish(b'available_devices', "who is here" + json.dumps(device_info))

def on_message(topic, message):
    global reference_set  # Use the global flag
    print(f"Message received on topic {topic}: {message.decode('utf-8')}")
    
    if message == b'who_is_here':
        publish_device_info()
    elif message == b'servo':
        set_servo_angle(120)
        time.sleep(1)
        set_servo_angle(85)
        time.sleep(1.2)
        set_servo_angle(120)
    elif message == b'record_reference':
        if not reference_set:  # Check if reference is already set
            record_reference_audio()
        else:
            print("Reference already recorded.")

connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

client = MQTTClient(client_id, broker_address, port=port, user=user, password=password)
client.set_callback(on_message)

client.connect()
client.subscribe(b'sonde1')
client.subscribe(b'available_devices')

def record_reference_audio():
    global reference_samples, reference_set
    print("Recording reference audio...")
    for i in range(len(reference_samples)):
        reference_samples[i] = adc.read_u16()  # Record sample
        time.sleep(1 / sample_rate)  # Wait for the next sample
    reference_set = True
    print("Reference recording complete.")
    time.sleep(1)  # Give some time after recording before detection starts

def compare_samples(incoming_samples):
    global reference_samples
    if not reference_set:
        print("Reference sample not set.")
        return False

    # Basic similarity check using RMS (Root Mean Square)
    reference_rms = math.sqrt(sum(x ** 2 for x in reference_samples) / len(reference_samples))
    incoming_rms = math.sqrt(sum(x ** 2 for x in incoming_samples) / len(incoming_samples))
    
    # Set a threshold for similarity (adjust as necessary)
    similarity_threshold = 0.7  # Adjust this threshold based on testing

    # Calculate similarity based on RMS values
    if incoming_rms > reference_rms * similarity_threshold:
        return True
    return False

def detect_beep_pattern(audio_level):
    if audio_level > 7800:  # Beep detected
        print("Beep detected!")
        incoming_samples = array.array('H', [adc.read_u16() for _ in range(int(sample_rate * recording_duration))])
        
        if compare_samples(incoming_samples):
            print("Detected a matching beep pattern!")
            client.publish(b'beep_detection', b'beep detected')
        else:
            print("No recognizable beep pattern detected.")

try:
    while True:
        client.check_msg()
        audio_level = adc.read_u16()
        detect_beep_pattern(audio_level)

except KeyboardInterrupt:
    print("Exiting")
    client.disconnect()
    led.off()
