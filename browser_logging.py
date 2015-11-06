# coding: UTF-8
import json
import logging
import re
from StringIO import StringIO
import threading

LEVELS = {
	logging.NOTSET: '',
	logging.DEBUG: '',  # equals to 'log'
	logging.INFO: 'info',
	logging.WARNING: 'warn',
	logging.ERROR: 'error',
	logging.CRITICAL: 'error',
}


def _interleave(msg, args):
	""" Returns a list from a template string and arguments.
		
		>>> a, b, c = 'a', 'b', 'c'
		>>> _interleave("This is my log %s: %s, %s", (a, b, c))
		... ["this is my log ", "a", ": ", "b", ", ", "c"]
		
	:param msg: string template
	:param args: sequence arguments
	:return: list
	"""
	template = re.split("(%s|%r)", msg)
	args = list(args)
	for n, part in enumerate(template):
		if part == "%s" or part == "%r":
			try:
				template[n] = args.pop(0)
			except IndexError:
				pass
	return template + args


class BrowserLoggingFormatter(object):
	""" This is useful to send down to the browser even complex object
		that can be examined in the Console Tab.
	"""

	def format(self, record):
		if isinstance(record.args, dict):
			# if you supply a single dict to the logging functions,
			# then args won't be a list but instead a dictionary.
			args = [record.args]
		else:
			args = record.args
		return _interleave(record.msg, args)


class BrowserLoggingHandler(logging.Handler):
	header_name = 'X-ChromeLogger-Data'
	version = 1
	
	def __init__(self):
		logging.Handler.__init__(self)
		self._threadlocal = threading.local()
		self.formatter = BrowserLoggingFormatter()

	def emit(self, record):
		tl = self._threadlocal
		if not hasattr(tl, 'logs'):
			self._clear()
		
		try:
			msg = self.format(record)
			if isinstance(msg, basestring):
				msg = [msg]
				
			backtrace_info = "{0} : {1}".format(record.filename, record.lineno)
			if backtrace_info in tl.backtrace_stack:
				backtrace_info = None
			else:
				tl.backtrace_stack.add(backtrace_info)
			
			self._threadlocal.logs.append((msg, backtrace_info, LEVELS.get(record.levelno, '')))
		except (KeyboardInterrupt, SystemExit):
			raise
		except:
			self.handleError(record)
	
	def _clear(self):
		""" Clear log data
		:return:
		"""
		self._threadlocal.logs = []
		self._threadlocal.backtrace_stack = set()
	
	def flush_headers(self):
		json_data = json.dumps({
			'version': self.version,
			'columns': ['log', 'backtrace', 'type'],
			'rows': getattr(self._threadlocal, 'logs', [])
		}, default=lambda obj: repr(obj))
		json_data = json_data.encode('utf-8')
		json_data = json_data.encode('base64').replace('\n', '')
		# FIXME: cosa fare se il log supera i 250kb?
		headers = [(self.header_name, json_data)]
		self._clear()
		return headers


class FakeStartResponse(object):
	def __init__(self):
		self.status = "200 OK"
		self.headers = []
		self.exc_info = None
		self.fake_handler = StringIO()
	
	def __call__(self, status, headers, exc_info=None):
		self.status = status
		self.headers = self.headers
		self.exc_info = exc_info
		return self.fake_handler.write


class BrowserLoggingMiddleware(object):
	""" Wraps a WSGI application and adds a BrowserLoggingHandler to
		the given logger. When the application ends, it extracts all
		the logging messages and renders them as ChromeLogger data.
	
	"""
	request_header = 'HTTP_X_BROWSERLOGGINGAUTH'
	
	def __init__(self, application, logger_name=None):
		
		self.application = application
		self.handler = BrowserLoggingHandler()
		self.request_password = request_password
		if logger_name:
			logger = logging.getLogger(logger_name)
		else:
			logger = logging.getLogger()
		logger.addHandler(self.handler)
	
	def __call__(self, environ, start_response):
		fsr = FakeStartResponse()
		output = self.application(environ, fsr)
		headers = fsr.headers + self.handler.flush_headers()

		write = start_response(fsr.status, headers)
		if fsr.fake_handler.tell():  # someone wrote to the start_response write handler
			fsr.fake_handler.seek(0)
			write(fsr.fake_handler.read())
		return output
