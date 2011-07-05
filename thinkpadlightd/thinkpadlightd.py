#!/usr/bin/env python3

def main():
	"""
	Starts a thinkpadlightd on the default host/port localhost:9698.
	It can be connected to via netcat: "nc localhost 9698"; writing "1" and "0" turns the light on and off.
	"""

	import sys
	if sys.version_info[:2] < (3,1):
		sys.stderr.write("Python >= 3.1 is required to run thinkpadlightd\n")
		exit(1)

	from daemon import Thinkpadlightd
	from daemon import ThinkpadlightdException

	try:
		Thinkpadlightd().run()
	except ThinkpadlightdException as e:
		print(e, file=sys.stdout)
		exit(1)
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
