"""Force ESP Measurement Class

filesystem i/o
processing/analysis"""

import subprocess
from datetime import datetime
from time import time
from pathlib import Path

from classes.helpers import clr

from constants import (
	MEASUREMENT_BASE_PATH
)

class Measurement:
	def __init__(self, forceEsp, measurementInterval: float, label: str, subject: str) -> None:
		self.measurementInterval = measurementInterval
		self.label = label
		self.subject = subject
		self.headers = ['time', 'force']
		self.dataset = []
		self.forceEsp = forceEsp
		self.hasRun = False

		self.name: str
		self.timestamp: str
		self.fileName: str

	# gathers data from forceEsp
	async def run(self) -> None:
		assert not self.hasRun
		self.hasRun = True

		relativeTime = 0
		startTime = None
		self.timestamp = str(datetime.now()).replace(' ', '_')
		self.name = '_'.join([self.timestamp, self.label])

		print(clr.blue('measuring, Δt=' + str(self.measurementInterval)))
		await self.forceEsp.startESPMeasure()
		while relativeTime <= self.measurementInterval:
			await self.forceEsp.measureEvent.wait()
			# start clock with first measurement
			startTime = time() if startTime is None else startTime
			relativeTime = self.forceEsp.measureData["time"] - startTime
			print(round(relativeTime, 2), '/', self.measurementInterval, '     ', end="\r")
			self.dataset.append([
				relativeTime,
				self.forceEsp.measureData["force"],
			])
		await self.forceEsp.stopESPMeasure()
		print('done                      ')
		return self

	def writeToFile(self):
		path = f'{MEASUREMENT_BASE_PATH}{self.subject}/'
		Path(path).mkdir(parents=True, exist_ok=True)
		self.fileName = f'{path}{self.name}.csv'
		file = open(self.fileName, 'x', encoding='UTF-8')
		file.write(','.join(self.headers) + '\n')
		for point in self.dataset:
			file.write(','.join([str(value) for value in point]) + '\n')
		file.close()
		print(f'saved measurement to {clr.yellow(self.fileName)}')
		return self

	def plot(self):
		if self.fileName is None:
			self.writeToFile()
		subprocess.Popen([
			'./src/plot.sh',
			self.fileName,
			self.name.replace('_', ' '),
			str(round(self.getPeak(), 2)),
			str(self.measurementInterval),
		])
		return self

	def getPeak(self, column: int or str = 1) -> float:
		index = None
		try:
			if isinstance(column, int) and column in range(len(self.headers)):
				index = column
			elif isinstance(column, str):
				index = self.headers.index(column)
			else:
				raise Exception()
		except Exception as exc:
			raise Exception('column not found') from exc
		return max([el[index] for el in self.dataset])
