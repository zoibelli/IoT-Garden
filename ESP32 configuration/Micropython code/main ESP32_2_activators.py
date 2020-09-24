# ESP32 - Micropython Code
# activators: relays for ledstrip ans fan
# IMPORTANT! rename this file to main.py and copy it to the ESP32 board

# connects to Wifi
# subscribes to topics
# publises data to topics


from time import sleep

import machine
import ubinascii
from util.mqtt import MQTTClient


myssid='xxxxxxx'  # type your wifi ssid
mypwd ='xxxxxxx'  # type your wifi password


# configure MQTT and pub-sub topics
mqtt_server = '192.168.1.60' # replace with your Raspberry pi IP address
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub_lights = b'GH/lights'  # user send signal for ON/OFF lights
topic_sub_fan = b'GH/fan'  # user send signal for ON/OFF fan

topic_pub_lightsONOF = b'GH/lightsONOF' # update nodered dashboard in all connected devices


time_interval=1 #default time interval 


#### connect to wifi
def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(myssid, mypwd)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


#### control lights Relay 
# react to msg from NODEred dashboard  
def ctrl_lightsRelay():
    global lightsRelay, client
    # ON/OFF ledstrip,
    if lightsRelay.value()==0:
          lightsRelay.value(1) # turn off the lights
          msg="/lamp-bulb-off.png"  # the filename of the image to be displayed on the dashboard
    else:
          lightsRelay.value(0) # turn on the lights
          msg="/lamp-bulb-on.png" # the filename of the image to be displayed on the dashboard
    #publish message to update dashboard image in all clients
    client.publish(topic_pub_lightsONOF, msg)

#### control fan Relay 
# react to msg from NODEred dashboard  
def ctrl_fanRelay():
    global fanRelay, client
    # ON/OFF fan
    if fanRelay.value()==0:
          fanRelay.value(1) # turn off the fan
    else:
          fanRelay.value(0) # turn on the fan

              
#### MQTT functions

def sub_cb(topic, msg):
  if topic==topic_sub_lights:
      ctrl_lightsRelay()
  elif topic==topic_sub_fan:
      ctrl_fanRelay()
      
  

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub_lights)
  client.subscribe(topic_sub_fan)
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  sleep(10)
  machine.reset()


#### end of MQTT functions


#connect to Wifi
do_connect()

#connect and subscribe to MQTT server
try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

#initilaize devices

# relay to control lights pin33 
lightsRelay = machine.Pin(33, machine.Pin.OUT)
ctrl_lightsRelay()

# relay to control fan pin32
fanRelay = machine.Pin(32, machine.Pin.OUT)
ctrl_fanRelay()

# main loop
while True:  
    try:
        #check for msg in sub topics
        client.check_msg()        
        sleep(time_interval)
    except OSError as e:
       restart_and_reconnect()


