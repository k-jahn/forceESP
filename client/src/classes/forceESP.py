"""Force ESP controller class

handles BLE communication, user input"""

import asyncio
from time import time

from pynput import keyboard

from bleak import BleakClient
from bleak.exc import BleakDBusError

from classes.helpers.colors import Colors
from classes.measurement import Measurement
from classes.helpers.bleCharacteristic import BLECharacteristic

RECONNECT_ATTEMPTS = 5

DEFAULT_MEASUREMENT_INTERVAL = 10
MAX_MEASURMENT_INTERVAL = 600
DEFAULT_MEASUREMENT_LABEL = 'measurement'
DEFAULT_TARA_READINGS = 15

TARA_CHAR_UUID = '00000000-0000-0000-0000-000000001001'
CALIBRATE_CHAR_UUID = '00000000-0000-0000-0000-000000001002'
MEASURE_CHAR_UUID = '00000000-0000-0000-0000-000000001003'
FORCE_CHAR_UUID = '00000000-0000-0000-0000-000000001312'

c = Colors()

CMDS = '[tara [n], measure [s], monitor, calibrate, label [l], exit]'

class ForceESP:
	def __init__(self, device) -> None:
		self.device = device
		self.measureEvent = asyncio.Event()
		self.measureData = {
			"time": time(),
			"force": 0,
		}
		self.measurementLabel = DEFAULT_MEASUREMENT_LABEL
		self.measurementIndex = 1

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

		measurement = Measurement(self, interval, self.measurementLabel, self.measurementIndex)
		await measurement.run()

		measurement.writeToFile().plot()
		print(f'max:{round(measurement.getPeak("force"), 2)}')
		self.measurementIndex +=1

	async def cmdLabel(self, label, *_pars):
		if label is not None and label != self.measurementLabel:
			self.measurementLabel = label
			self.measurementIndex = 1

	async def cmdTara(self, *pars) -> None:
		taraReadings = int(pars[0]) if pars[0] else DEFAULT_TARA_READINGS
		print(c.blue(f'Tara, n={taraReadings}'))
		await self.taraChar.writeValue(taraReadings)

	async def cmdMonitor(self, *_pars) -> None:
		print(c.blue('monitoring, press any key to stop'))

		# start keypress monitoring
		keypressedEvent = asyncio.Event()
		def onPress(_key):
			keypressedEvent.set()
		await self.startESPMeasure()
		with keyboard.Listener(on_press=onPress) as listener:
			# write values
			while not keypressedEvent.is_set():
				await self.measureEvent.wait()
				val = round(self.measureData["force"], 2)
				output = c.bold(f'{val} kg * ge             '.format())
				print(output, end='\r')
			listener.stop()
			print('\n')
		await self.stopESPMeasure()
		print('stopped')

	# TODO - non-functional
	async def cmdCalibrate(self, *_pars) -> None:
		print(c.blue('calibrating'))
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
				print(c.blue('Connecting to ESP...'))
				async with BleakClient(self.device) as client:
					# reset attempts
					attempts = 0

					self.taraChar = BLECharacteristic(client, TARA_CHAR_UUID, int)
					self.calibrateChar = BLECharacteristic(client, CALIBRATE_CHAR_UUID, float)
					self.measureChar = BLECharacteristic(client, MEASURE_CHAR_UUID, bool)
					self.forceChar = BLECharacteristic(client, FORCE_CHAR_UUID, float)
					print(f"Connected to ESP, enter command {c.bold(CMDS)}")

					def forceCallback(force):
						self.measureData["force"] = force
						self.measureData["time"] = time()
						self.measureEvent.set()
						self.measureEvent.clear()
					await self.forceChar.startNotify(forceCallback)

					# user input loop
					while not exitRequested:
						prompt = ''.join([
							c.bold(self.measurementLabel + '@['),
							c.yellow(client.address),
							c.bold(']$ '),
						])
						inp = input(prompt).split(' ')
						inp.extend([None for _ in range(2)])
						[command, *parameters] = inp[0:3]

						# eval input
						if command == 'exit' or command == 'x':
							exitRequested = True
						elif command == 'tara' or command == 't':
							await self.cmdTara(*parameters)
						elif command == 'measure' or command == 'm':
							await self.cmdMeasure(*parameters)
						elif command == 'monitor':
							await self.cmdMonitor(*parameters)
						elif command == 'calibrate' or command == 'c':
							await self.cmdCalibrate(*parameters)
						elif command == 'label' or command == 'l':
							await self.cmdLabel(*parameters)
						else:
							print(c.red('enter valid command ') + CMDS)

					print(c.blue('Disconnecting...'))
					await self.forceChar.stopNotify()

			# Handle Comm Exceptions
			except BleakDBusError as _exception:
				attempts += 1
				print(c.red("Connection failed ") + f'[{attempts}/{RECONNECT_ATTEMPTS}]')
