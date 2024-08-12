# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 11:33:45 2024
This script can send petkit serial bus commands via a usb to uart serial adapter, and can parse the responses 
@author: mmsyl
"""

import binascii
import serial
import time

serialPort = 'com16'
serialbaud = 115200
ser = serial.Serial()

seq = 0

class Frame():
    def __init__(self):
        self.type = 'none'
        self.length = 0
        self.sequence = 0
        self.data = []
        self.crc = []
        self.validity = False
        self.frameBytes = bytearray()
        self.typename = ""
        
class Count():
    def __init__(self):
        self.counter = int(0)
        
    def __call__(self):
        self.counter += 1
        if self.counter > 255: self.counter = 1
        return self.counter    

counter = Count() 

packetTypes = [
     "Boot",
     "Get Status",
     "Status",
     "unknown3",
     "unknown4",
     "unknown5",
     "unknown6",
     "Open Door",
     "Door Open",
     "Close Door",
     "Door Closed",
     "Dispense",
     "Dispensed",
     "unknownconfig13",
     "Blink/Beep",
     "Sleep Now",
     "unknown16",
     "getunknown17",
     "replyunknown18",
     "configunknown19",
     "responseunknown20",
     "dispenseData21",
     ]

CRC16_XMODEM_TABLE = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
        ]

def crc16(data, crc, table):
    """Calculate CRC16 using the given table.
    `data`      - data for calculating CRC, must be bytes
    `crc`       - initial value
    `table`     - table for caclulating CRC (list of 256 integers)
    Return calculated value of CRC
    """
    for byte in data:
        crc = ((crc<<8)&0xff00) ^ table[((crc>>8)&0xff)^byte]
    return crc & 0xffff

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def parseResponse(frame):
    #print(len(frame))
    #print(binascii.hexlify(frame))
    frame.type = frame.frameBytes[3]
    frame.sequence =frame.frameBytes[4]
    frame.data = []
    for i in range(5, len(frame.frameBytes) - 2):
        frame.data.append(frame.frameBytes[i])
    frame.crc = frame.frameBytes[-2:]
    frame.validity = "[bad]"
    frame.typename = packetTypes[frame.type]
    if(crc16(frame.frameBytes, 0xffff,CRC16_XMODEM_TABLE) == 0): frame.validity = "[valid!]"
    print("rx:", frame.type," pkt type", frame.typename, ", seq:", frame.sequence, ", data:", frame.data, "crc:", binascii.hexlify(frame.crc), frame.validity )
    return frame

def printReply(ser, command, sequence):
    
    header = bytes([170,170])
    ser.timeout = 10
    frame = Frame()
    frame.type = 2
    while(frame.type == 2):
        if(ser.read_until(expected = header)):
            l = ser.read(size = 1)
            packetlength = int.from_bytes(l)
            if(packetlength > 0):
                frame.frameBytes = bytearray(header)
                frame.frameBytes += l
                #print("expecting packet length ", packetlength, ",", packetlength-3, "bytes remaining")
                frame.frameBytes += ser.read(size = packetlength-3)
                if(len(frame.frameBytes) == packetlength):
                    frame = parseResponse(frame)
                    if(sequence == frame.sequence): break
                    if(frame.type == 2 and command == 1): break
                    
                    #
            else:
                print("incomplete rx")
                frame = 0
        else:
            print("timeout")
            return 0
    return frame
    #print(binascii.hexlify(frame))
    

def sendCommand(ser, command, sequence, payload):
    #printReply(ser)
    packet = bytearray()
    packet.append(0xaa)
    packet.append(0xaa)
    length = int(len(payload) + 7)
    packet.append(length)
    packet.append(command)
    packet.append(sequence)
    for b in range(0,len(payload)):
        packet.append(payload[b])
    crc = crc16(packet, 0xffff,CRC16_XMODEM_TABLE)
    packet.append(((crc)>>8) & 0xff)
    packet.append(crc&0xff)
    #print("tx:",binascii.hexlify(packet))
    print("tx:", command, "pkt type", packetTypes[command], ", seq:", sequence, ", data:", binascii.hexlify(packet[5:-2]), "crc:", binascii.hexlify(packet[-2:]))
    ser.write(packet)
    #printReply(ser)
    frame = printReply(ser, command, sequence)
    if(command in [19, 17, 7, 9, 1]): 
        frame = printReply(ser, command, sequence)
        
    print()
    #ser.close()


def openDoor(ser, duration, strength):
    command = 7
    sequence = counter()
    duration = constrain(duration, 0, 255)
    strength = constrain(strength, 0, 255)
    payload = [duration, strength]
    sendCommand(ser, command, sequence, payload)

    
def closeDoor(ser, duration, strength):
    command = 9
    sequence = counter()
    duration = constrain(duration, 0, 255)
    strength = constrain(strength, 0, 255)
    payload = [duration, strength]
    sendCommand(ser, command, sequence, payload)

def beep(ser, ontime, offtime, count):
    command = 14
    sequence = counter()
    subcommand = 3
    ontime = constrain(ontime, 0, 65535)
    offtime = constrain(offtime, 0, 65535)
    count = constrain(count, 0, 65535)
    payload = bytearray()
    payload += bytearray(subcommand.to_bytes(1))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(count.to_bytes(2))
    sendCommand(ser, command, sequence, payload)
    
def blink_upper(ser, ontime, offtime, count):
    command = 14
    sequence = counter()
    subcommand = 1
    ontime = constrain(ontime, 0, 65535)
    offtime = constrain(offtime, 0, 65535)
    count = constrain(count, 0, 65535)
    payload = bytearray()
    payload += bytearray(subcommand.to_bytes(1))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(count.to_bytes(2))
    sendCommand(ser, command,sequence, payload)
    
def blink_lower(ser, ontime, offtime, count):
    command = 14
    sequence = counter()
    subcommand = 2
    ontime = constrain(ontime, 0, 65535)
    offtime = constrain(offtime, 0, 65535)
    count = constrain(count, 0, 65535)
    payload = bytearray()
    payload += bytearray(subcommand.to_bytes(1))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(ontime.to_bytes(2))
    payload += bytearray(count.to_bytes(2))
    sendCommand(ser, command, sequence, payload)
    
def dispense(ser, param1, param2, direction, current):
    command = 11
    sequence = counter()
    payload = bytearray()
    param1 = constrain(param1, 0, 255)
    param2 = constrain(param2, 0, 255)
    direction = constrain(direction, 0,1)
    current = constrain(current, 0, 255)
    payload += bytearray(param1.to_bytes(1))
    payload += bytearray(param2.to_bytes(1))
    payload += bytearray(direction.to_bytes(1))
    payload += bytearray(current.to_bytes(1))
    sendCommand(ser, command, sequence, payload)
    
def get_status(ser):
    command = 1
    sequence = counter()
    payload = []
    sendCommand(ser, command, sequence, payload)


ser = serial.Serial(serialPort, serialbaud)
#openDoor(10, 30)
#time.sleep(1)
#closeDoor(10,30)
#time.sleep(1)
#blink_upper(ser, 100,100,8)
#blink_lower(200,200,8)
#beep(100, 200, 5)
#dispense(1,1,1,100)
sendCommand(ser, 17, counter() , [])
time.sleep(0.3)

sendCommand(ser, 19, counter(), [5, 126])
time.sleep(0.3)
sendCommand(ser, 3, counter(), [0,5,0,5])
time.sleep(0.3)
sendCommand(ser, 5, counter(), [0,5])
time.sleep(0.3)

sendCommand(ser, 4, counter(), [0,255,0,255])
time.sleep(0.3)
sendCommand(ser, 6, counter(), [255,255])
time.sleep(0.3)
sendCommand(ser, 13, counter(), [0,60,1,144,15,1,34,34,1,244,15,1])
time.sleep(0.3)
#openDoor(10, 30)
#time.sleep(1)
sendCommand(ser, 17, counter() , [])
time.sleep(0.3)

#blink_upper(ser, 100,100,2)
#blink_lower(ser, 200,200,3)
#beep(100, 200, 5)
#@dispense(1,1,1,88)
#time.sleep(6)
#closeDoor(10,30)

      # open serial port
openDoor(ser,10, 30)
time.sleep(1)
dispense(ser,3,1,0,16)
time.sleep(1)
closeDoor(ser, 10, 30)
time.sleep(1)

for i in range(0,3):
    get_status(ser)
    

ser.close()
