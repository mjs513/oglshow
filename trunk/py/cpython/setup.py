"""Build the smaz python module."""
from distutils.core import setup, Extension

setup(
    name = "cobj",
    version = "1.0",
    description = 'Python interface for smaz',
    author = 'Benjamin Sergeant',
    author_email = 'bsergean@gmail.com',

    ext_modules = [
        Extension("cobj", sources=["cobj.c"]),
        ],
    )
