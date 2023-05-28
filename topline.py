import sys

import numpy as np
import struct
#from queue import Queue
from collections import deque

from datetime import datetime

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
    rxqueue=deque()
    cmdqueue=deque()
    interqueue=deque()
    inter_sync=deque()
    intra_count=0
    inter_count=0
    #is cb the first or the last? 
    frame_sequence=["b8","b9","ba","bb","bc","cb"]
    #think this is position parameters!
    sequence_count=0
    minutes=0
    seconds=0
    hours=0
    day=0
    month=0
    year=0
    current_cmd=None
    states=["rx_data","command","sync","no_sync"]
    bus_state="no_sync"
    commands=0
    #fast_time is 1a++
    
    #fast_sensors is 15++
    
    #slow is the count between resulting in a frame sync
    
    #sync is intermediate like frame sequence that comes after final slow frame

    #by switching to state processing maybe things become easier


    def __init__(self):
        self.sync=False
        self.do_detect_sequence=False
        self.detect_next=2
        self.last_expect=0
        self.buffer=[]
        self.accept_list={
            #unknown
            #'0x02':"Does the controller send?",
            #'0x17':"Whats this", #no idea
            #'0x1c':"?",
            #'0x1e':"rudder angle",
            #asume all 0x4 are releated to gyropilot ? 
            #'0x41':"whats this guy ",
            #'0x42':"and this guy ",
            #'0x4e':"gyropilot ? sends acks 0x100 it seems",
            #otherwise it sends 0x0167 and some other stuff

            #'0x51':"?",
            #maybe some IPC between controllers something happens here on AP on off",
            #'0x4f':"and this? 

            #'0x5b':"?",#this one is going to be tough

            #dept+log
            #'0x15': "speed",
            #'0x16': "?", #depth?
            #"'0x1f': "?", #some kind of counter/timestamp
            #'0x20': "?", #no clue seems to not change
            #'0x31': "?",#temp.. but how
            #'0x34': "?", #some calibration param?
            #'0x3a': "?", #nothing maybe depth?
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
        if bytestring[0] == '01':
            deg=int("0x"+bytestring[1],16)-100
        else:
            deg=int("0x"+bytestring[1],16)
        return deg
    
    def handle_int16(self,bytestring):
        #a bit to lazy
        int_s="0x"+bytestring[0]+bytestring[1]#.split('0x',1))
        return int(int_s,16)

    def handle_float16(self,bytestring):
        #int_s="".join(bytestring[2].split('0x',1)).join(bytestring[1].split('0x',1))
        #print("int_s",int_s)
        #h_hex_byte = bytes.fromhex(int_s)
        
        int_s="0x"+bytestring[0]+bytestring[1]
        int_16=int(int_s,16)
        #a_int16 = struct.unpack('h', h_hex_byte)
        a_np_int16 = np.int16(int_16)
        return a_np_int16.view(np.float16)

    def simple_decoder(self,cmd,bytestring):
        int16=self.handle_int16(bytestring)
        float16=self.handle_float16(bytestring)
        splith=int(str("0x"+bytestring[0]),0)
        splitl=int(str("0x"+bytestring[1]),0)
        angle=self.handle_angle(bytestring)
        #resp=bytestring[0].join(bytestring[1].split('0x',1))
        #"float",float16
        print("req",cmd,"payload",bytestring,"int",int16,"angle",angle,"hi.lo",splith,splitl)


    def process_cmd(self,cmd,bytestring):
        self.cmdqueue.append(cmd)
        if len(self.cmdqueue) > 3:
            self.cmdqueue.popleft()
        #print("cmd ",cmd)
        if cmd == "1b":
            #update time
            self.minutes=int(str("0x"+bytestring[0]),16)
            self.seconds=int(str("0x"+bytestring[1]),16)
        #if cmd == "1d":
            #goes up and down.. maybe it counts something..
            #update year
            #self.year=1970+int(str("0x"+bytestring[1]),16)
            #print("year ",self.year)
        # No idea yet
        #if cmd == "56" or cmd == "57":
        #    self.simple_decoder(cmd,bytestring)
        # if cmd == "1d" or cmd == "1e":
            #self.simple_decoder(cmd,bytestring)
            #self.minutes=int(str("0x"+bytestring[0]),0)
            #self.seconds=int(str("0x"+bytestring[1]),0)
        if cmd == "04":
            self.simple_decoder(cmd,bytestring)

            ##print("time ",self.minutes,":",self.seconds)
        #if cmd == "cb":
        #    print("cb ",bytestring)
        #if cmd == "53":
        #    print("53 ",bytestring)
        #empty rx buffer and set current_cmd to none!
        self.rxqueue=deque()
        self.current_cmd=None
    
    def process_controller(self,controller,code):
        if code[0] == controller:
            print("status from ",controller," ",code[1])

        elif int(code[0],16) > int("f0",16):
            print("cmd  ",controller,code[0],code[1])
            #print("Command from ",controller," upcode ",list(code))
            self.commands=1#int(code[1],16)
            self.bus_state="command"
        #":
        #    print("unknown controller command")
        
        self.rxqueue=deque()

    def process_command(self,cmd,bytestring):
          
        #print("status from ",controller," ",code[1])

        #elif int(code[0],16) > int("f0",16):
            #print("Command from ",controller," count ",int(code[1],16))
        print("code ",cmd,bytestring[0],bytestring[1])
        #print("command ",cmd,bytestring)
        self.commands-=1
        self.rxqueue=deque()
        #return to sync in case command was the first of the controllers to answer
        if self.commands == 0:
            self.bus_state="sync"

    def recieve(self,byte):
        #states=["fast_time","fast_sensors","rx_slow","command","sync","no_sync"]

        self.rxqueue.append(byte.hex())

        if self.bus_state=="no_sync": 
            print("no_sync")
            if len(self.rxqueue) > 3:
                #remove old element from list   
                self.rxqueue.popleft()
            pattern=[ '1a',"ff","ff"] #is this a bad choice.. what are the options?
            if list(self.rxqueue) != pattern: #next byte is previous sender
                return
            cmd=self.rxqueue.popleft()
            self.process_cmd(cmd,self.rxqueue)
            self.intra_count += 1 #first upcode recived
            print("Sync found!",pattern)
            self.bus_state="rx_data"
            return
                
        if self.bus_state=="rx_data":
            #1a -- 1e (5 data points)
            #cmd=self.rxqueue.popleft()
            #self.process_cmd(cmd,list[self.rxqueue])
            #print("rx_data")
            if len(self.rxqueue) == 3:
                cmd=self.rxqueue.popleft()
                self.process_cmd(cmd,self.rxqueue)
                self.intra_count += 1 #first upcode recived
            if self.intra_count > 9:
                self.bus_state="sync"
                self.intra_count=0
            return

        if self.bus_state=="sync":
            if self.inter_count > 1:
                #print("sync complete ", list(self.inter_sync)) #list(self.rxqueue))
                self.inter_count=0
                #self.inter_sync=deque()
                self.bus_state="rx_data"
                return
            #allways two ..
            #maybe reply on both
            #when major sync allways on first..
            device=list(self.rxqueue)[0]
            #print("device ", device)
            if self.inter_count == 0 and device in self.frame_sequence:
                # next 2 bytes is frame sequence content
                # todo lose sync if this pattern is lost ? 
                if len(self.rxqueue) > 2:
                    dt = datetime.now()
                    #print(str(str(dt.second)+"."+str(dt.microsecond/1000)),"Large sync ",list(self.rxqueue))
                    cmd=self.rxqueue.popleft()
                    self.inter_sync.append(cmd)
                    self.process_controller(cmd,self.rxqueue) #cganges list
                    #self.rxqueue.append(cmd)
                    self.inter_count=1
                return
            
            #if we receive something thats > 0f and not fx and not in sequence .. its an error!
            #but doesnt bus support more than 16 slaves ? 
            #check that xx is followed by > xx if inter_count=0

            if int(device,16) > int("f",16) and int(device,16) < int("f0",16):
                print("Error unexpected command!!",int(device,16))
                self.bus_state="no_sync"
                return
            
            #if 0x is followed by 0x (listen in for an extra byte)
            #if xx is followed by fx (listen in for the fx 3 bytes)
            #if xx is followed by yy .. then xx didnt reply ? 
            if len(self.rxqueue) > 1:
                #basically these are the same.. but one! sends a status the other command..
                #maybe process_cmd is not the right tool here!
                command=format(int("f0",16)+int(device,16),"02x")
                control=device
                #print("comand",command,"control",control,self.rxqueue)  
                if control == self.rxqueue[1] or int(self.rxqueue[1],16) >= int("f0",16):
                    #print("command & control",self.rxqueue)
                    if len(self.rxqueue) > 2:
                        self.inter_count += 1
                        cmd=self.rxqueue.popleft()
                        self.inter_sync.append(cmd)
                        self.process_controller(cmd,self.rxqueue)
                else:
                    #no command no upcode.. exit
                    self.inter_count += 1
                    self.rxqueue.popleft()

            #else if upcode=hex(int(elements[0],16)+int("0xF0",16))
            #00 02 
            #03 04 etc.. counter on master+slaves where masters and slaves come with commands
            #print("sync")
            return
        if self.bus_state=="command":
            if len(self.rxqueue) == 3:
                cmd=self.rxqueue.popleft()
                self.process_command(cmd,self.rxqueue)
                #self.intra_count += 1 #first upcode recived
        return

        if not self.sync:
            #print("hex "+byte.hex())
          

            if len(self.rxqueue) > 3:
                #remove old element from list   
                self.rxqueue.popleft()
            #print("received ",str(byte))
            #print("Rxqueue ",list(self.rxqueue))
            pattern=[ '1a',"ff","ff"]
            
            #pattern2=[ '20',"03","91" ]
            #pattern=[ '1a',"ff","ff" ]

            if list(self.rxqu<eue) == pattern: #next byte is previous sender
                print("Sync found!\n")
                self.intra_count=1 #first upcode recived
                cmd=self.rxqueue.popleft()
                self.process_cmd(cmd,list[self.rxqueue])
                self.rxqueue=deque() #emty queue is the next a frame sync ? 
                self.sync=True
            return
        
        #recieve 10 frames 
        if self.intra_count < 10:
            if len(self.rxqueue) == 3:
                cmd=self.rxqueue.popleft()
                self.process_cmd(cmd,self.rxqueue)
                self.rxqueue=deque() #emty queue is the next a frame sync ? 
                self.intra_count += 1 #first upcode recived
        else:
            if not self.current_cmd:
                 self.current_cmd=byte.hex()
            #print("sync" , list(self.rxqueue))
            #process slaves or sync system
            #if len(self.rxqueue) == 0:
            #    id=int.from_bytes(byte,"big")
            #if self.inter_count == 0:
                #if int.from_bytes(byte):
                #if 
            ##i dont think this is safe!!
            if self.current_cmd in self.frame_sequence:
                 
            #if list(self.cmdqueue) == ["73","1f","20"]:
                if len(self.rxqueue) == 3:
                    #dt = datetime.now()
                    
                    #   print(dt.second," : ",dt.microsecond,"Large sync ",list(self.rxqueue))
                    cmd=self.rxqueue.popleft()
                    self.inter_sync.append(cmd)
                    #self.simple_decoder(cmd,list(self.rxqueue))

                    self.process_cmd(cmd,list[self.rxqueue]) #cganges list
                    self.rxqueue=deque() #emty queue is the next a frame sync ? 
                    #self.rxqueue.append(cmd)
                    self.inter_count=1
                    #self.intra_count += 1 #first upcode recived 
                #process int
            else:
                #so is either 00 02 03 04 etc.. can we build this sequence and expect it and loose sync if its off ?

                #ok we stick it in there..
                #how do we check if 04 is acked by 04.. 
                #so asuming ack is not timed.. 
                #we can simply check .. if first equals to second..
                #if we write 04 in here.. then 
                if len(self.rxqueue) > 1:
                    #if self.inter_count=1:
                        #"check if new byte is same as previous"
                    #cmd0=list(self.rxqueue).index(2)
                    #cmd1=list(self.rxqueue).index(3)
                    elements=list(self.rxqueue)
                    #print("Elements ",elements)
                    # concat id with Fx"0xFx" only woirks for 16 units
                    upcode=hex(int(elements[0],16)+int("0xF0",16))
                    if elements[0] == elements[1] or elements[1] == upcode:
                        #print("Small sync ",list(self.rxqueue))

                        if len(self.rxqueue) > 2:
                            if elements[1] == upcode:
                                print("upcode ", upcode," received count= ",int(elements[2],16))
                                return
                            #process response!!
                            cmd=self.rxqueue.popleft()
                            self.process_cmd(cmd,list(self.rxqueue))
                            self.inter_sync.append(cmd)
                            print("Small sync cmd ", cmd, list(self.rxqueue))

                            self.rxqueue=deque() #emty queue is the next a frame sync ? 
                            self.rxqueue.append(cmd)
                            self.inter_count += 1
                        #if same get response from index2
                    else:
                        #print("Small sync ",list(self.rxqueue))
                        cmd=self.rxqueue.popleft()
                        self.inter_sync.append(cmd)
 
                        self.inter_count += 1
            if self.inter_count > 1:
                #print("sync complete ", list(self.inter_sync)) #list(self.rxqueue))
                self.inter_count=0
                self.intra_count=0
                self.inter_sync=deque()
                    #print("")
        return
                            
            #73xxxx 1fxxxx 20xxxx is pattern before these!!
            #if (byte.hex()=="bc") 
            #{
            #     #expect bc string
            #}
            #controller=byte


                #self.sync=True
            #return

             #look for pattern
        #maybe we dont need a sync ? well once we want to register as something we do..
        #if not self.sync:
        #print(byte.hex())
        #1f 08 + 8 chars .. is some kind of sync sequence.. 
        
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