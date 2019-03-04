kclip
=====

**kclip** reads Kindle clipping text files and generates objects suitable for further processing.

Installation & Requirements
---------------------------

* Python >=3.7 (only tested with Python 3.7)
* ``pip install kclip``

Usage
-----

**Module usage**::

    import kclip
    for clipping in get_clippings_from_filename(source_filename):
        # do something with the generated object
        print(clipping)


**Command-line demo**:

Iterate the generated objects and print them to stdout:

* ``kclip.py -i source_filename``



**Tests**:

* ``test_kclip.py``


License
-------
MIT, see ``LICENSE.txt``, `jbsmithjj@gmail.com <mailto:jbsmithjj@gmail.com>`_