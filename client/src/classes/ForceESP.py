# Force ESP controller class
#
# handles BLE communication, user input

import asyncio
from pickle import FALSE
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

CMDS = "[tara, measure [int], exit]"

# # helperrm
class ForceESP:
	def __init__(self, device):
		self.device = device


	async def start(self):
		exit = False
		attempts = 0
		while (not exit and attempts < RECONNECT_ATTEMPTS):
			try:
				print(c.blue('Connecting to ESP...'))
				try:
					async with BleakClient(self.device) as client:
						# reset attempts
						attempts = 0

						taraChar = BLECharacteristic(client, TARA_CHAR_UUID)
						calibrateChar = BLECharacteristic(client, CALIBRATE_CHAR_UUID)
						measureChar = BLECharacteristic(client, MEASURE_CHAR_UUID)
						forceChar = BLECharacteristic(client, FORCE_CHAR_UUID)
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
						await forceChar.startNotify(forceCallback)

						# user input loop
						while (not exit):
							inp = input(c.bold("forceESP@[") + c.yellow(client.address) + c.bold(']$ ')).split(' ')
							inp.append('')
							[cd, pr1] = inp[0:2]
							try:
								p1 = float(pr1)
							except:
								p1 = None

							# eval input
							if cd == 'exit' or cd == 'x':
								exit = True
							elif cd == 'tara' or cd == 't':
								taraReadings = int(p1) if p1 else DEFAULT_TARA_READINGS
								print(c.blue('Tara, n=' + str(taraReadings)))
								await taraChar.writeValue(taraReadings)
							elif cd == 'measure' or cd == 'm':
								measurementInterval = p1 if  p1 and p1 > 0 else DEFAULT_MEASUREMENT_INTERVAL
								measurement = Measurement(self, measurementInterval)

								await measureChar.writeValue(True)
								await measurement.start()
								await measureChar.writeValue(False)

								measurement.writeToFile().plot()
								print('max:', round(measurement.getPeak('force'), 2))
							elif cd == 'monitor':
								# TODO
								pass
							elif cd == 'calibrate':
								# TODO
								pass
							else:
								print(c.red('enter valid command ') + CMDS)
						print(c.blue('Disconnecting...'))
						await forceChar.stopNotify()
				except Exception as e:
					if True: # TODO: Filter connection errors
						raise e
					else:
						# Do not reconnect in case of software error
						print(c.red('Error'))
						traceback.print_exc()
						traceback.print_stack()
						exit = True
			except Exception as e:
				attempts += 1
				print(c.red("Connection failed ") + '[' + str(attempts) + '/' + str(RECONNECT_ATTEMPTS) + ']')
