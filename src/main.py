"Simple GPS parser for the Raspberry Pi conected via uart to a GPS module."
"Input: NMEA sentences from the GPS module overt hardware uart."
"Output: GPS data in a readable format."

import os
import sys
import logging
import serial
import serial.tools.list_ports
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG) # enable debug logging avaibile DEBUG, INFO, WARNING, ERROR, CRITICAL
import serial
import glob
import time
UTCoffset=int(-time.timezone/3600) # calculate UTC offset
port = serial.Serial()

# function for setting up the serial port
def setup():
    global port

    if os.name == "nt":
        print("Running on Windows - using virtual com port:\n")
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
        COM = input("\n Using COM port: ")
        try:
            port = serial.Serial("COM" + COM, baudrate=9600, timeout=2.0)
        except:
            logging.error("Could not find a serial port")
            sys.exit(1)

    if os.name == "posix":
        print("Running on Linux - using serial port:\n")

        ports = glob.glob("/dev/tty[A-Za-z]*")
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                print(port)
            except (OSError, serial.SerialException):
                pass
        port = input("\n Using port: ")
        port = serial.Serial(port, baudrate=9600, timeout=2.0)

# function for repairing time format AKA adding ":" to time string and time zone offset
# input: 123456 
# output: 12+XX:34:56 [local time]
# format: [hh:mm:ss] 
def repairTime(time):
    return (str(int(time[:2])+UTCoffset)) + ":" + time[2:4] + ":" + time[4:6]

# function for parsing data from GPS module
def parseData(receivedData):
    receivedData = str(receivedData)
    # check if data is available
    if len(receivedData) < 1:
        logging.debug("No data")
        return 
    # check if data is not too long
    if len(receivedData) > 82:
        logging.error("Data too long")
        return 
    # check if data starts with $ 
    if receivedData[0] != "$":
        logging.error("Invalid data - no $ at the beginning")
        return

    receivedChecksum = receivedData.split("*")[1]  # get checksum
    data = receivedData.split("*")[0]  # remove checksum from data
    data = data.split(",")  # split data into a list of shorted string
    data.append(receivedChecksum)  # add checksum to the end of the list

    # $XXYYY,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ,ZZ*CC
    # $ - header
    # XX - talker ID
    # YYY - message ID
    # ZZ - data
    # CC - checksum

    talkerID = data[0][1:3]  # get talker ID
    if   talkerID == "GP":          _stalkerID = "GPS"
    elif talkerID == "GL":          _stalkerID = "GLONASS"
    elif talkerID == "GN":          _stalkerID = "GNSS"
    elif talkerID == "GA":          _stalkerID = "Galileo"
    elif talkerID == ("GB" or "GB"):_stalkerID = "BeiDou"
    elif talkerID == "QZ":          _stalkerID = "QZSS"
    elif talkerID == "NA":          _stalkerID = "NavIC"
    else:                           _stalkerID = "Unknown"
    logging.info("Talker ID: %s" % (_stalkerID))

    messageID = data[0][3:6]  # get message ID
    logging.info("Message ID: %s" % (messageID))

    # GPRMC - Recommended Minimum Specific GPS/TRANSIT Data
    if messageID == "RMC":
        logging.info("Time: %s" % (repairTime(data[1])))
        status = ["active", "No fix avaibile", "invalid"]
        if   data[2] == "A": _sstatus = status[0]
        elif data[2] == "V": _sstatus = status[1]
        else:                _sstatus = status[2]
        logging.info("Status: %s" % (_sstatus))
        logging.info("Latitude: %s %s" % (data[3], data[4]))
        logging.info("Longitude: %s %s" % (data[5], data[6]))
        logging.info("Speed in knots: %s " % (data[7]))
        logging.info("Track Angle: %s" % (data[8]))
        logging.info("Date: %s" % (data[9]))
        logging.info("Magnetic Variation: %s" % (data[10]))
        logging.info("Mag Var Direction: %s" % (data[11]))
        logging.info("Checksum: %s" % (data[12]))

    # detailed GPS Satellites in View
    elif messageID == "GSV":
        logging.info("Number of messages: %s" % (data[1]))
        logging.info("Message number: %s" % (data[2]))
        logging.info("Number of satellites in view: %s" % (data[3]))
        for i in range(4, 17, 4):
            if data[i] != "":
                logging.info(
                    "Satellite ID: %s Elevation: %s Azimuth: %s SNR: %s"
                    % (data[i], data[i + 1], data[i + 2], data[i + 3])
                )
        logging.info("Checksum: %s" % (data[20]))

    # Geographic Position - Latitude/Longitude
    elif messageID == "GLL":
        logging.info("Latitude: %s" % (data[1]))
        logging.info("Longitude: %s" % (data[3]))
        logging.info("Time: %s" % (data[5]))
        GLLstatus = ["active", "inactive", "invalid"]
        if   data[6] == "A": _sGLLstatus = GLLstatus[0]
        elif data[6] == "V": _sGLLstatus = GLLstatus[1]
        else:                _sGLLstatus = GLLstatus[2]
        logging.info("Status: %s" % (_sGLLstatus))
        logging.info("Checksum: %s" % (data[7]))

    # GPGGA - Global Positioning System Fix Data
    elif messageID == "GGA":
        logging.info("Time: %s" % (data[1]))
        logging.info("Latitude: %s%s" % (data[2], data[3]))
        logging.info("Longitude: %s%s" % (data[4], data[5]))
        fixDetails = [
            "0. Invalid, no position available.",
            "1. Autonomous GPS fix, no correction data used.",
            "2. DGPS fix, using a local DGPS base station or correction service such as WAAS or EGNOS.",
            "3. PPS fix, I’ve never seen this used.",
            "4. RTK fix, high accuracy Real Time Kinematic.",
            "5. RTK Float, better than DGPS, but not quite RTK.",
            "6. Estimated fix (dead reckoning).",
            "7. Manual input mode.",
            "8. Simulation mode.",
            "9. WAAS fix",
        ]
        logging.info("Fix Quality: %s" % (data[6]))
        logging.info("Fix Quality Details: %s" % (fixDetails[int(data[6])]))
        logging.info("Number of Satellites: %s" % (data[7]))
        HDOP = data[8]  # Horizontal Dilution of Precision = accuracy of horizontal position
        logging.info("Horizontal Dilution of Precision: %s" % (HDOP))
        if HDOP == "0": logging.info("No HDOP available")
        if HDOP >= "6": logging.info("HDOP is terrible")
        logging.info("Altitude ASL: %s %s" % (data[9], data[10]))
        logging.info("Height of Geoid: %s %s" % (data[11], data[12]))
        logging.info("Time since last DGPS update: %s" % (data[13]))
        logging.info("DGPS reference station id: %s" % (data[14]))
        logging.info("Checksum: %s" % (data[15]))

    # GPS Overall Satellite Data
    elif messageID == "GSA":
        mode = ["Automatic", "Manual", "Invalid"]
        if   data[1] == "A": _smode = mode[0]
        elif data[1] == "M": _smode = mode[1]
        else:                _smode = mode[2]
        logging.info("Mode: %s" % _smode)
        type = ["No Fix", "2D", "3D"]
        logging.info("Fix Type: %s" % (type[int(data[2]) - 1]))
        for i in range(12):
            if data[3 + i] != "": logging.info("Satellite ID: %s" % (data[3 + i]))
        logging.info("DOP: %sm" % (data[15]))
        logging.info("HDOP: %sm" % (data[16]))
        logging.info("VDOP: %sm" % (data[17]))
        logging.info("Checksum: %s" % (data[18]))

    # Track Made Good and Ground Speed
    elif messageID == "VTG":
        logging.info("True Track Made Good: %s" % (data[1]))
        logging.info("True Track indicator: %s" % (data[2]))
        logging.info("Magnetic Track Made Good: %s" % (data[3]))
        logging.info("Magnetic Track indicator: %s" % (data[4]))
        logging.info("Ground Speed (knots): %s" % (data[5]))
        logging.info("Ground Speed (km/h): %s" % (data[7]))
        modeIndicator = [
            "Autonomous",
            "Differential",
            "Estimated",
            "Manual",
            "Data not valid",
        ]
        if   data[9] == "A": _smodeIndicator = modeIndicator[0]
        elif data[9] == "D": _smodeIndicator = modeIndicator[1]
        elif data[9] == "E": _smodeIndicator = modeIndicator[2]
        elif data[9] == "M": _smodeIndicator = modeIndicator[3]
        else:                _smodeIndicator = modeIndicator[4]
        logging.info("Mode indicator: %s" % (_smodeIndicator))
        logging.info("Checksum: %s" % (data[10]))

    # abort if unknown header
    else:
        logging.error("Unknown message ID")
        return

    # check checksum
    if checkChecksum(receivedData[1:]):  # remove $ from cropped data, because checkChecksum function does not need it
        logging.info("Checksum OK")
    else:
        logging.info("Checksum Invalid or Unavailable")


