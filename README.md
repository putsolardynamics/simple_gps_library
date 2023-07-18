# simple_gps_library
Simple GPS NMEA parser for RPI or other linux
 
## curently working under windows
but its easly portable
### usage 
1 connect UART dongle with shorted RX and TX to simulate GPS receiver
2 choose COM port
3 watch how are decoded some dummy messages

### what works?
script is aware of broken messages and checksum is working
### TODO
speed calculations, time and date semicolons, coordinate fix, GUI?