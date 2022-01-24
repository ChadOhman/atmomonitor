# eCO2/tVOC Monitor v1.02 (2021/12/23)
# Chad Ohman (chad@chadohman.ca)
# Edmonton, AB, Canada
#
# Inspired to help others make healthy choices about indoor ventilation
# to mitigate the airborne spread of COVID-19 affordably
#
# Licenced under Creative Commons
# Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
# https://creativecommons.org/licenses/by-nc-sa/4.0/

import time
import math
import machine
from machine import Pin, SoftI2C, WDT
from ssd1306 import SSD1306_I2C
import ccs811
import bme280

# Init RGB LED
led_rgb_r = Pin(2, Pin.OUT)
led_rgb_g = Pin(3, Pin.OUT)
led_rgb_b = Pin(4, Pin.OUT)

def led_set_rgb(r,g,b):
    led_rgb_r.value(r)
    led_rgb_g.value(g)
    led_rgb_b.value(b)

# Set RGB LED to white during init
led_set_rgb(1,1,1)

# Init I2C
i2c=machine.I2C(0,sda=Pin(16),scl=Pin(17),freq=400000)

# Init SSD1306 (OLED Display)
# using default addr 0x3c
oled = SSD1306_I2C(128, 64, i2c)
oled.text("Initializing...",0,0)
oled.show()
time.sleep(1)

# Init BME280 (Atmospheric Sensor)
bme = bme280.BME280(i2c=i2c, address=0x77)
time.sleep(1)

# Init CCS811 (Air Quality Sensor)
ccs=ccs811.CCS811(i2c=i2c,addr=0x5b)
time.sleep(1)

def secondsToString(s):
    hour = math.floor(s/3600)
    minute = math.floor((s-(hour*3600))/60)
    second = s - (60 * minute) - (3600 * hour)
    return '{:02d}:{:02d}:{:02d}'.format(hour,minute,second)

def secondsToStringNoHour(s):
    hour = math.floor(s/3600)
    minute = math.floor((s-(hour*3600))/60)
    second = s - (60 * minute) - (3600 * hour)
    return '{:02d}:{:02d}'.format(minute,second)

# Store start time to derive uptime
start = time.time()
runtime = (time.time() - start)

# Initialize the Watchdog timer timeout (5 seconds)
wdt = WDT(timeout=5000)

while True:
    # Reset the watchdog timer
    wdt.feed()
    if ccs.data_ready():
        if (runtime < 5):
            if (ccs.eCO2 > 400 and ccs.tVOC > 0):
                # Skip warmup if I2C error
                start = start - 1200
                print("Warmup skip detected.")
        runtime = (time.time() - start)
        # Get BME data
        atmo = bme.read_compensated_data()
        temp = float(atmo[0]/100)
        pressure = float(atmo[1]/25600)
        humidity = float(atmo[2]/1024)
        temp_r = round(temp,2)
        pressure_r = round(pressure,2)
        humidity_r = round(humidity,2)
        print('eCO2: %d ppm, TVOC: %d ppb' % (ccs.eCO2, ccs.tVOC), bme.values)
        print('Uptime: ' + secondsToString(runtime))
        oled.fill(0)
        oled.text('eCO2: %d ppm' % (ccs.eCO2),0,0)
        oled.text('tVOC: %d ppb' % (ccs.tVOC),0,9)
        oled.text(f"Temp: {temp_r} C",0,20)
        oled.text(f"Hum:  {humidity_r} %",0,30)
        oled.text(f"Pres: {pressure_r} kPa",0,40)
        if (runtime >= 1200):
            if (ccs.eCO2 <= 1000):
                # set LED to green
                led_set_rgb(0,1,0)
                print('LED: GREEN')
                oled.text('Uptime: ' + secondsToString(runtime),0,50)
            elif (ccs.eCO2 <= 1400):
                # set LED to yellow
                led_set_rgb(1,1,0)
                print('LED: YELLOW')
                oled.text('Uptime: ' + secondsToString(runtime),0,50)
            else:
                # set LED to red
                led_set_rgb(1,0,0)
                print('LED: RED')
                oled.text('Uptime: ' + secondsToString(runtime),0,50)
        else:
            # set LED to blue (warmup)
            led_set_rgb(0,0,1)
            print('LED: BLUE')
            t_remaining = 1200 - runtime
            oled.text('Warming: ' + secondsToStringNoHour(t_remaining),0,50)
        oled.show()
        # Calibrate CCS811
        ccs.put_envdata(humidity=humidity,temp=temp)
        time.sleep(1)
    else:
        #print('CCS811 not ready')
        time.sleep(1)
        
main()