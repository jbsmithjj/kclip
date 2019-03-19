from setuptools import setup

with open("README.rst", 'r') as f:
    long_description = f.read()

setup(
   name='kclip',
   version='1.0.1',
   description='Parse Kindle Clippings text file',
   license="MIT",
   long_description=long_description,
   author='Jeremy B. Smith',
   author_email='jbsmithjj@gmail.com',
   url="https://github.com/jbsmithjj/kclip",
   py_modules=['kclip']
)
 