# BLEChar helper class
# 
# enriches BleakCharacteristic with some syntactic sugar and less pain

from bleak import BleakClient
from struct import pack, unpack

class BLECharacteristic:
	def __init__(self, client: BleakClient, uuid: str, charType: type=None) -> None:
		self.client = client
		self.char = client.services.get_characteristic(uuid)
		self.type = charType

	# TODO handle data conversion
	async def startNotify(self, callback):
		def notifyCallback(_char, bleData: bytearray):
			if self.type is float:
				[ data ] = unpack('f', bleData)
			else:
				raise Exception('type unknown')
			callback(data)
		await self.client.start_notify(self.char, notifyCallback)
		return self

	async def stopNotify(self):
		await self.client.stop_notify(self.char)
		return self

	async def writeValue(self, value: bool or float or int):
		if self.type is bool:
			val = bytearray(pack('i', 1)) if value else bytearray(pack('i', 0))
		elif self.type is float:
			val = bytearray(pack('f', value))
		elif self.type is int:
			val = bytearray(pack('i', value))
		else:
			raise Exception('type unknown')

		await self.client.write_gatt_char(self.char, val)
		return self

	async def getValue(self):
		return await self.client.read_gatt_char(self.char)
