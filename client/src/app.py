#!/usr/bin/python3

"""Entry point, scans for ForceESP and connects controller"""

import asyncio

from bleak import BleakScanner
from classes import ForceESP
from classes.helpers import clr

from constants import (
	CONTROL_SERVICE_UUID,
	FORCE_SERVICE_UUID,
	BLE_SCAN_TIMEOUT,
)

async def main():
	found = {
		"event": asyncio.Event(),
		"device": None
	}

	async def callback(device, _advertisement):
		if not found["event"].is_set():
			found["device"] = device
			found["event"].set()

	print(clr.blue('Searching BLE...'))
	async with BleakScanner(callback, [CONTROL_SERVICE_UUID, FORCE_SERVICE_UUID]) as scanner:
		await asyncio.wait(
			[
				found["event"].wait(),
				asyncio.sleep(BLE_SCAN_TIMEOUT)
			],
			return_when=asyncio.FIRST_COMPLETED
		)
		if found["event"].is_set():
			print ('ForceESP found at', found["device"])
			await scanner.stop()
			forceESP = ForceESP(found["device"])
			await forceESP.start()
		else:
			print(clr.red('No ForceESP found'))

asyncio.run(main())
