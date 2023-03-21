import sys

import numpy as np
import struct
#Startup sequence!!
#F0 is forbidden ? charater only issued at bus startup..
#All characters in F range are not addresses!
#0000F0 then iterate from 02-EE where any REPLY means device is present.

#TODO write code for "master as well as slaves!"

class ToplineDecoder:
    #dict handlers
    detect_array=[]
    detect_cur=255
    n="ff"
    n2="ff"
    detect_miss=0
    accept_list=()
    def __init__(self):
        self.sync=False
        self.do_detect_sequence=False
        self.detect_next=2
        self.last_expect=0
        self.buffer=[]
        self.accept_list={}
        self.deny_list={
            '0x15':"speed",
            '0x19':"heading",
            '0x3d':"accum heading",
            '0x73':"Trim",
            '0x2b':"Heel",
            '0x3a': "Distance?",
            }
    
    def detect_sequence(self,byte):
        val=int.from_bytes(byte,"big") & 0xff
        #Make sure we keep current..
        if val == self.detect_next:
            self.detect_cur=self.detect_next
            self.detect_next += 1
            self.detect_miss=0
        else:
            #we are expecting 2 misses for every HIT
            self.detect_miss +=1
            if self.detect_miss == 2:
                print("detected ",hex(self.detect_cur))
                self.detect_array.append(hex(self.detect_cur))
            if self.detect_miss > 2:
                print("Detection error")
        if self.detect_next > 238:
            self.do_detect_sequence=False
            print("detected ",self.detect_array," types ",len(self.detect_array))

    def handle_angle(self,bytearray):
        deg=0
        if bytearray[1] == '0x1':
            deg=int(bytearray[2],16)-100
        else:
            deg=int(bytearray[2],16)
        return deg
    def handle_int16(self,bytearray):
        #a bit to lazy
        int_s=bytearray[1].join(bytearray[2].split('0x',1))
        return int(int_s,16)

    def handle_float16(self,bytearray):
        #int_s="".join(bytearray[2].split('0x',1)).join(bytearray[1].split('0x',1))
        #print("int_s",int_s)
        #h_hex_byte = bytes.fromhex(int_s)
        
        int_s=bytearray[2].join(bytearray[1].split('0x',1))
        int_16=int(int_s,16)
        #a_int16 = struct.unpack('h', h_hex_byte)
        a_np_int16 = np.int16(int_16)
        return a_np_int16.view(np.float16)

    def simple_decoder(self,bytearray):
        int16=self.handle_int16(bytearray)
        #float16=self.handle_float16(bytearray)
        splith=int(bytearray[1],16)
        splitl=int(bytearray[2],16)
        angle=self.handle_angle(bytearray)
        resp=bytearray[1].join(bytearray[2].split('0x',1))
        #"float",float16
        print("req",bytearray[0],"resp",resp,"int",int16,"angle",angle,"hi.lo",splith,splitl)

    def handle_message(self,bytearray):
        #decode strings
        #print("handle message",bytearray)
        #['0x15', '0x16', '0x19', '0x1b', '0x1d', '0x1f', 
        # '0x20', '0x2b', '0x2f', 
        # '0x31', '0x34', '0x3a', '0x3d', 
        # '0x41', '0x42', '0x45', 
        # '0x56', '0x57', '0x58', '0x59', '0x5c', '0x5d', '0x5e', '0x5f', 
        # '0x73', '0xcb'] 
        match bytearray[0]:
            #heal
            case '0x2b':
                print("Heel",self.handle_angle(bytearray),"°")
            case '0x73':
                print("Trim",self.handle_angle(bytearray),"°")
            case '0x19':
                print("Head",self.handle_int16(bytearray),"°")
            case '0x15':
                ##very annoying binary representation
                ##have to check that this is right
                speed_low=int((int(bytearray[2],16)*100)/256)
                #speed_low=int((int(bytearray[2],16)*100)/256)

                ## there is a XX 00 sometimes from 0x15 speed sensor.. no idea what it is..
                ##maybe its meant to be detected by the 00 or its the upper nibble above 11
                ## dealing with this is work in progress
                ## check if two highest bits must be cleared first and that this is some kind of code.
                if int(bytearray[1],16) > 47:
                    print("unknown from speed sensor ",bytearray[1])
                else:
                    print("Speed",int(bytearray[1],16),".",speed_low) #self.handle_float16(bytearray),"knots")
            case '0x16':
                #depth probably is 0000 now try on actual bus when there is depth data!
                if bytearray[1]!='0x0' or bytearray[2] != '0x0':
                    print("handle message",bytearray)
            case '0x1b':
                #0xFF currently
                print("handle message",bytearray)
            case '0x1f':
                #Looks like this one is time in seconds...
                #No idea currently. maybe temp?
                a=bytearray
                self.simple_decoder(bytearray)
            case '0x20':
                #No idea currently
                a=bytearray
                self.simple_decoder(bytearray)
                #print("handle message",bytearray)
            case '0x2f':
                #0xFF currently
                #a=bytearray
                self.simple_decoder(bytearray)
            case '0x31':
                #No idea currently
                a=bytearray
                #self.simple_decoder(bytearray)
            case '0x34':
                #No idea currently
                a=bytearray
                #self.simple_decoder(bytearray)
            case '0x3a':
                #No Think this is the distance logged ... easy to test irl
                a=bytearray[1]
                #create a byteswap function
                #bytearray[1]=bytearray[2]
                #bytearray[2]=a
                #self.simple_decoder(bytearray)
                speed_low=int((int(bytearray[2],16)*100)/256)
                #speed_low=int((int(bytearray[2],16)*100)/256)

                ## there is a XX 00 sometimes from 0x15 speed sensor.. no idea what it is..
                ##maybe its meant to be detected by the 00 or its the upper nibble above 11
                ## dealing with this is work in progress
                ## check if two highest bits must be cleared first and that this is some kind of code.
                if int(bytearray[1],16) > 47:
                    print("unknown from speed sensor ",bytearray[1])
                else:
                    print("Distance ?",int(bytearray[1],16),".",speed_low)
                
            case '0x3d':
                #Accumulated heading / dampened
                print("Accum Head",self.handle_int16(bytearray),"°")

            case '0x41':
                #0xFFFF unkown
                self.simple_decoder(bytearray)
            case '0x42':
                #0xFFFF unkown
                self.simple_decoder(bytearray)
            case '0x45':
                #0xthere are some data here we need to figure out but its not in every pass
                self.simple_decoder(bytearray)            
            case _:
                b=bytearray[0]
                

    def process_protocol(self,byte):
        #a=byte
        self.buffer.append(hex(int.from_bytes(byte,"big")))

        if (len(self.buffer) > 3):
            self.buffer.pop(0)
        
        if (len(self.buffer) == 3):
            ##this now only worls if you have the detect sequencee
            request=self.buffer[0]
            if request in self.deny_list:
                self.buffer.clear()
                return
            if request in self.detect_array or request in self.accept_list:
                #skip empty data
                if self.buffer[1] != '0xff' and self.buffer[2] != '0xff':
                    self.handle_message(self.buffer)
                #print("code ",self.buffer)
                self.buffer.clear()
        
        
    def recieve(self,byte):
        #maybe we dont need a sync ? well once we want to register as something we do..
        #if not self.sync:
        #print(byte.hex())
        if self.n2 == "00" and self.n == "00" and byte.hex() == "f0":
            print("Detect sequence started")
            self.do_detect_sequence=True
            self.detect_next=2
            return

        if self.do_detect_sequence:
            self.detect_sequence(byte)
        else:
            self.process_protocol(byte)

        self.n2=self.n
        self.n=byte.hex()



if len(sys.argv) >= 2:
    td=ToplineDecoder()
    with open(sys.argv[1],"rb") as input:
        while(byte := input.read(1)):
            td.recieve(byte)