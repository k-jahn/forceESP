"""Force ESP Measurement Class

filesystem i/o
processing/analysis"""

import subprocess
import json
from datetime import datetime
from time import time
from pathlib import Path

from classes.helpers import clr

from constants import (
	MEASUREMENT_BASE_PATH
)

class Measurement:
	def __init__(self) -> None:
		self.measurementInterval: float
		self.label: str
		self.subject: str
		self.headers = ['time', 'force']
		self.dataset = []

		self.name: str
		self.timestamp: str
		self.fileNameCSV: str
		self.fileNameJSON: str

	# gathers data from forceEsp
	async def run(self, forceEsp, measurementInterval: float, label: str, subject: str) -> None:
		self.measurementInterval = measurementInterval
		self.label = label
		self.subject = subject
		assert len(self.dataset) == 0

		relativeTime = 0
		startTime = None
		self.timestamp = str(datetime.now()).replace(' ', '_')
		self.name = '_'.join([self.timestamp, self.label])

		print(clr.blue(f'measuring, Δt={self.measurementInterval}'))
		await forceEsp.startESPMeasure()
		while relativeTime <= self.measurementInterval:
			await forceEsp.measureEvent.wait()
			# start clock with first measurement
			startTime = time() if startTime is None else startTime
			relativeTime = forceEsp.measureData["time"] - startTime
			print(round(relativeTime, 2), '/', self.measurementInterval, '     ', end="\r")
			self.dataset.append([
				relativeTime,
				forceEsp.measureData["force"],
			])
		await forceEsp.stopESPMeasure()
		print('done                      ')
		return self

	def fromFile(self, fileName: str):
		jsonData: dict
		with open(fileName, encoding='UTF-8') as file:
			file.read()
			jsonData = json.load(file.read())
			file.close()
		self.subject = jsonData["subject"]
		self.label = jsonData["label"]
		self.timestamp = jsonData["timestamp"]
		self.measurementInterval = jsonData["interval"]
		self.headers = jsonData["datasetHeaders"]
		self.dataset = jsonData["dataset"]
		self.fileNameJSON = fileName
		return self

	def writeToFile(self):
		path = f'{MEASUREMENT_BASE_PATH}{self.subject}/'
		Path(path).mkdir(parents=True, exist_ok=True)
		self.fileNameCSV = f'{path}{self.name}.csv'
		self.fileNameJSON = f'{path}{self.name}.json'

		# csv - TODO remove once gnuplot removed
		with open(self.fileNameCSV, 'x', encoding='UTF-8') as file:
			file.write(','.join(self.headers) + '\n')
			for point in self.dataset:
				file.write(','.join([str(value) for value in point]) + '\n')
			file.close()

		# json
		with open(self.fileNameJSON, 'x', encoding='UTF-8') as file:
			jsonData = {
				"subject": self.subject,
				"label": self.label,
				"timestamp": self.timestamp,
				"interval": self.measurementInterval,
				"f_max": self.getPeak(),
				"datasetHeaders": self.headers,
				"dataset": self.dataset,
			}
			json.dump(jsonData, file)
			file.close()

		print(f'saved measurement to {clr.yellow(self.fileNameJSON)}')
		return self

	def plot(self):
		if self.fileNameCSV is None:
			self.writeToFile()
		subprocess.Popen([
			'./src/plot.sh',
			self.fileNameCSV,
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