# function for calculating checksum and comparing it with received one
def checkChecksum(word):
    # Split the message into the message body and the checksum
    message, checksum = word.split("*")

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

def main():
    global port
    sendingIdx = -1
    while True:
        # send data over bridged uart - simulating GPS module
        if os.name == "nt":
            sendingIdx = (sendingIdx + 1) % 7
            port.write(
                {
                    0: b"$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68\r\n",
                    1: b"$GPGSV,3,1,11,20,75,131,26,01,40,223,20,11,37,246,22,22,30,067,20*79\r\n",
                    2: b"$GPGSV,3,2,11,14,25,306,18,03,25,101,23,06,21,050,20,19,14,333,18*74\r\n",
                    3: b"$GPGSV,3,3,11,05,09,199,13,23,09,073,17,18,07,179,,21,05,252,*7E\r\n",
                    4: b"$GPGLL,4916.45,N,12311.12,W,225444,A*31\r\n",
                    5: b"$GPGGA,225446,4916.45,N,12311.12,W,1,04,2.0,100.0,M,-33.9,M,,*56\r\n",
                    6: b"$GPGSA,A,3,20,01,11,14,,,,,,,,,2.0,2.0,2.0*39\r\n",
                }[sendingIdx]
            )

        data = port.readline().decode('utf-8').rstrip()
        logging.debug("RAW received data %s" % data)
        parseData(data)
        time.sleep(0.2)


if __name__ == "__main__":
    print("GPS parser script by Mateusz Czarnecki PUT Solar Dynamics\n")
    logging.debug(time.strftime("%d.%m.%Y %H:%M:%S\n")) # print current time
    setup()
    main()

