#!/usr/bin/env python
import serial 
import datetime
import time
import binascii
import numpy as np
from topline import ToplineDecoder

#ms = time.time_ns() // 1_000_000
ser = serial.Serial(
    port="/dev/ttyUSB3",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=60)

#ser2 = serial.Serial(
#    port="/dev/ttyUSB1",
#    baudrate=9600,
#    bytesize=serial.EIGHTBITS,
#    stopbits=serial.STOPBITS_ONE,
#    parity=serial.PARITY_NONE,
#    timeout=60)

prev1='00'
prev2='00'
last_ms=time.time_ns() // 1_000_000

commands={
    "19": "Compass",
    "73": "Trim",
    "2b": "Heal",
    }

def hex_to_float16(a_hex_str):
    a_hex_byte = bytes.fromhex(a_hex_str)
    print("A hex_string ",a_hex_str)
    a_int16 = struct.unpack('>H', h_hex_byte)  # sometimes you need h_hex_byte[::-1] because of big/little endian
    a_np_int16 = np.int16(a_int16)
    return a_np_int16.view(np.float16)

tp=ToplineDecoder()

with open("dump_remote_handler.hex","w") as file:
    while True:
        c=ser.read()
        if len(c) == 0:
            break
        tp.recieve(c)
        file.write(str(c.hex()))
exit

with open("dump.bin","rb") as file:
    while True:
        c=file.read(1)
        if len(c)==0:
                break
        tp.recieve(c)
        #print(prev2.hex()+prev1.hex()+b.hex())

        #print(b.hex()+" " + b.decode("utf-8",errors="replace"),)
        
