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
        if cmd == '0x4e':
            if bytestring[1] == "0x10" and bytestring[2]=='0x0':
                print("GP ACK")
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