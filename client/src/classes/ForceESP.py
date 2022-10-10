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
DEFAULT_TARA_READINGS = 15

TARA_CHAR_UUID = '00000000-0000-0000-0000-000000001001'
CALIBRATE_CHAR_UUID = '00000000-0000-0000-0000-000000001002'
MEASURE_CHAR_UUID = '00000000-0000-0000-0000-000000001003'
FORCE_CHAR_UUID = '00000000-0000-0000-0000-000000001312'

c = Colors()

CMDS = "[tara [n], measure [s], monitor, calibrate, exit]"

class ForceESP:
	def __init__(self, device) -> None:
		self.device = device

	# command functions -----------------------------------------------------------------------------------------------
	async def measure(self, *pars) -> None:
		try:
			measurementInterval = float(pars[0])
		except:
			measurementInterval = DEFAULT_MEASUREMENT_INTERVAL

		measurement = Measurement(self, measurementInterval)

		await self.measureChar.writeValue(True)
		await measurement.start()
		await self.measureChar.writeValue(False)

		measurement.writeToFile().plot()
		print('max:', round(measurement.getPeak('force'), 2))

	async def tara(self, *pars) -> None:
		taraReadings = int(pars[0]) if pars[0] else DEFAULT_TARA_READINGS
		print(c.blue('Tara, n=' + str(taraReadings)))
		await self.taraChar.writeValue(taraReadings)

	# TODO - non-functional
	async def calibrate(self, *pars) -> None:
		print(c.blue('calibrating'))
		await self.calibrateChar.writeValue(9072.6, float)

	async def monitor(self, *pars) -> None:
		print(c.blue('monitor'))

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

						self.taraChar = BLECharacteristic(client, TARA_CHAR_UUID)
						self.calibrateChar = BLECharacteristic(client, CALIBRATE_CHAR_UUID)
						self.measureChar = BLECharacteristic(client, MEASURE_CHAR_UUID)
						self.forceChar = BLECharacteristic(client, FORCE_CHAR_UUID)
						print("Connected to ESP, enter command " + c.bold(CMDS))

						# start force tracker
						self.measureEvent = asyncio.Event()
						self.measureData = {
							"time": time(),
							"force": 0,
						}
						def forceCallback(char, data: bytearray):
							[ force ] = struct.unpack('f', data)
							self.measureData["force"] = force
							self.measureData["time"] = time()
							self.measureEvent.set()
							self.measureEvent.clear()
						await self.forceChar.startNotify(forceCallback)

						# user input loop
						while (not exit):
							inp = input(c.bold("forceESP@[") + c.yellow(client.address) + c.bold(']$ ')).split(' ')
							inp.extend([None for _ in range(2)])
							[cd, *parameters] = inp[0:3]

							# eval input
							if cd == 'exit' or cd == 'x':
								exit = True
							elif cd == 'tara' or cd == 't':
								await self.tara(*parameters)
							elif cd == 'measure' or cd == 'm':
								await self.measure(*parameters)
							elif cd == 'monitor':
								await self.monitor(*parameters)
							elif cd == 'calibrate' or cd == 'c':
								await self.calibrate(*parameters)
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
