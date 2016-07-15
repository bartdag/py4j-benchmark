from __future__ import unicode_literals
import argparse
import codecs
from collections import OrderedDict, namedtuple
import csv
import gc
from math import sqrt
import os
import platform
import subprocess
import sys
from time import time, sleep

DEFAULT_MAX_BYTES = 268435456

DEFAULT_MAX_ITERATIONS = 1000

DEFAULT_SEED = 17

DEFAULT_SLEEP_TIME = 0.1

STD_CLASS_NAME = "Py4JBenchmarkUtility"

PINNED_THREAD_CLASS_NAME = "Py4JPinnedThreadBenchmarkUtility"

DEFAULT_CSV_ENCODING = "ascii"

GC_COLLECT_RUN = 3

HEADER = ["test", "iterations", "mean", "stddev", "total", "python version",
          "java version", "py4j version", "os version", "cpu count"]

STD_JAVA_SOURCE_FILE = "java/src/{0}.java".format(STD_CLASS_NAME)

PINNED_THREAD_JAVA_SOURCE_FILE =\
    "java/src/{0}.java".format(PINNED_THREAD_CLASS_NAME)

BenchStats = namedtuple(
    "BenchStats", ["iterations", "mean", "stddev", "total"])

if sys.version_info.major == 2:
    range = xrange


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

def java_instance_creation(options, gateway):
    StringBuilder = gateway.jvm.StringBuilder

    def func():
        StringBuilder()

    def cleanup():
        run_gc_collect()

    return benchmark(func, cleanup, options.max_iterations)


STD_TESTS = OrderedDict([
    ("java-instance-creation", java_instance_creation),
])

PINNED_THREAD_TESTS = OrderedDict([

])


class OnlineStats(object):
    """
    Welford's algorithm computes the sample variance incrementally.

    Source: http://stackoverflow.com/a/5544108/131427

    Fixed by bart :-)
    """

    def __init__(self, iterable=None, ddof=1):
        self.n = 1
        self.mean = 0.0
        self.total = 0.0
        self.s = 0.0
        if iterable is not None:
            for datum in iterable:
                self.include(datum)

    def include(self, datum):
        self.total += datum
        tempMean = self.mean
        self.mean += (datum - tempMean) / self.n
        self.s += (datum - tempMean) * (datum - self.mean)
        self.n += 1

    @property
    def size(self):
        return self.n - 1

    @property
    def variance(self):
        if self.n > 2:
            return self.s / (self.n - 2)
        else:
            return 0

    @property
    def std(self):
        return sqrt(self.variance)


def benchmark(function, cleanup, iterations):
    online_stats = OnlineStats()
    for i in range(iterations):
        start = time()
        function()
        stop = time()
        if cleanup:
            cleanup()
        online_stats.include(stop-start)
    return BenchStats(
        iterations,
        online_stats.mean,
        online_stats.std,
        online_stats.total
    )


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
        type=int, default=DEFAULT_MAX_BYTES,
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
    if compile_pinned_thread:
        classes = STD_JAVA_SOURCE_FILE + " " + PINNED_THREAD_JAVA_SOURCE_FILE
    else:
        classes = STD_JAVA_SOURCE_FILE

    cmd_line = "{0} -d java/bin -cp {1} {2}".format(
        javac_path, py4j_jar_path, classes)
    output = subprocess.call(cmd_line, shell=True)
    if output != 0:
        raise Exception("Could not compile utility classes. Error code: {0}"
                        .format(output))


def start_java(java_path, py4j_jar_path, main_class):
    """Starts a Java process"""
    cmd_line = "{0} -cp {1}{2}{3} {4}".format(
        java_path, py4j_jar_path, os.pathsep, "java/bin", main_class)
    process = subprocess.Popen(cmd_line, shell=True, stdout=None, stderr=None,
                               stdin=None, close_fds=True)
    sleep(DEFAULT_SLEEP_TIME * 5)
    return process


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


def get_java_version(options):
    cmd_line = "{0} -version".format(options.java_path)
    version = subprocess.check_output(
        cmd_line, stderr=subprocess.STDOUT, shell=True).decode("ascii")
    version = version.split("\n")[0].split('"')[1]
    return version


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

    try:
        _run_tests(options, results, gateway, STD_TESTS)
    except Exception:
        gateway.shutdown()
        raise

    gateway.shutdown()
    sleep(DEFAULT_SLEEP_TIME * 5)


def run_pinned_thread_tests(options, results):
    pass


def run_gc_collect():
    for i in range(GC_COLLECT_RUN):
        gc.collect()


def _run_tests(options, results, gateway, test_dict):
    for test_name, test in test_dict.items():
        stats = test(options, gateway)
        results[test_name] = stats
        if options.verbose:
            report_verbose_result(test_name, stats)
        run_gc_collect()
        gateway.close()
        sleep(DEFAULT_SLEEP_TIME)


def report_results(options, results):
    csv_file_path = options.csv_output
    file_exists = os.path.exists(csv_file_path)
    mode = "a" if options.append_to_csv and file_exists else "w"
    suffix = [
        get_python_version(), get_java_version(options), get_py4j_version(),
        get_os_version(), get_cpu_count()]
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
