==========
python-osc
==========

Open Sound Control server and client implementations in **pure python** (3.3+).

--------------
Current status
--------------

This library was developped following the specifications at
http://opensoundcontrol.org/spec-1_0
and is currently in a stable state.

--------
Features
--------

* UDP blocking/threading/forking server implementations
* UDP client
* int, float, string, blob OSC arguments
* extensive unit test coverage
* basic client and server examples

To come:
* more argument types

============
Installation
============

python-osc is a pure python library that has no external dependencies,
to install it just use pip (prefered):

.. code-block:: bash

    $ pip install python-osc

or from the raw sources for the development version:

.. code-block:: bash

    $ python setup.py test
    $ python setup.py install

========
Examples
========

-------------
Simple client
-------------
.. literalinclude:: examples/simple_client.py
