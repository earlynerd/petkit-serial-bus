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

