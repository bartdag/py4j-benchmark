from __future__ import unicode_literals
import argparse
import codecs
from collections import OrderedDict, namedtuple
import csv
import gc
import os
import platform
import sys
from time import time, sleep

DEFAULT_MAX_BYTES = 268435456

DEFAULT_MAX_ITERATIONS = 1000000

DEFAULT_SEED = 17

DEFAULT_SLEEP_TIME = 0.1

STD_CLASS_NAME = "StandardBenchmarkUtility"

PINNED_THREAD_CLASS_NAME = "PinnedBenchmarkUtility"

DEFAULT_CSV_ENCODING = "ascii"

GC_COLLECT_RUN = 10

HEADER = ["test", "iterations", "mean", "stddev", "total", "python version",
          "py4j version", "os version", "cpu count"]

BenchStats = namedtuple(
    "BenchStats", ["iterations", "mean", "stddev", "total"])


def null_print(message):
    """Do not print anything
    """
    pass


def verbose_print(message):
    """Prints that uses stdout
    """
    print(message)


vprint = null_print


# TESTS HERE

def java_instance_creation(gateway):
    start = time()
    stop = time()
    return BenchStats(1000, 50.23, 12.0, stop - start)


STD_TESTS = OrderedDict([
    ("java-instance-creation", java_instance_creation),
])

PINNED_THREAD_TESTS = OrderedDict([

])


def get_parser():
    """Creates the command line argument parser.
    """
    parser = argparse.ArgumentParser(description="Benchmarks Py4J")
    parser.add_argument(
        "py4j_jar_path", help="The path to the Py4J jar.")
    parser.add_argument(
        "--no-pinned-thread", dest="with_pinned_thread", action="store_false",
        default=True,
        help="Test pinned thread ClientServer. Not available before 0.10")
    parser.add_argument(
        "--csv-output", dest="csv_output", action="store",
        help="Where to save a csv output of the benchmark results.")
    parser.add_argument(
        "--append-to-csv", dest="append_to_csv", action="store_true",
        default=False,
        help="Append to the csv file and do not rewrite the header "
        "if the file exists.")
    parser.add_argument(
        "--javac-path", dest="javac_path", action="store",
        default="javac",
        help="Full path to javac. Otherwise javac is invoked with "
        "current PATH")
    parser.add_argument(
        "--java-path", dest="java_path", action="store",
        default="java",
        help="Full path to java. Otherwise java is invoked with "
        "current PATH")
    parser.add_argument(
        "--max-bytes", dest="max_bytes", action="store",
        type=int, default=DEFAULT_MAX_ITERATIONS,
        help="Maximum number of bytes transferred from either sides")
    parser.add_argument(
        "--max-iterations", dest="max_iterations", action="store",
        type=int, default=DEFAULT_MAX_ITERATIONS,
        help="Maximum number of iterations. Determine the testing time.")
    parser.add_argument(
        "--seed", dest="seed", action="store",
        type=int, default=DEFAULT_SEED,
        help="Seed to use to generate random data.")
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true",
        default=False,
        help="Print information as the benchmark progresses")
    return parser


def compile_java(javac_path, py4j_jar_path, compile_pinned_thread):
    """Compiles the Java utility classes used for the benchmark.
    """
    pass


def start_java(java_path, py4j_jar_path, main_class):
    """Starts a Java process"""
    pass


def has_pinned_thread():
    try:
        from py4j.clientserver import ClientServer
        if ClientServer:
            return True
    except ImportError:
        pass
    return False


def get_gateway():
    """Get Py4J JavaGateway that can work with both sides.
    """
    # Do some magic here to determine if we are running old or new py4j
    # versions.
    from py4j.java_gateway import JavaGateway
    return JavaGateway()


def get_pinned_thread_gateway():
    """Get Py4J ClientServer that can work with both sides.
    """
    from py4j.clientserver import ClientServer
    client_server = ClientServer()
    return client_server


def get_python_version():
    """Gets a friendly python version.
    """
    import platform
    version = sys.version_info
    impl = platform.python_implementation()
    return "{0} {1}.{2}.{3}".format(
        impl, version.major, version.minor, version.micro)


def get_py4j_version():
    from py4j import version
    return version.__version__


def get_os_version():
    return "{0} {1}".format(platform.system(), platform.release())


def get_cpu_count():
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except Exception:
        return -1


def run_standard_tests(options, results):
    """Runs the full standard test suite.
    """
    start_java(options.java_path, options.py4j_jar_path, STD_CLASS_NAME)
    gateway = get_gateway()
    _run_tests(options, results, gateway, STD_TESTS)


def run_pinned_thread_tests(options, results):
    pass


def run_gc_collect():
    for i in range(GC_COLLECT_RUN):
        gc.collect()


def _run_tests(options, results, gateway, test_dict):
    for test_name, test in test_dict.items():
        stats = test(gateway)
        results[test_name] = stats
        if options.verbose:
            report_verbose_result(test_name, stats)
        gc.collect()
        gateway.close()
        sleep(DEFAULT_SLEEP_TIME)


def report_results(options, results):
    csv_file_path = options.csv_output
    file_exists = os.path.exists(csv_file_path)
    mode = "a" if options.append_to_csv and file_exists else "w"
    suffix = [
        get_python_version(), get_py4j_version(), get_os_version(),
        get_cpu_count()]
    with codecs.open(
            csv_file_path, mode, encoding=DEFAULT_CSV_ENCODING) as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
        if not file_exists:
            writer.writerow(HEADER)
        for test_name, stat in results.items():
            writer.writerow([test_name] + list(stat) + suffix)


def report_verbose_result(test_name, result):
    msg = "Test {0} - avg: {1}s, stddev: {2}s, total: {3}s, "\
        "iterations: {4}".format(
            test_name, result.mean, result.stddev, result.total,
            result.iterations)
    vprint(msg)


def main():
    parser = get_parser()
    args = parser.parse_args()
    results = {}

    if args.verbose:
        global vprint
        vprint = verbose_print

    vprint("Starting benchmark")

    with_pinned_thread = args.with_pinned_thread and has_pinned_thread()
    vprint("With pinned thread? {0}".format(with_pinned_thread))

    vprint("Compiling java utility classe(s)")
    compile_java(args.javac_path, args.py4j_jar_path, with_pinned_thread)

    vprint("Running standard tests")
    run_standard_tests(args, results)

    if with_pinned_thread:
        vprint("Running pinned thread tests")
        run_pinned_thread_tests(args, results)

    if args.csv_output:
        vprint("Writing csv output")
        report_results(args, results)


if __name__ == "__main__":
    main()
