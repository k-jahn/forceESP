# BLEChar helper class
# 
# enriches BleakCharacteristic with some syntactic sugar and less pain

from bleak import BleakClient
from struct import pack

class BLECharacteristic:
	def __init__(self, client: BleakClient, uuid: str) -> None:
		self.client = client
		self.char = client.services.get_characteristic(uuid)

	async def startNotify(self, callback):
		await self.client.start_notify(self.char, callback)
		return self

	async def stopNotify(self):
		await self.client.stop_notify(self.char)
		return self

	async def writeValue(self, value: bool or float or int, overrideFormatType: type=None):
		formatType = overrideFormatType if overrideFormatType != None else type(value)
		if formatType is bool:
			val = bytearray(pack('i', 1)) if value else bytearray(pack('i', 0))
		elif formatType is float:
			val = bytearray(pack('f', value))
		elif formatType is int:
			val = bytearray(pack('i', value))
		else:
			raise Exception('type unknown')
		await self.client.write_gatt_char(self.char, val)
		return self

	async def getValue(self):
		return await self.client.read_gatt_char(self.char)
