#!/usr/bin/python3

"""Entry point, scans for ForceESP and connects controller"""

import asyncio

from bleak import BleakScanner
from classes import ForceESP
from classes.helpers import Colors

c = Colors()

CONTROL_SERVICE_UUID = '00000000-0000-0000-0000-000000cd1102'
FORCE_SERVICE_UUID = '00000000-0000-0000-0000-0000fce04277'

SERVICE_UUIDS = [CONTROL_SERVICE_UUID, FORCE_SERVICE_UUID]

TIMEOUT = 5

async def main():
	found = {
		"event": asyncio.Event(),
		"device": None
	}

	async def callback(device, _advertisement):
		if not found["event"].is_set():
			found["device"] = device
			found["event"].set()

	print(c.blue('Searching BLE...'))
	async with BleakScanner(callback, SERVICE_UUIDS) as scanner:
		await asyncio.wait(
			[
				found["event"].wait(),
				asyncio.sleep(TIMEOUT)
			],
			return_when=asyncio.FIRST_COMPLETED
		)
		if found["event"].is_set():
			print ('ForceESP found at', found["device"])
			await scanner.stop()
			forceESP = ForceESP(found["device"])
			await forceESP.start()
		else:
			print(c.red('No ForceESP found'))

asyncio.run(main())
