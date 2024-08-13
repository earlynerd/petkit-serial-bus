# petkit-serial-bus
details of petkit fresh element mini automatic feeder internal serial bus protocol

This automatic feeder device is a bit unusual inside, it has an esp8266 that is responsible for connecting to the internet,
and for all the high level operations, and it has an ARM cortex M0 (Nuvoton ISD91230) that is responsible for all the low level motor driving and sensor interfacing.
Mine was purchased used from the petkit ebay store, and has never worked. Refuses to connect to their app. but does actually connect to my wifi. Why does it need to conenct to their app anyway?
I couldnt return it so i took it apart. 

What I've learned is that the ESP8266 and the ARM M0 use a pretty simple and well implemented protocol to exchange a few bytes of command and status data. I've worked out the protocol and many of the command and response types. 
Packets on the bus have a rigid structure and so are easy to receive and parse properly. They are sent at 115200 baud. The ESP8266 has only one full UART and it is shared with the bootloader.
Here is an example packet:

# Command Packet Structure

![get status command and responses](/pictures/get_status.png)
![command packet](/pictures/get_status_2.png)
 
`AA AA 07 01 01 59 9B`

`AA AA`: this is the packet header, all packets begin with this two byte sequence

`07`: this is the packet total length in bytes, including the header

`01`: this is the packet/command/response type. 01 is a command to the M0 to send a status packet.

`01`: this is the sequence number. each command type has its own count. the M0 doesnt seem to care what you put here, but it does include this number in the response or acknowledgement packets for tracking. 

`59 9B`: CRC-16 CCITT code, with 0xFFFF seed value. calculated over the whole packet including its header.

# Response Packet Structure

![get status acknowledgement](/pictures/status_ack.png)

the expected response to this packet is two more packets in reply.

`AA AA 08 01 01 01 94 13` and `AA AA 12 02  FF 00 00 01 08 EC 02 3F 08 71 02 20 24 C5`

The first is an acknowledgement of the "get status" command received. you can tell which command is being acknowledged by the type and the sequunce number which are copied from the command packet.

The second is the status packet requested. 

`AA AA`: packet header

`12`: length 18 bytes

`02`: packet type 2, status packet

`FF`: sequence number. status packets always 0xFF

`00`: Food level IR sensor status. 0x00 for food low, 0x01 for ok

`00`: Door IR sensor. 0x00 for OK, 0x01 when not quite open or closed. 

