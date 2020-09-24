# ESP32 - Micropython Code
# sensors: BME280, SoilMoisture, water tank level
# IMPORTANT! rename this file to main.py and copy it to the ESP32 board

# connects to Wifi
# publises data to topics


from bme280 import BME280
from time import sleep
from util.octopus import i2c_init, disp7_init


import machine
import ubinascii
from util.mqtt import MQTTClient


myssid='xxxxxxx'  # type your wifi ssid
mypwd ='xxxxxxx'  # type your wifi password


# configure MQTT and pub-sub topics
mqtt_server = '192.168.1.60' # replace with your Raspberry pi IP address
client_id = ubinascii.hexlify(machine.unique_id())

topic_sub_mesSoil1 = b'GH/mesSoil1' # user send signal for messuring soil moisture
topic_sub_mesLevel = b'GH/mesLevel' # user send signal for messuring fluid level

topic_pub_temperature = b'GH/temperature'
topic_pub_pressure = b'GH/pressure'
topic_pub_humidity = b'GH/humidity'
topic_pub_soilMoist = b'GH/soilMoisture1'
topic_pub_fluidLevel = b'GH/fluidLevel'

time_interval=1 #default time interval 


#### bme initialization
def bme280_init():
    i2c = i2c_init(1)
    bme = BME280(i2c=i2c)
    #print(bme.values)
    return bme

### Soil Moisture sensor
# Map R value returned from Sensor to moisture%
def mapMoist(m):
    #values from calibration
    ClearWaterRes=1300.0
    DrySoilRes=4095.0
    interV=DrySoilRes-ClearWaterRes
    if m<ClearWaterRes:
        m=0
    else:
        m=float(m-ClearWaterRes)*100.0
    mapVal=100.0-m/interV
    return round(mapVal,2)

### Fluid Level sensor
# Map R value returned from Sensor to level%
def mapLevel(m):
    #values from calibration
    mapVal=(100.0*m)/4095.0
    #print("m=", m, "  mapped=", mapVal)
    return round(mapVal,2)

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


    
#### MQTT functions

def sub_cb(topic, msg):
  global soilMoist_value, fluidLevel_value  
  #print('msg recieved', (topic, msg))
  if topic==topic_sub_mesSoil1:
      soilMoist_value=mapMoist(soilMoist.read())
  elif topic==topic_sub_mesLevel:
      fluidLevel_value=mapLevel(fluidLevel.read())
      
  

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub_mesSoil1)
  client.subscribe(topic_sub_mesLevel)
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
disp7 = disp7_init()    
bme280 = bme280_init()
#Soil Moisture Sensor to analog Pin39
soilMoist= machine.ADC(machine.Pin(39))
soilMoist.atten(machine.ADC.ATTN_11DB)
soilMoist_value=mapMoist(soilMoist.read())

#Tank water level Sensor to analog Pin34
fluidLevel= machine.ADC(machine.Pin(34))
fluidLevel.atten(machine.ADC.ATTN_11DB)
fluidLevel_value=mapLevel(fluidLevel.read())


# main loop
while True:  
    try:
        #check for msg in sub topics
        client.check_msg()
        sleep(time_interval)

        disp7.show(bme280.values[0])
        print('bme280: ', bme280.values)
             
        print(' Soil Moisture: ', soilMoist_value,'%',
              ' Fluid Level: ', fluidLevel_value,'%')
        
        
        # publish to topoics
        client.publish(topic_pub_temperature, bme280.values[0])      
        client.publish(topic_pub_pressure, bme280.values[1])
        client.publish(topic_pub_humidity, bme280.values[2])
        client.publish(topic_pub_soilMoist, str(soilMoist_value))
        client.publish(topic_pub_fluidLevel, str(fluidLevel_value))
        
        sleep(time_interval)
    except OSError as e:
       restart_and_reconnect()


