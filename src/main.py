"Simple GPS parser for the Raspberry Pi conected via uart to a GPS module."
"Input: NMEA sentences from the GPS module overt hardware uart."
"Output: GPS data in a readable format."

import os
import time
if os.name == 'nt':
    print("Running on Windows - using virtual com port:\n")
    import serial
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))
    COM = input("\n Using COM port: ")
    port = serial.Serial("COM"+COM, baudrate=9600, timeout=2.0)
if os.name == 'posix':
    import serial
    
    #import machine
if os.name == 'esp32':
    port = machine.UART(2, 9600)
    # do initialization stuff for ESP32-S2-Mini

        


# function for parsing data from GPS module
def parseData(receivedData):
    # check if data is available
    if len(receivedData) < 0: 
        print("No data")
        return
    # check if data is not too long
    if len(receivedData) > 82: 
        print("Data too long")
        return
    
    croppedReceivedData = str(receivedData)[2:(len(receivedData))] # shorted string without b' and \r\n
    # check if data starts with $
    if croppedReceivedData[0] != "$":
        print("Data not starting with $")
        return
    
    receivedChecksum = croppedReceivedData.split("*")[1] # get checksum
    data = croppedReceivedData.split("*")[0] # remove checksum from data
    croppedReceivedData = croppedReceivedData[1:] # save data without checksum
    data = data[1:len(data)] # remove $ from data
    data = data.split(",") #split data into a list of shorted string
    data.append(receivedChecksum) # add checksum to the end of the list

    talkerID = data[0][0:2] # get talker ID
    if talkerID == "GP": _stalkerID = "GPS"
    elif talkerID == "GL": _stalkerID = "GLONASS"
    elif talkerID == "GN": _stalkerID = "GNSS"
    elif talkerID == "GA": _stalkerID = "Galileo"
    elif talkerID == ("GB" or "GB"): _stalkerID = "BeiDou"
    elif talkerID == "QZ": _stalkerID = "QZSS"
    elif talkerID == "NA": _stalkerID = "NavIC"
    else: _stalkerID = "Unknown"
    print("Talker ID: %s" % (_stalkerID))

    messageID = data[0][2:5] # get message ID
    print("Message ID: %s" % (messageID))

    # Recommended Minimum Specific GPS/TRANSIT Data
    if messageID == "RMC": 
        print("Time: %s" % (data[1]))
        status = ["active", 
                "No fix avaibile", 
                "invalid"]
        if data[2] == "A": _sstatus = status[0]
        elif data[2] == "V" : _sstatus = status[1]
        else: _sstatus = status[2]
        print("Status: %s" % (_sstatus))
        print("Latitude: %s %s" % (data[3], data[4]))
        print("Longitude: %s %s" % (data[5], data[6]))
        print("Speed in knots: %s " % (data[7]))
        print("Track Angle: %s" % (data[8]))
        print("Date: %s" % (data[9]))
        print("Magnetic Variation: %s" % (data[10]))
        print("Mag Var Direction: %s" % (data[11]))
        print("Checksum: %s" % (data[12]))
    
    # detailed GPS Satellites in View
    elif messageID == "GSV": 
        print("Number of messages: %s" % (data[1]))
        print("Message number: %s" % (data[2]))
        print("Number of satellites in view: %s" % (data[3]))
        for i in range(4, 17, 4):
            if data[i] != "":
                print("Satellite ID: %s Elevation: %s Azimuth: %s SNR: %s" % (data[i], data[i+1], data[i+2], data[i+3]))
        print("Checksum: %s" % (data[20]))

    # Geographic Position - Latitude/Longitude
    elif messageID == "GLL": 
        print("Latitude: %s" % (data[1]))
        print("Longitude: %s" % (data[3]))
        print("Time: %s" % (data[5]))
        GLLstatus = ["active", 
                  "inactive", 
                  "invalid"]
        if data[6] == "A" : _sGLLstatus = GLLstatus[0]
        elif data[6] == "V" : _sGLLstatus = GLLstatus[1]
        else: _sGLLstatus = GLLstatus[2]
        print("Status: %s" % (_sGLLstatus))
        print("Checksum: %s" % (data[7]))

    # GPS Fix Data
    elif messageID == "GGA": 
        print("Time: %s" % (data[1]))
        print("Latitude: %s%s" % (data[2], data[3]))
        print("Longitude: %s%s" % (data[4], data[5]))
        fixDetails = [
            "Invalid, no position available.",
            "Autonomous GPS fix, no correction data used.",
            "DGPS fix, using a local DGPS base station or correction service such as WAAS or EGNOS.",
            "PPS fix, I’ve never seen this used.",
            "RTK fix, high accuracy Real Time Kinematic.",
            "RTK Float, better than DGPS, but not quite RTK.",
            "Estimated fix (dead reckoning).",
            "Manual input mode.",
            "Simulation mode.",
            "WAAS fix"]   
        print("Fix Quality: %s" % (data[6]))
        print("Fix Quality Details: %s" % (fixDetails[int(data[6])]))
        print("Number of Satellites: %s" % (data[7]))
        HDOP = data[8] # Horizontal Dilution of Precision = accuracy of horizontal position
        print("Horizontal Dilution of Precision: %s" % (HDOP))
        if HDOP == "0":
            print("No horizontal dilution of precision available")
        if HDOP >= "6":
            print("Horizontal dilution of precision is terrible")
        print("Altitude ASL: %s %s" % (data[9], data[10]))
        print("Height of Geoid: %s %s" % (data[11], data[12]))
        print("Time since last DGPS update: %s" % (data[13]))
        print("DGPS reference station id: %s" % (data[14]))
        print("Checksum: %s" % (data[15]))

    # GPS Overall Satellite Data
    elif messageID == "GSA": 
        mode = ["Automatic", "Manual", "Invalid"]
        if data[1] == "A": _smode = mode[0]
        elif data[1] == "M": _smode = mode[1]
        else: _smode = mode[2]
        print("Mode: %s" % _smode)
        type = ["No Fix", "2D", "3D"]
        print("Fix Type: %s" % (type[int(data[2])-1]))
        for i in range(12):
            if data[3+i] != "":
                print("Satellite ID: %s" % (data[3+i]))
        print("DOP: %sm" % (data[15]))
        print("HDOP: %sm" % (data[16]))
        print("VDOP: %sm" % (data[17]))
        print("Checksum: %s" % (data[18]))

    # Track Made Good and Ground Speed
    elif messageID == "VTG": 
        print("True Track Made Good: %s" % (data[1]))
        print("True Track indicator: %s" % (data[2]))
        print("Magnetic Track Made Good: %s" % (data[3]))
        print("Magnetic Track indicator: %s" % (data[4]))
        print("Ground Speed (knots): %s" % (data[5]))
        print("Ground Speed (km/h): %s" % (data[7]))
        modeIndicator = ["Autonomous", "Differential", "Estimated", "Manual", "Data not valid"]
        if data[9] == "A":  _smodeIndicator = modeIndicator[0]
        elif data[9] == "D": _smodeIndicator = modeIndicator[1]
        elif data[9] == "E": _smodeIndicator = modeIndicator[2]
        elif data[9] == "M": _smodeIndicator = modeIndicator[3]
        else: _smodeIndicator = modeIndicator[4]
        print("Mode indicator: %s" % (_smodeIndicator))
        print("Checksum: %s" % (data[10]))

    # abort if unknown header
    else:
        print("Unknown message ID")
        return

    # check checksum
    if checkChecksum(croppedReceivedData):
        print("Checksum OK")
    else:
        print("Checksum Invalid or Unavailable")