`01`: Still determining what this is. I`ve only ever seen it be 1

`08EC`: this is a voltage measurement I think. it is only present when the AC adapter is plugged in. I think this one is raw 12-bit ADC counts.

`023F`: this is a voltage measurement I think. it is only present when the AC adapter is plugged in. I think this is in millivolts

`0871`: this is a voltage measurement I think. It is related to battery or system voltage. I think this one is raw 12-bit ADC counts

`0220`: this is a voltage measurement I think. It is related to battery or system voltage. I think this one is in millivolts

`24C5`: CRC-16 code


# Petkit Bus Command Table and Notes

This is not yet complete, and likely isnt fully correct.

`0x01` get status. no payload

`0x02` status reply frame

`0x03` unknown, but present in capture. probably "set two parameters" command of some sort. captured payload at boot `0x00050005`

`0x04` unknown, but present in capture. probably "set two parameters" command of some sort. captured payload at boot `0x00ff00ff`

`0x05` unknown, but present in capture.  probably "set one parameter" command of some sort. captured payload at boot `0x0005`

`0x06` unknown, but present in capture.  probably "set one parameter" command of some sort. captured payload at boot `0xffff`

`0x07` open feed door. payload is duration_8b, strength_8b

`0x08` probably indicates "door open complete!" seen as response type only, following command 7. example payload: `0x021614002A`

`0x09` close feed door. payload is duration_8b, strength_8b

`0x0A` probably indicates "door close complete!" seen as response type only, following command 9. arrives alongside 0x15. example payloads: `0x020614002E` (door actually closed) `0x0010000010` (door was already closed)

`0x0B` turn dispenser wheel, payload is duration_8b, distance_8b, direction_8b, motorCurrent_8b

`0x0C` probably indicates "dispense complete!" typical payload `0x01010300AC`,`01010300A4`,`0x01010300A2`,`0x010103009E`,`0x01010300A0`,`0x01010300A2`,`01010300A4`,`0x01010300A2`  (captured after sequential short dispense commands)

`0x0D` unknown command. probably sets multiple parameters. this is the longest command type. payload in capture : `0x003c01900f01222201f40f01`

`0x0E` subcommand 1 blink upper led, subcommand 2 blink lower led, subcommand 3 make beeps. payload is subcommand_8b, ontime_ms_16b, offtime_ms_16b, count_16b

`0x0F` put microcontroller to sleep or something. stops responding after this command

`0x10` not sure. maybe wakeup? but it didnt wake up

`0x11` this command requests data of some sort. it will reply with a packet of type 18

`0x12` reply packet for the above request. payload `0x01010101`

`0x13` configure motor params. format tbd. stock firmware payload at boot `0x057e`

`0x14` response packet to command 19. payload `0x0004`

`0x15` always arrives after a door close command, along with 0x0A.typical payloads: `0x0352`, `0x04E1` 

# Boot up Sequence and values
```
ISD91230: packet type: 0, length: 7, seq: 0, crc: 7A8B [Valid!], 
ISD91230: packet type: 2, length: 18, seq: 255, crc: F981 [Valid!],  Data: 0x0001010918024A0D030347
ESP8266: packet type: 1, length: 7, seq: 1, crc: 599B [Valid!], 
ISD91230: packet type: 1, length: 8, seq: 1, crc: 9413 [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 1, crc: 3CD8 [Valid!],  Data: 0x00010108ED023F086D021F
ESP8266: packet type: 19, length: 9, seq: 1, crc: DF3E [Valid!],  Data: 0x057E
ESP8266: packet type: 3, length: 11, seq: 1, crc: 6CFA [Valid!],  Data: 0x00050005
ISD91230: packet type: 19, length: 8, seq: 1, crc: B910 [Valid!],  Data: 0x01
ISD91230: packet type: 20, length: 9, seq: 1, crc: AE3B [Valid!],  Data: 0x0004
ESP8266: packet type: 1, length: 7, seq: 2, crc: 69F8 [Valid!], 
ESP8266: packet type: 5, length: 9, seq: 1, crc: D309 [Valid!],  Data: 0x0005
ISD91230: packet type: 3, length: 8, seq: 1, crc: FA73 [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 2, crc: 3947 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 5, length: 8, seq: 1, crc: 48D3 [Valid!],  Data: 0x01
ISD91230: packet type: 4, length: 8, seq: 1, crc: 7FE3 [Valid!],  Data: 0x01
ESP8266: packet type: 4, length: 11, seq: 1, crc: CE7D [Valid!],  Data: 0x00FF00FF
ISD91230: packet type: 6, length: 8, seq: 1, crc: 1183 [Valid!],  Data: 0x01
ESP8266: packet type: 6, length: 9, seq: 1, crc: 057F [Valid!],  Data: 0xFFFF
ISD91230: packet type: 13, length: 8, seq: 1, crc: E172 [Valid!],  Data: 0x01
ESP8266: packet type: 13, length: 19, seq: 1, crc: 62BA [Valid!],  Data: 0x003C0190F01222201F4F01
ISD91230: packet type: 1, length: 8, seq: 3, crc: F271 [Valid!],  Data: 0x01
ESP8266: packet type: 1, length: 7, seq: 3, crc: 79D9 [Valid!], 
ESP8266: packet type: 1, length: 7, seq: 4, crc: 093E [Valid!], 
ISD91230: packet type: 2, length: 18, seq: 3, crc: 3A32 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 1, length: 8, seq: 4, crc: 6BE6 [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 4, crc: 3279 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 13, length: 8, seq: 2, crc: B421 [Valid!],  Data: 0x01
ESP8266: packet type: 13, length: 19, seq: 2, crc: AD1F [Valid!],  Data: 0x003C0190F01222201F4F01
ESP8266: packet type: 1, length: 7, seq: 5, crc: 191F [Valid!], 
ISD91230: packet type: 1, length: 8, seq: 5, crc: 58D7 [Valid!],  Data: 0x01
ESP8266: packet type: 1, length: 7, seq: 6, crc: 297C [Valid!], 
ISD91230: packet type: 2, length: 18, seq: 5, crc: 896D [Valid!],  Data: 0x00010108EC023F086D021F
ISD91230: packet type: 1, length: 8, seq: 6, crc: 0D84 [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 6, crc: 3493 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 1, length: 8, seq: 7, crc: 3EB5 [Valid!],  Data: 0x01
ESP8266: packet type: 1, length: 7, seq: 7, crc: 395D [Valid!], 
ESP8266: packet type: 1, length: 7, seq: 8, crc: C8B2 [Valid!], 
ISD91230: packet type: 2, length: 18, seq: 7, crc: 37E6 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 1, length: 8, seq: 8, crc: 2E8B [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 8, crc: 2405 [Valid!],  Data: 0x00010108ED023F086D021F
ESP8266: packet type: 1, length: 7, seq: 9, crc: D893 [Valid!], 
ISD91230: packet type: 1, length: 8, seq: 9, crc: 1DBA [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 9, crc: 2770 [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 1, length: 8, seq: 10, crc: 48E9 [Valid!],  Data: 0x01
ESP8266: packet type: 1, length: 7, seq: 10, crc: E8F0 [Valid!], 
ISD91230: packet type: 2, length: 18, seq: 10, crc: 67ED [Valid!],  Data: 0x00010108ED023F0861021C
ISD91230: packet type: 14, length: 8, seq: 1, crc: B822 [Valid!],  Data: 0x01
ESP8266: packet type: 14, length: 14, seq: 1, crc: B1E4 [Valid!],  Data: 0x0103E803E8FFFF
ESP8266: packet type: 14, length: 14, seq: 2, crc: 56D2 [Valid!],  Data: 0x02000003E8FFFF
ISD91230: packet type: 14, length: 8, seq: 2, crc: ED71 [Valid!],  Data: 0x01
ISD91230: packet type: 2, length: 18, seq: 255, crc: 025F [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 14, length: 8, seq: 3, crc: DE40 [Valid!],  Data: 0x01
ESP8266: packet type: 14, length: 14, seq: 3, crc: AC0E [Valid!],  Data: 0x0103E80000FFFF
ISD91230: packet type: 2, length: 18, seq: 255, crc: 025F [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 2, length: 18, seq: 255, crc: 025F [Valid!],  Data: 0x00010108ED023F086D021F
ESP8266: packet type: 14, length: 14, seq: 4, crc: 7FBA [Valid!],  Data: 0x0300C800C80002
ISD91230: packet type: 14, length: 8, seq: 4, crc: 47D7 [Valid!],  Data: 0x01
ISD91230: packet type: 14, length: 8, seq: 5, crc: 74E6 [Valid!],  Data: 0x01
ESP8266: packet type: 14, length: 14, seq: 5, crc: 0C75 [Valid!],  Data: 0x0100640064FFFF
ISD91230: packet type: 2, length: 18, seq: 255, crc: CB35 [Valid!],  Data: 0x00010108EA023F08470216
ISD91230: packet type: 2, length: 18, seq: 255, crc: FBF2 [Valid!],  Data: 0x00010108EE0240086E021F
ISD91230: packet type: 2, length: 18, seq: 255, crc: 025F [Valid!],  Data: 0x00010108ED023F086D021F
ISD91230: packet type: 2, length: 18, seq: 255, crc: EB7D [Valid!],  Data: 0x00010108EF024008710220
```

# Other Data

## Flash Dumps
I've been able to dump the flash on both microcontrollers, uploaded here. Theres tons of strings in the esp8266 binary but none to speak of in the M0 flash. 

## logic analyzer captures
These can be viewed using Saleae's free Logic software. The CSV files are exports from these files.

## Python Scripts
petkitParser.py is able to parse packets out of a logic analyzer CSV file
petkitMaster.py is able to directly send commands and parse responses on the bus. 
Theres a debug header with the pins exposed on the control board, and it works best if the ESP8266 is held in reset while an external device takes control of the bus. 

