""""Color helper Class

formats colored output via ANSI"""

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

	def blue(self, string: str) -> str:
		return self.OKBLUE + string + self.ENDC

	def bold(self, string: str) -> str:
		return self.BOLD + string + self.ENDC

	def green(self, string: str) -> str:
		return self.OKGREEN + string + self.ENDC

	def yellow(self, string: str) -> str:
		return self.YELLOW + string + self.ENDC

	def red(self, string: str) -> str:
		return self.RED + string + self.ENDC
