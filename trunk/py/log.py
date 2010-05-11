"""
Simple logger module based on the standard module logging (needs python 2.3).
"""
# Written by Benjamin Sergeant <bsergean@gmail.com>

import logging
from os import getpid

# TODO: Would be nice to have funcName here as well, but it's only available for python >- 2.5
# We print the pid to be ease the kill process
format = str(getpid())
format += "-%(levelname)s   [%(pathname)s:%(lineno)d] %(message)s"

# Create logger
logger = logging.getLogger('ogl')
logger.setLevel(logging.ERROR)

# Create handler and set level to debug
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(format))

# Add handler to the main logger instance
logger.addHandler(handler)

def quiet():
    logger.setLevel(logging.WARNING)

def noisy():
    logger.setLevel(logging.DEBUG)
