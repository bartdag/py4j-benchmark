Py4J-Benchmark
==============

This is the official benchmark suite for Py4J. It is available as a command
line client and integrates with tox for convenience.

Requirements
============

- Python 2.7, 3.4, or 3.5
- Java 6+
- Works with Py4J 0.8+
- Optional: tox

Usage
=====

::

    usage: py4jbench.py [-h] [--no-pinned-thread] [--csv-output CSV_OUTPUT]
        [--append-to-csv] [--javac-path JAVAC_PATH]
        [--java-path JAVA_PATH] [--max-bytes MAX_BYTES]
        [--max-iterations MAX_ITERATIONS] [--seed SEED]
        [--verbose]

Example:

::

	python py4jbench.py --verbose --csv-output test.csv --append-to-csv path/to/py4j0.10.2.1.jar

LICENSE
=======

Py4J-Benchmark is distributed with the BSD 3-Clause license. See LICENSE.txt for more
information.
