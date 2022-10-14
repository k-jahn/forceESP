"""Force ESP controller class

handles BLE communication, user input"""

import asyncio
import re
from time import time

from pynput import keyboard

from bleak import BleakClient
from bleak.exc import BleakDBusError

from classes import Measurement
from classes.helpers import BLECharacteristic
from classes.helpers import clr

from constants import (
	RECONNECT_ATTEMPTS,
	DEFAULT_MEASUREMENT_INTERVAL,
	MAX_MEASURMENT_INTERVAL,
	DEFAULT_LABEL,
	DEFAULT_SUBJECT,
	DEFAULT_TARA_READINGS,
	TARA_CHAR_UUID,
	CALIBRATE_CHAR_UUID,
	MEASURE_CHAR_UUID,
	FORCE_CHAR_UUID,
)

# TODO This sucks. Command objects?
CMDS = '[tara [n], measure [s], monitor, calibrate, label [l], exit]'

class ForceESP:
	def __init__(self, device) -> None:
		self.device = device
		self.measureEvent = asyncio.Event()
		self.measureData = {
			"time": time(),
			"force": 0,
		}
		self.label = DEFAULT_LABEL
		self.subject = DEFAULT_SUBJECT

		self.taraChar: BLECharacteristic
		self.calibrateChar: BLECharacteristic
		self.forceChar: BLECharacteristic
		self.measureChar: BLECharacteristic

	# command functions ---------------------------------------------------------------------------
	async def cmdMeasure(self, pInterval, *_pars) -> None:
		try:
			interval = float(pInterval)
			assert 0 < interval <= MAX_MEASURMENT_INTERVAL
		except:
			interval = DEFAULT_MEASUREMENT_INTERVAL

		measurement = Measurement(
			self,
			interval,
			self.label,
			self.subject
		)
		await measurement.run()

		measurement.writeToFile().plot()
		print(f'max:{round(measurement.getPeak("force"), 2)}')

	async def cmdLabel(self, label, subject, *_pars):
		if label is not None and label != self.label:
			self.label = label
		if subject is not None:
			self.subject = subject

	async def cmdTara(self, readings, *_pars) -> None:
		taraReadings = int(readings) if readings is not None else DEFAULT_TARA_READINGS
		print(clr.blue(f'Tara, n={taraReadings}'))
		await self.taraChar.writeValue(taraReadings)

	async def cmdMonitor(self, *_pars) -> None:
		print(clr.blue('monitoring, press any key to stop'))

		# start keypress monitoring
		keypressedEvent = asyncio.Event()
		def onPress(_key):
			keypressedEvent.set()
		await self.startESPMeasure()
		with keyboard.Listener(on_press=onPress) as _listener:
			# write values
			while not keypressedEvent.is_set():
				await self.measureEvent.wait()
				val = round(self.measureData["force"], 2)
				output = clr.bold(f'{val} kg * ge             ')
				print(output, end='\r')
			print('\n')
		await self.stopESPMeasure()
		print('stopped')

	# TODO - non-functional
	async def cmdCalibrate(self, *_pars) -> None:
		print(clr.blue('calibrating'))
		await self.calibrateChar.writeValue(9072.6, float)

	# public --------------------------------------------------------------------------------------
	async def startESPMeasure(self):
		await self.measureChar.writeValue(True)

	async def stopESPMeasure(self):
		await self.measureChar.writeValue(False)

	# main loop -----------------------------------------------------------------------------------
	async def start(self) -> None:
		exitRequested = False
		attempts = 0
		while (not exitRequested and attempts < RECONNECT_ATTEMPTS):
			try:
				print(clr.blue('Connecting to ESP...'))
				async with BleakClient(self.device) as client:
					# reset attempts
					attempts = 0

					self.taraChar = BLECharacteristic(client, TARA_CHAR_UUID, int)
					self.calibrateChar = BLECharacteristic(client, CALIBRATE_CHAR_UUID, float)
					self.measureChar = BLECharacteristic(client, MEASURE_CHAR_UUID, bool)
					self.forceChar = BLECharacteristic(client, FORCE_CHAR_UUID, float)
					print(f"Connected to ESP, enter command {clr.bold(CMDS)}")

					def forceCallback(force):
						self.measureData["force"] = force
						self.measureData["time"] = time()
						self.measureEvent.set()
						self.measureEvent.clear()
					await self.forceChar.startNotify(forceCallback)

					# user input loop
					while not exitRequested:
						label = ':'.join([self.label, self.subject])
						prompt = ''.join([
							clr.bold(label + '@['),
							clr.yellow(client.address),
							clr.bold(']$ '),
						])
						inpRaw = input(prompt)
						inp  = re.split(r'\s+', inpRaw)
						# pad empty input arguments
						inp.extend([None for _ in range(3 - len(inp))])
						[command, *parameters] = inp

						# eval input
						if command == 'exit' or command == 'x':
							exitRequested = True
						elif command == 'tara' or command == 't':
							await self.cmdTara(*parameters)
						elif command == 'measure' or command == 'm':
							await self.cmdMeasure(*parameters)
						elif command == 'monitor' or command == 'o':
							await self.cmdMonitor(*parameters)
						elif command == 'calibrate' or command == 'c':
							await self.cmdCalibrate(*parameters)
						elif command == 'label' or command == 'l':
							await self.cmdLabel(*parameters)
						else:
							print(clr.red('enter valid command ') + CMDS)

					print(clr.blue('Disconnecting...'))
					await self.forceChar.stopNotify()

			# Handle Comm Exceptions
			except BleakDBusError as _exception:
				attempts += 1
				print(clr.red("Connection failed ") + f'[{attempts}/{RECONNECT_ATTEMPTS}]')
