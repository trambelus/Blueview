#!/usr/bin/env python3

import socket
import struct
import os
import sys
from ctypes import CDLL, get_errno
from ctypes.util import find_library
import requests

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

def pp(data):
	string = ""
	for i,_ in enumerate(data):
		string += "%02x" % struct.unpack("B", data[i:i+1])[0]
	return string

def main():
	# define and establish socket connection
	btlib = find_library("bluetooth")
	ble = CDLL(btlib, use_errno=True)
	device_id = ble.hci_get_route(None)

	sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
	sock.bind((device_id,))

	# create HCI filter to allow advertising events
	hci_filter = struct.pack("<IQH", 0x00000010, 0x4000000000000000, 0)
	sock.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, hci_filter)

	err = lambda: ble.hci_le_set_scan_parameters(sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000)
	if err() < 0:
		# reload the interface and try again
		os.system("ifdown hci0")
		os.system("ifup hci0")
		if err() < 0:
			# if it still didn't work, die
			sys.exit("Could not set hci scan parameters")

	err = ble.hci_le_set_scan_enable(s.fileno(), 1, 1, 1000)

	try:
		while True:
			packet = s.recv(1024)

			ptype, event, plen = struct.unpack("BBB", packet[:3])
			if event == LE_META_EVENT:
				subevent = packet[3]
				data = packet[4:]

				if subevent == EVT_LE_ADVERTISING_REPORT:
					num_reports = data[0]
					for i in range(0, num_reports):
						# parse packet
						mac_addr = ':'.join("{0:02x}".format(x).upper() for x in packet[12:6:-1])
						uuid = pp(data[-22:-6])

						requests.post("http://trambel.us:83/blueview/data", data={"packet":pp(packet), "mac":mac_addr, "uuid":uuid})

	except KeyboardInterrupt:
		sock.close()
		os.system("ifdown hci0")
		os.system("ifup hci0")

if __name__ == '__main__':
	main()