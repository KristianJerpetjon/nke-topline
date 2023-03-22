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

ser2 = serial.Serial(
    port="/dev/ttyUSB1",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=60)

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
with open("dump.bin","wb") as file:
    while True:
        c=ser.read()
        if len(c) == 0:
            break
        tp.recieve(c)
        file.write(c)
exit

with open("dump.bin","wb") as file:
    while True:
        c=ser.read()
        if len(c) == 0:
            break
        #write uninverted
        #file.write(c)
        #i=int.from_bytes( c , "big")
        #i= i ^ 0xFF
        #write inverted
        #b = i.to_bytes(1,"big")
        file.write(c)
        #ser2.write(c)
        #if 
                    #print(payload)   
        #if prev2.hex() == "04":
        #print(prev2+ " " + prev1 +" "+ c.hex())
        if prev2 == "19" and prev1 == "01" :
            l= prev1 + (c.hex())
            compass=bytes.fromhex(l)
            compass=int.from_bytes(compass,"big") &  0xFFFF
            print("Heading ",compass)
            #hmm not sure if this is right!!
            #print(" voltage "+str(l)+"."+str(h))
        if prev2 == "73" and (prev1 == "00" or prev1 == "01"):
            trim=int.from_bytes(c,"big")
            if prev1=="01":
                #this results in negative values.. but currect
                trim=trim-100

            print("Trim ",trim,"°<")

        if prev2 == "2b" and (prev1 == "00" or prev1 == "01" ):
            #this works after reset as well
            #which means its probably correct.. 
            heal=int.from_bytes(c,"big")
            if prev1 == "01":
                #this feels wrong..
                heal=heal-100
                print("heal ang ",heal,"°>")
            else:
                print("heal ang ",heal,"°<")
        if prev2 == "5c" and prev1 == "00":
            print("? ",int.from_bytes(c,"big"))
        if prev2 == "5d" and prev1 == "3e":

            print("? ",int.from_bytes(c,"big"))
            s=c.hex()+prev1
            data=bytes.fromhex(s)
            #res=hex_to_float16(s)
            res=np.frombuffer(data, dtype=np.float16, count=1)
            print("float16 ",res)
        if prev2 =="ff" and prev1 == "ff":
            if c.hex() not in commands: 
                d=c.hex()
                #print("upcode ",c.hex())
        
        prev2=prev1
        prev1=c.hex()
        #print(prev2.hex()+prev1.hex()+b.hex())

        #print(b.hex()+" " + b.decode("utf-8",errors="replace"),)
        
