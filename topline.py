import sys

import numpy as np
import struct
#Startup sequence!!
#F0 is forbidden ? charater only issued at bus startup..
#All characters in F range are not addresses!
#0000F0 then iterate from 02-EE where any REPLY means device is present.

#TODO write code for "master as well as slaves!"

#only master 
#detected  ['0x1b', '0x2f', '0x41', '0x42', '0x45', '0x56', '0x57', '0x58', '0x59']  types  9

#depth + speed with removed master
#detected  ['0x15', '0x16', '0x1f', '0x20', '0x31', '0x34', '0x3a',]  types  16

#compass 
#detected  ['0x19', '0x1d', '0x2b', '0x3d', '0x73', '0xcb']  types  15

#master +shunt decoded..
#detected  [ '0x5c', '0x5d', '0x5e', '0x5f']  types  13

#master + slave + gyro + rudder
#this one requires some magic!
#detected  ['0x3', '0x17', '0x1c', '0x1e', '0x41', '0x42', '0x45', '0x4e', '0x4f', '0x50', '0x51', '0x52', '0x53', '0x54', '0x55', '0x56', '0x57', '0x58', '0x59', '0x5b']  types  22


class ToplineDecoder:
    #dict handlers
    detect_array=[]
    detect_cur=255
    n="ff"
    n2="ff"
    detect_miss=0
    accept_list=()
    temp_divider=0
    def __init__(self):
        self.sync=False
        self.do_detect_sequence=False
        self.detect_next=2
        self.last_expect=0
        self.buffer=[]
        self.accept_list={
            #unknown
            #'0x17':"Whats this", #no idea
            #'0x1c':"?",
            '0x1e':"rudder angle",
            #'0x5b':"?",
            #dept+log
            #'0x15': "speed",
            #'0x16': "?", depth?
            #'0x1f': "?", #some kind of counter/timestamp
            #'0x20': "?", #no clue seems to not change
            #'0x31': "?",#temp.. but how
            #'0x34': "?", #some calibration param?
            #'0x3a': "?", #nothing maybe depth?

            #'0x15':"speed", # 15 is not speed :(
            #compass
            #'0x19':"heading", 
            #'0x1d':"?", unsure.. spits out 69
            #'0x2b' : "heel", 
            #'0x3d':"accum heading",
            #'0x73':"trim", 
            #'0xcb':"?", #unsure not very frequent maybe some accumulated

            #'0x19':"heading",
            #shunt 
            #'0x5c':"volt", 
            #'0x5d':"ampere",
            #'0x5e':"capacity ah", 
            #'0x5f':"capacity",
            '0x03':"second-controller",
        }
        self.deny_list={
            #'0x15':"speed",
            #'0x19':"heading",
            #'0x3d':"accum heading",
            #'0x73':"Trim",
            #'0x2b':"Heel",
            #'0x3a': "Distance?",
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

    def handle_angle(self,bytestring):
        deg=0
        if bytestring[1] == '0x1':
            deg=int(bytestring[2],16)-100
        else:
            deg=int(bytestring[2],16)
        return deg
    def handle_int16(self,bytestring):
        #a bit to lazy
        int_s=bytestring[1].join(bytestring[2].split('0x',1))
        return int(int_s,16)

    def handle_float16(self,bytestring):
        #int_s="".join(bytestring[2].split('0x',1)).join(bytestring[1].split('0x',1))
        #print("int_s",int_s)
        #h_hex_byte = bytes.fromhex(int_s)
        
        int_s=bytestring[2].join(bytestring[1].split('0x',1))
        int_16=int(int_s,16)
        #a_int16 = struct.unpack('h', h_hex_byte)
        a_np_int16 = np.int16(int_16)
        return a_np_int16.view(np.float16)

    def simple_decoder(self,bytestring):
        int16=self.handle_int16(bytestring)
        #float16=self.handle_float16(bytestring)
        splith=int(bytestring[1],16)
        splitl=int(bytestring[2],16)
        angle=self.handle_angle(bytestring)
        resp=bytestring[1].join(bytestring[2].split('0x',1))
        #"float",float16
        print("req",bytestring[0],"resp",resp,"int",int16,"angle",angle,"hi.lo",splith,splitl)

    def handle_message(self,bytestring):
        #decode strings
        #print("handle message",bytestring)
        #['0x15', '0x16', '0x19', '0x1b', '0x1d', '0x1f', 
        # '0x20', '0x2b', '0x2f', 
        # '0x31', '0x34', '0x3a', '0x3d', 
        # '0x41', '0x42', '0x45', 
        # '0x56', '0x57', '0x58', '0x59', '0x5c', '0x5d', '0x5e', '0x5f', 
        # '0x73', '0xcb'] 

        cmd=bytestring[0]
        if cmd == '0x2b':
                print("Heel",self.handle_angle(bytestring),"°")
        if cmd == '0x73':
                print("Trim",self.handle_angle(bytestring),"°")
        if cmd == '0x19':
                print("Head",self.handle_int16(bytestring),"°")
        if cmd == '0x15':
                ##very annoying binary representation
                ##have to check that this is right
                speed_low=int((int(bytestring[2],16)*100)/256)
                speed_high=int((int(    bytestring[1],16)*100)/256)
                #print(bytestring)
                #speed_low=int((int(bytestring[2],16)*100)/256)
                speed=self.handle_int16(bytestring)
                ## there is a XX 00 sometimes from 0x15 speed sensor.. no idea what it is..
                ##maybe its meant to be detected by the 00 or its the upper nibble above 11
                ## dealing with this is work in progress
                ## check if two highest bits must be cleared first and that this is some kind of code.
                print("speed",speed_high,".",speed_low)
                #if int(bytestring[1],16) > 47:
                #    print("unknown from speed sensor ",bytestring[1])
                #else:
                #    a=bytestring
                    #print("Speed",int(bytestring[1],16),".",speed_low) #self.handle_float16(bytestring),"knots")
        if cmd == '0x16':
                #depth probably is 0000 now try on actual bus when there is depth data!
                if bytestring[1]!='0x0' or bytestring[2] != '0x0':
                    print("handle message",bytestring)
        
        if cmd == '0x1b':
                #0xFF currently
                print("handle message",bytestring)
        if cmd == '0x1f':
                #Looks like this one is time in seconds...
                #No idea currently. maybe temp?
                a=bytestring
                self.simple_decoder(bytestring)
        if cmd == '0x1e':
            val=self.handle_int16(bytestring)
            angle=int(bytestring[2],16)

            #process as 6 bit signed
            if bytestring[1] == '0x4':
                #before=(before & 0x3F) | 0xC0
                angle=(angle&0x3F) | 0xC0 #insert two bits to make signed 8 bit
                res=angle.to_bytes(1,"big",signed=False)
                angle=int.from_bytes(res,"big",signed=True)
                angle
                #angle=int((angle/3.141592))+1#(100/(4*64))))

            ##close enough might need some fixing with rounding off 
            ##the -1 makes no sense but it works ish
            angle=int(angle/3.141592)#(100/(4*64))))
            if angle < 0 :
                angle+=1

            print("rudder angle",angle)
        if cmd == '0x20':
                #No idea currently
                a=bytestring
                self.simple_decoder(bytestring)
                #print("handle message",bytestring)
        if cmd == '0x2f':
                #0xFF currently
                #a=bytestring
                self.simple_decoder(bytestring)
        if cmd == '0x31':
                #No idea currently
                a=bytestring
                #asume 13 bit or 16 bit temp sensor..
                #least significant bit is sign bit
                #high=int(bytestring[1],16)
                #low=int(bytestring[2],16)
                #value=(high<<7&0x7F80)| (low>>1)&0x7F

                #negative=(low&0x1)&0x1
                #celcius=value
                celcius=0
                if self.temp_divider != 0:
                    celcius=self.handle_int16(bytestring)*10/self.temp_divider
                #remove sign bit
                #after=int((int(bytestring[2],16)*100)/256)
                #celcius=((after-32)*5)/9
                #temp=(37°F − 32) × 5/9 = 2.778°C
                #print("after",after)
                print("Temperature",celcius)
                #if negative:
                #    print("Temperature ",celcius)
                #else:
                #    print("Temperature ",celcius)
                #print(bytestring)
                #self.simple_decoder(bytestring)
        if cmd == '0x34':
                #No idea currently
                a=bytestring
                self.temp_divider=self.handle_int16(bytestring)
                #self.simple_decoder(bytestring)
        if cmd == '0x3a':
                #No Think this is the distance logged ... easy to test irl
                a=bytestring[1]
                #create a byteswap function
                #bytestring[1]=bytestring[2]
                #bytestring[2]=a
                #self.simple_decoder(bytestring)
                speed_low=int((int(bytestring[2],16)*100)/256)
                #speed_low=int((int(bytestring[2],16)*100)/256)

                ## there is a XX 00 sometimes from 0x15 speed sensor.. no idea what it is..
                ##maybe its meant to be detected by the 00 or its the upper nibble above 11
                ## dealing with this is work in progress
                ## check if two highest bits must be cleared first and that this is some kind of code.
                if int(bytestring[1],16) > 47:
                    print("unknown from speed sensor ",bytestring[1])
                else:
                    print("Distance ?",int(bytestring[1],16),".",speed_low)
                
        if cmd == '0x3d':
                #Accumulated heading / dampened
                print("Accum Head",self.handle_int16(bytestring),"°")

        if cmd == '0x41':
                #0xFFFF unkown
                self.simple_decoder(bytestring)
        if cmd == '0x42':
                #0xFFFF unkown
                self.simple_decoder(bytestring)
        if cmd == '0x45':
                #0xthere are some data here we need to figure out but its not in every pass
                self.simple_decoder(bytestring)
        if cmd == '0x5c': #"volt"
            #volt is given in dV (deci volt)
            val=self.handle_int16(bytestring)
            val1=int(val/10)
            val2=int(val-(val1*10))
            print("volt "+str(val1)+"."+str(val2))
            #print(bytestring)
            #self.simple_decoder(bytestring)

        if cmd == '0x5d': #amperes
            after_dot=int((int(bytestring[2],16)*100)/256)
            before=int(bytestring[1],16)
            #this makes no sense what if you charge faster than this!!
            #if first number is >0x1F its a 6 bit negative number?
            #how do they deal with bigger amp values?
            if before > 31:
                before=(before & 0x3F) | 0xC0
            res=before.to_bytes(1,"big",signed=False)
            signed=int.from_bytes(res,"big",signed=True)

            print("amp",signed,".",after_dot)

        if cmd == '0x5e': #"capacity",
            #if bytestring[1]=='0x0':
            if bytestring[1]!='0x3':
                print("capacity "+str(self.handle_int16(bytestring))+"Ah")

        if cmd == '0x5f': #"capacity",
            if bytestring[1]=='0x0':
                print("capacity "+str(int(bytestring[2],16))+"%")
            #whats up with 0x0340 and 0x001b the latter causes issues

        self.simple_decoder(bytestring)            
        #    case _:
        #        b=bytestring[0]     

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
        if self.n == "00" and byte.hex() == "f0":
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