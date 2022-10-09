class Colors:
	def __init__(self) -> None:
		pass

	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	YELLOW = '\033[0;33m'
	RED = '\033[0;31m'

	WARNING = '\033[93m'
	FAIL = '\033[91m'

	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	ENDC = '\033[0m'

	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.ENDC = ''

	def blue(self, str: str) -> str:
		return self.OKBLUE + str + self.ENDC

	def bold(self, str: str) -> str:
		return self.BOLD + str + self.ENDC

	def green(self, str: str) -> str:
		return self.OKGREEN + str + self.ENDC

	def yellow(self, str: str) -> str:
		return self.YELLOW + str + self.ENDC

	def red(self, str: str) -> str:
		return self.RED + str + self.ENDC
