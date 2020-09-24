from picamera import PiCamera
from time import sleep
import paho.mqtt.client as mqtt

# Δημιουργεί το κείμενο της λεζάντας που θα προστεθεί στην εικόνα
def timestamp():
    from datetime import datetime
    dateTimeObj= datetime.now()
    timestampstr="EK Evosmou - "+dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S)")
    return timestampstr

#Προεπισκόπηση, λήψη και αποθήκευση της εικόνας
def do_capture():
    global i   
    try:
        msg="/image"+str(i)+".jpg"
        fname='/home/pi/node-red-static'+msg
        camera.start_preview()
        camera.annotate_text_size = 50
        camera.annotate_text=timestamp()
        sleep(5)
        camera.capture(fname)
        camera.stop_preview()
        print (msg)
        client.publish("piCam/ImgRecieved", msg) # στέλνει μνμ ότι έγινε η λήψη της φωτογραφίας
        if i==10:  # Διατηρει αρχείο με τις 10 πιο πρόσφατες εικόνες
            i=1
        else:
            i=i+1
    except:
        camera.close()
    

# ------ MQTT code ------------------
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("piCam/NewImg") # μνμ που στέλνει ο χρήστης για από το node-red dashboard ια να γίνει λήψη

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    do_capture()
    
#----------end og MQTT code ------------

i=1
camera = PiCamera()
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.1.60", 1883, 60)
client.publish("piCam/ImgRecieved", "/image0.jpg") # μνμ για να εμφανίσει στο node-red dashboard την προεπιλεγμένη εικόνα

client.loop_forever()
    


