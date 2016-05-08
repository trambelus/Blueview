#!/usr/bin/env python3

"""
Created by Siraj Ali
Last modified on 01 May 2016

Scan for Beacons and other BLE devices

based on:

http://stackoverflow.com/questions/23788176/finding-bluetooth-low-energy-with-python
https://github.com/switchdoclabs/iBeacon-Scanner-/blob/master/blescan.py
"""

import argparse
import os
import struct
import socket
import sys
from ctypes import CDLL, get_errno
from ctypes.util import find_library

# CONSTANTS from C
LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS=0x00
LE_RANDOM_ADDRESS=0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE=7
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_PARAMETERS=0x000B
OCF_LE_SET_SCAN_ENABLE=0x000C
OCF_LE_CREATE_CONN=0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02
EVT_LE_CONN_UPDATE_COMPLETE=0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE=0x04

# Advertisment event types
ADV_IND=0x00
ADV_DIRECT_IND=0x01

# reverse endianness - swap byte order
def changeEndian(word):
    return word[2:] + word[0:2]

# get company name from ID as string
def getCompanyName(ID):
    codes = {
        '004c' : "apple",
        '011b' : "aruba",
        '00e0' : "google",
        '015d' : "estimote",
        'feaa' : "eddystone"
    }
    if codes.get(ID) != None:
        return codes.get(ID)
    else:
        return "Unknown"

# get scheme as string - for eddystone URL packet
def getscheme(b):
    scheme = ""
    if b == 0x00:
        scheme = "http://www."
    elif b == 0x01:
        scheme = "https://www."
    elif b == 0x02:
        scheme = "http://"
    elif b == 0x03:
        scheme = "https://"
    return scheme

# print packet to stdout
def printpacket(data):
    string = ""
    for i,j in enumerate(data):
        string += "%02x" % struct.unpack("B", data[i:i+1])[0]
    return string

# MAIN
def main(argv=sys.argv):

    # command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--iface", metavar='', help="BLE device (hci0)")
    opts = parser.parse_args()

    # check if ran as root
    if os.geteuid() != 0:
        sys.exit("Permission denied.")

    # setup
    btlib = find_library("bluetooth")
    if not btlib:
        sys.exit("Please install bluetooth libraries")
    ble = CDLL(btlib, use_errno=True)

    # HCI device
    device_id = 0
    if not opts.iface:
        device_id = ble.hci_get_route(None)
    else:
        device_id = int(opts.iface[-1])

    # Bluetooth socker
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
    s.bind((device_id,))
    
    if not socket:
        sys.exit("Unable to access HCI device")

    # create HCI filter to allow advertising events
    hci_filter = struct.pack("<IQH", 0x00000010, 0x4000000000000000, 0)
    s.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, hci_filter)
    
    err = ble.hci_le_set_scan_parameters(s.fileno(), 0, 0x10, 0x10, 0, 0, 1000)
    if err < 0:
        sys.exit("Failed to set scan parameters.")

    # 1 = on, 0 = off
    # 0 = filtering disabled, 1 = filter out duplicates
    # 1000 = timeout
    err = ble.hci_le_set_scan_enable(s.fileno(), 1, 1, 1000)
    if err < 0:
        e = get_errno()
        print("{0} {1}".format(errno.errorcode[e], os.strerror(e)))
        sys.exit()

    # SCAN
    try:
        while True:
            # BLE device found - print information
            packet = s.recv(1024)
            print("PACKET: ", printpacket(packet))
            ptype, event, plen = struct.unpack("BBB", packet[:3])
            if event == LE_META_EVENT:
                subevent = packet[3]
                data = packet[4:]
                if subevent == EVT_LE_ADVERTISING_REPORT:
                    num_reports = data[0]
                    for i in range(0, num_reports):

                        # parse packet
                        mac_addr = ':'.join("{0:02x}".format(x).upper() for x in packet[12:6:-1])

                        # not only manufacturer, but could also be type/frame format
                        manufacturer = getCompanyName(changeEndian(printpacket(data[15:17])))
                        if manufacturer == 'apple': #iBeacon

                            uuid = printpacket(data[-22:-6])
                            major = printpacket(data[-6:-4])
                            minor = printpacket(data[-4:-2])
                            rssi = str(data[-1])
        
                            # print packet info.    
                            print("MAC: " + mac_addr)
                            print("  MAN.: " + manufacturer)
                            print("  UUID: " + uuid)
                            print("  MAJOR: 0x" + major)
                            print("  MINOR: 0x" + minor)
                            print("  RSSI: " + rssi)
                        
                        elif manufacturer == 'eddystone': #not an actual manufacturer
                            eddystone_type = printpacket(packet[25:26])
                            
                            # UUID frame
                            if eddystone_type == '00': #0x00
                                pass
                            # URL frame
                            elif eddystone_type == '10': #0x10
                                scheme = getscheme(data[23])
                                url = printpacket(data[24:])
                                url_str = bytes.fromhex(url[0:len(url)-2]).decode('utf-8')
                                print("Website: " + scheme + url_str)
                            # TLM frame
                            elif eddystone_type == '20': #0x20
                                pass
            print('------------------------------------------------------------')

    except KeyboardInterrupt:
        s.close()

# RUN
if __name__ == "__main__":
    main()
