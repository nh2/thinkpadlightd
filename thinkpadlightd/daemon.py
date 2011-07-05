import socketserver
import sys

ADDR = HOST, PORT = "localhost", 9698
LIGHT_DEVICE_PATH = "/proc/acpi/ibm/light"

# Use a threaded TCP server so that multiple clients can be connected to change lights
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	daemon_threads = True  # Let all server threads die on Ctrl-C
	allow_reuse_address = True  # Don't wait for long socket reuse timeouts

	def __init__(self, lightd, *args, **kw):
		super().__init__(*args, **kw)
		# The server must know about the light daemon instance
		# such that the LightHandler can access it
		self.lightd = lightd

# Print helper to flush without printing newlines
def log(a):
	print(a, end='')
	sys.stdout.flush()

class LightHandler(socketserver.StreamRequestHandler):

	# Executed once per connection
	def handle(self):

		# Multiple messages must be handled manually with a while loop
		while True:
			try:
				self.data = self.rfile.readline().strip()
			except KeyboardInterrupt:
				return
			if not self.data:  # EOF
				return
			if self.data in (b"0",b"1"):
				cmd = self.data
				log(cmd.decode('ascii'))
				# The server knows about the handler, not the handler;
				# this is because we cannot call constructors of handlers ourselves as they are created with TCPServer(ADDR, Handler)
				self.server.lightd.set_light(int(cmd))
				self.wfile.write(cmd + b"\n")
			else:  # Invalid message
				log("i")
				self.wfile.write(b"i\n")
				return

class ThinkpadlightdException(Exception):
	pass

class LightDeviceFileException(ThinkpadlightdException):
	def __init__(self, path):
		self.path = path

class LightDeviceFileNotFoundException(LightDeviceFileException):
	def __str__(self):
		return "%s does not exist. Please make sure your device is supported: on http://www.thinkwiki.org/wiki/ThinkLight" % self.path

class LightDeviceFileNotWritableException(LightDeviceFileException):
	def __str__(self):
		return "%s is not open for writing. This program must be run as root!" % self.path


class Thinkpadlightd(object):

	def __init__(self, addr=ADDR, light_device_path=LIGHT_DEVICE_PATH):
		self.ADDR = self.HOST, self.PORT = addr
		self.LIGHT_DEVICE_PATH = light_device_path

	def set_light(self, status):
		self.light_file.write("on" if status else "off")
		self.light_file.flush()

	def run(self):
		try:
			# TODO This with statement assigning to self.light_file does not look to clean...
			with open(self.LIGHT_DEVICE_PATH, "w") as self.light_file:
				server = ThreadedTCPServer(self, self.ADDR, LightHandler)
				server.serve_forever()
		except IOError as e:
			if e.errno == 2:  # 2 is "No such file or directory"
				raise LightDeviceFileNotFoundException(self.LIGHT_DEVICE_PATH)
			elif e.errno == 13:  # 13 is "Permission denied"
				raise LightDeviceFileNotWritableException(self.LIGHT_DEVICE_PATH)
			else:
				raise
