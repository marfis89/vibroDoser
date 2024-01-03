#!/usr/bin/python3
import sys
import time
import paho.mqtt.client as mqtt # mqtt libary 
from hx711 import HX711 # https://github.com/tatobari/hx711py

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print("Failed to connect to MQTT broker, return code %d\n", rc)

    client.subscribe(list_2_subscribe)

def on_message_set_tare_mqtt(client, userdata, msg):
    try:
        decode_string=str(msg.payload.decode("utf-8","ignore")) 
        print("on_message_set_tare_mqtt: ", decode_string)   
        hx711ReferenceUnit = int(decode_string)
        set_tare(hx711ReferenceUnit)

    except Exception as e:
        print(e)
    finally:
        pass    

def set_tare(hx711ReferenceUnit):

    global scaleStatus

    scaleStatus = False

    print("Start tare !...")

    hx.set_reference_unit(hx711ReferenceUnit)

    hx.reset()

    hx.tare()  

    client.publish(mqtt_broker_topic_scaleStatus, True)

    print("Tare done")

    scaleStatus = True
 

def main():    

    # init tare on start
    set_tare(hx711ReferenceUnit)
    
    last_weight = 10


    while True:
        try:

            if scaleStatus:               
                # calc the load
                weight = round(hx.get_weight(3))               

                if weight != last_weight:
                    print("weight: %s [g]" % (weight))

                    client.publish("vibroDoser/scale/load", weight)
                    last_weight = weight

                hx.power_down()
                hx.power_up()

            time.sleep(0.01)

        except Exception as e:
            print("Vibrodoser Exception: ", e)
            break

        except (KeyboardInterrupt, SystemExit):
            print("Vibrodoser KeyboardInterrupt")
            break  

    client.loop_stop()
    print("exit vibroDoser loop!")
    sys.exit(1)
        
if __name__ == "__main__":

    global scaleStatus

    mqtt_broker_topic_tare = "vibroDoser/scale/tare"
    list_2_subscribe = [(mqtt_broker_topic_tare,2)]

    mqtt_broker_topic_scaleStatus = "vibroDoser/scale/status"

    client = mqtt.Client()

    client.on_connect = on_connect
    client.connect("localhost", 1883, 60)

    client.loop_start() 

    client.message_callback_add(mqtt_broker_topic_tare, on_message_set_tare_mqtt)

    # HX711 settings
    # The correct calibration of the weight sensor is crucial. 
    # For this we need a reference object whose weight we know. 
    # Select the average value of the maximum (load cell 1 kilogram = 500g reference object) 
    # The displayed values can be positive or negative. 
    # In my case, values around 1298304 were displayed for 503g. 
    # My reference value is therefore 1298304 ÷ 503 = 2581.

    # using pin 22 and 23
    hx = HX711(22, 23) 
    hx711ReferenceUnit = 1946

    hx.set_reading_format("MSB", "MSB")
    hx.reset()

    # start main loop 
    main()