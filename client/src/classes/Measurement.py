# Force ESP Measurement Class
#
# filesystem i/o
# processing/analysis

import subprocess
from datetime import datetime
import asyncio
from time import time
from classes.helpers.Colors import Colors

c = Colors()

class Measurement:
	def __init__(self, forceEsp, measurementInterval) -> None:
		self.measurementInterval = measurementInterval
		self.headers = ['time', 'force']
		self.dataset = []
		self.forceEsp = forceEsp

	# gathers data from forceEsp
	async def start(self) -> None:
		relativeTime = 0
		startTime = time()
		self.timestamp = str(datetime.now())

		print(c.blue('measuring, Δt=' + str(self.measurementInterval)))
		while relativeTime <= self.measurementInterval:
			await self.forceEsp.measureEvent.wait()
			relativeTime = self.forceEsp.measureData["time"] - startTime
			print(round(relativeTime, 2), '/', self.measurementInterval, '     ', end="\r")
			self.dataset.append([
				relativeTime,
				self.forceEsp.measureData["force"],
			])
		print('done                      ')
		return self

	def writeToFile(self):
		self.fileName = '../measurements/' + self.timestamp + '.csv'
		file = open(self.fileName, 'x')
		file.write(','.join(self.headers) + '\n')
		for point in self.dataset:
			file.write(','.join([str(value) for value in point]) + '\n')
		file.close()
		return self

	def plot(self):
		if (self.fileName == None): self.writeToFile()
		subprocess.Popen([
			'./plot.sh',
			self.fileName,
			self.timestamp,
			str(round(self.getPeak(), 2)),
			str(self.measurementInterval),
		])
		return self

	def getPeak(self, column: int or str = 1) -> float:
		index = None
		try:
			if type(column) is int and column in range(len(self.headers)):
				index = column
			elif type(column) is str:
				index = self.headers.index(column)
			else:
				raise Exception()
		except:
			raise Exception('column not found')
		return max([el[index] for el in self.dataset])
