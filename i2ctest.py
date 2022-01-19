import machine
 
sda=machine.Pin(16)
scl=machine.Pin(17)
 
i2c=machine.I2C(0,sda=sda,scl=scl,freq=400000)

devices = i2c.scan()

print('I2C address:')
print(devices)

if devices:
    for d in devices:
        print(hex(d), ' (hex)')