# function for calculating checksum and comparing it with received one
def checkChecksum(word):
    # Split the message into the message body and the checksum
    message, checksum = word.split('*')

    # Calculate the expected checksum
    expected_checksum = 0
    for char in message:
        expected_checksum ^= ord(char)

    # Compare the expected checksum to the actual checksum
    actual_checksum = int(checksum, 16)
    if expected_checksum == actual_checksum:
        return True
    else:
        return False


sensdingIdx=-1        
while True:
    # send data over bridged uart - simulating GPS module
    if os.name == 'nt':
        sensdingIdx = (sensdingIdx + 1) % 7
        port.write({
            0: b'$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68\r\n',
            1: b'$GPGSV,3,1,11,20,75,131,26,01,40,223,20,11,37,246,22,22,30,067,20*79\r\n',
            2: b'$GPGSV,3,2,11,14,25,306,18,03,25,101,23,06,21,050,20,19,14,333,18*74\r\n',
            3: b'$GPGSV,3,3,11,05,09,199,13,23,09,073,17,18,07,179,,21,05,252,*7E\r\n',
            4: b'$GPGLL,4916.45,N,12311.12,W,225444,A*31\r\n',
            5: b'$GPGGA,225446,4916.45,N,12311.12,W,1,04,2.0,100.0,M,-33.9,M,,*56\r\n',
            6: b'$GPGSA,A,3,20,01,11,14,,,,,,,,,2.0,2.0,2.0*39\r\n',
        }[sensdingIdx])

    data = port.readline()
    print("RAW received data %s" % data)
    parseData(data)
    time.sleep(0.2)
