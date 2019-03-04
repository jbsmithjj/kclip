from setuptools import setup

with open("README.rst", 'r') as f:
    long_description = f.read()

setup(
   name='kclip',
   version='1.0',
   description='Parse Kindle Clippings text file',
   license="MIT",
   long_description=long_description,
   author='Jeremy B. Smith',
   author_email='jbsmithjj@gmail.com',
   url="http://www.foopackage.com/",
   py_modules=['kclip']
)
 