"""
DEBUG
INFO
WARNING
ERROR
CRITICAL
"""

import logging

# Create a custom logger
bLogger = logging.getLogger('canvasApp')
bLogger.setLevel(logging.DEBUG)

print('bLogger:', bLogger)

# Create handlers
consoleHandler = logging.StreamHandler()
fileHandler = logging.FileHandler('bCanvasApp.log')
consoleHandler.setLevel(logging.DEBUG)
fileHandler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
consoleFormat = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
fileFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

FORMAT = logging.Formatter("[%(levelname)s - %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

consoleHandler.setFormatter(FORMAT)
fileHandler.setFormatter(FORMAT)

# Add handlers to the logger
bLogger.addHandler(consoleHandler)
bLogger.addHandler(fileHandler)

#bLogger.warning('This is a warning')
#bLogger.error('This is an error')
bLogger.info('bLogger initialized')
