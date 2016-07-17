Py4J-Benchmark
==============

:Version: 0.1.0

.. image:: https://img.shields.io/circleci/project/bartdag/py4j-benchmark.svg
    :target: https://circleci.com/gh/bartdag/py4j-benchmark

This is the official benchmark suite for Py4J. It is available as a command
line client and integrates with tox for convenience. It outputs the results of
the benchmark on standard output and can produce a csv file.

Requirements
============

- Python 2.7, 3.4, or 3.5
- Java 6+
- Works with Py4J 0.8+
- Optional: tox


Installation
============

Clone the repository and invoke the script with python py4jbench.py

Usage
=====

::

    usage: py4jbench.py [-h] [--no-pinned-thread] [--csv-output CSV_OUTPUT]
        [--append-to-csv] [--javac-path JAVAC_PATH]
        [--java-path JAVA_PATH] [--max-bytes MAX_BYTES]
        [--max-iterations MAX_ITERATIONS]
        [--max-threads MAX_THREADS] [--seed SEED] [--verbose]
        [--list] [--only ONLY_BENCHMARK]
        py4j_jar_path


    Benchmarks Py4J

    positional arguments:
    py4j_jar_path         The path to the Py4J jar.

    optional arguments:
    -h, --help            show this help message and exit
    --no-pinned-thread    Test pinned thread ClientServer. Not available before
                            0.10
    --csv-output CSV_OUTPUT
                            Where to save a csv output of the benchmark results.
    --append-to-csv       Append to the csv file and do not rewrite the header
                            if the file exists.
    --javac-path JAVAC_PATH
                            Full path to javac. Otherwise javac is invoked with
                            current PATH
    --java-path JAVA_PATH
                            Full path to java. Otherwise java is invoked with
                            current PATH
    --max-bytes MAX_BYTES
                            Maximum number of bytes transferred from either sides
    --max-iterations MAX_ITERATIONS
                            Maximum number of iterations. Determine the testing
                            time.
    --max-threads MAX_THREADS
                            Maximum number of explicitly started threads.
    --seed SEED           Seed to use to generate random data.
    --verbose             Print information as the benchmark progresses
    --list                Lists all benchmark tests
    --only ONLY_BENCHMARK
                            Run only the selected benchmark


Usage Examples
==============

::

    # Run benchmark on currently installed Py4J
    python py4jbench.py --verbose --csv-output report.csv --append-to-csv path/to/py4j0.10.2.1.jar

    # List all supported environments
    tox --listenvs

    # Run benchmark on one environment. Generates report.csv
    tox -e py27-py4j092

    # Run benchmark on all supported environments. Generates report.csv
    tox

LICENSE
=======

Py4J-Benchmark is distributed with the BSD 3-Clause license. See LICENSE.txt for more
information.
