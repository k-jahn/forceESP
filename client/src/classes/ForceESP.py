# Force ESP controller class
#
# handles BLE communication, user input

import asyncio
import traceback
import struct
from classes.helpers.Colors import Colors

from time import time
from bleak import BleakClient

from classes.Measurement import Measurement
from classes.helpers.BLECharacteristic import BLECharacteristic

RECONNECT_ATTEMPTS = 5

DEFAULT_MEASUREMENT_INTERVAL = 10
DEFAULT_MEASUREMENT_LABEL = 'measurement'
DEFAULT_TARA_READINGS = 15

TARA_CHAR_UUID = '00000000-0000-0000-0000-000000001001'
CALIBRATE_CHAR_UUID = '00000000-0000-0000-0000-000000001002'
MEASURE_CHAR_UUID = '00000000-0000-0000-0000-000000001003'
FORCE_CHAR_UUID = '00000000-0000-0000-0000-000000001312'

c = Colors()

CMDS = "[tara [n], measure [s], monitor, calibrate, label [l], exit]"

class ForceESP:
	def __init__(self, device) -> None:
		self.device = device
		self.measurementLabel = DEFAULT_MEASUREMENT_LABEL
		self.measurementIndex = 1

	# command functions -----------------------------------------------------------------------------------------------
	async def cmdMeasure(self, pInterval, *pars) -> None:
		try:
			interval = float(pInterval)
		except:
			interval = DEFAULT_MEASUREMENT_INTERVAL

		measurement = Measurement(self, interval, self.measurementLabel, self.measurementIndex)
		await measurement.run()

		measurement.writeToFile().plot()
		print('max:', round(measurement.getPeak('force'), 2))
		self.measurementIndex +=1

	async def cmdLabel(self, label, *pars):
		if label != None and label != self.measurementLabel:
			self.measurementLabel = label
			self.measurementIndex = 1

	async def cmdTara(self, *pars) -> None:
		taraReadings = int(pars[0]) if pars[0] else DEFAULT_TARA_READINGS
		print(c.blue('Tara, n=' + str(taraReadings)))
		await self.taraChar.writeValue(taraReadings)

	# TODO - non-functional
	async def cmdCalibrate(self, *pars) -> None:
		print(c.blue('calibrating'))
		await self.calibrateChar.writeValue(9072.6, float)

	async def cmdMonitor(self, *pars) -> None:
		print(c.blue('monitor'))

	# public ----------------------------------------------------------------------------------------------------------
	async def startMeasure(self):
		await self.measureChar.writeValue(True)

	async def stopMeasure(self):
		await self.measureChar.writeValue(False)

	# main loop -------------------------------------------------------------------------------------------------------
	async def start(self) -> None:
		exit = False
		attempts = 0
		while (not exit and attempts < RECONNECT_ATTEMPTS):
			try:
				print(c.blue('Connecting to ESP...'))
				try:
					async with BleakClient(self.device) as client:
						# reset attempts
						attempts = 0

						self.taraChar = BLECharacteristic(client, TARA_CHAR_UUID, int)
						self.calibrateChar = BLECharacteristic(client, CALIBRATE_CHAR_UUID, float)
						self.measureChar = BLECharacteristic(client, MEASURE_CHAR_UUID, bool)
						self.forceChar = BLECharacteristic(client, FORCE_CHAR_UUID, float)
						print("Connected to ESP, enter command " + c.bold(CMDS))

						# start force tracker
						self.measureEvent = asyncio.Event()
						self.measureData = {
							"time": time(),
							"force": 0,
						}
						def forceCallback(force):
							self.measureData["force"] = force
							self.measureData["time"] = time()
							self.measureEvent.set()
							self.measureEvent.clear()
						await self.forceChar.startNotify(forceCallback)

						# user input loop
						while (not exit):
							inp = input(c.bold(self.measurementLabel + '@[') + c.yellow(client.address) + c.bold(']$ ')).split(' ')
							inp.extend([None for _ in range(2)])
							[cd, *parameters] = inp[0:3]

							# eval input
							if cd == 'exit' or cd == 'x':
								exit = True
							elif cd == 'tara' or cd == 't':
								await self.cmdTara(*parameters)
							elif cd == 'measure' or cd == 'm':
								await self.cmdMeasure(*parameters)
							elif cd == 'monitor':
								await self.cmdMonitor(*parameters)
							elif cd == 'calibrate' or cd == 'c':
								await self.cmdCalibrate(*parameters)
							elif cd == 'label' or cd == 'l':
								await self.cmdLabel(*parameters)
							else:
								print(c.red('enter valid command ') + CMDS)

						print(c.blue('Disconnecting...'))
						await self.forceChar.stopNotify()

				# Handle General Exceptions
				except Exception as e:
					if True: # TODO: Filter connection errors
						raise e
					else:
						# Do not reconnect in case of software error
						print(c.red('Error'))
						exit = True

			# Handle Comm Exceptions
			except Exception as e:
				traceback.print_exc()
				traceback.print_stack()
				attempts += 1
				print(c.red("Connection failed ") + '[' + str(attempts) + '/' + str(RECONNECT_ATTEMPTS) + ']')
