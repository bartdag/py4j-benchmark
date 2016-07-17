# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
import codecs
from collections import OrderedDict, namedtuple, deque
import csv
import datetime
import gc
from math import sqrt
import os
import platform
import subprocess
import sys
from threading import Thread
from time import time, sleep

DEFAULT_MAX_BYTES = 268435456

DEFAULT_MAX_ITERATIONS = 100

DEFAULT_THREAD_COUNT = 50

# 1 KB
MEDIUM_BYTES = 1024

# 1 MB
LARGE_BYTES = 1024 * 1024

# 10 MB
EXTRA_LARGE_BYTES = 10 * 1024 * 1024

DEFAULT_SEED = 17

DEFAULT_SLEEP_TIME = 0.1

STD_CLASS_NAME = "Py4JBenchmarkUtility"

PINNED_THREAD_CLASS_NAME = "Py4JPinnedThreadBenchmarkUtility"

DEFAULT_CSV_ENCODING = "ascii"

GC_COLLECT_RUN = 3

HEADER = ["test", "iterations", "mean", "stddev", "total", "python version",
          "java version", "py4j version", "os version", "cpu count", "date"]

STD_JAVA_SOURCE_FILE = "java/src/{0}.java".format(STD_CLASS_NAME)

PINNED_THREAD_JAVA_SOURCE_FILE =\
    "java/src/{0}.java".format(PINNED_THREAD_CLASS_NAME)

# 64 bytes once encoded to utf-8
DEFAULT_STRING = "Hello\nWorld\n\nTest1234567\néééééééééééééèèèèèè\n"

DEFAULT_STRING_BYTE_SIZE = len(DEFAULT_STRING.encode("utf-8"))

BenchStats = namedtuple(
    "BenchStats", ["iterations", "mean", "stddev", "total", "timestamp"])

if sys.version_info.major == 2:
    range = xrange  # noqa


def null_print(message):
    """Do not print anything
    """
    pass


def verbose_print(message):
    """Prints that uses stdout
    """
    print(message)

vprint = null_print


# UTILITY HERE


def run_gc_collect():
    for i in range(GC_COLLECT_RUN):
        gc.collect()


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


def benchmark(function, startup, cleanup, iterations):
    online_stats = OnlineStats()
    timestamp = datetime.datetime.now()
    for i in range(iterations):
        if startup:
            startup()
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
        online_stats.total,
        timestamp
    )


# TESTS HERE
class Echo(object):
    def echo(self, param):
        return param

    class Java:
        implements = ["Py4JBenchmarkUtility$Echo"]


class Countdown(object):

    def __init__(self):
        self.called = 0

    def countdown(self, count, countdown_object):
        self.called += 1
        if count == 0:
            return 0
        else:
            return countdown_object.countdown(count - 1, self)

    class Java:
        implements = ["Py4JBenchmarkUtility$Countdown"]


def java_instance_creation(options, gateway):
    StringBuilder = gateway.jvm.StringBuilder

    def func():
        StringBuilder()

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def java_static_method_call(options, gateway):
    System = gateway.jvm.System

    def func():
        System.currentTimeMillis()

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def java_list(options, gateway):

    def func():
        al = gateway.jvm.java.util.ArrayList()
        al2 = gateway.jvm.java.util.ArrayList()
        al1orig = gateway.jvm.java.util.ArrayList()

        al1orig.append(1)
        al.append(1)
        al2.append(2)
        al += al2
        if not(len(al) == 2 and str(al) == str(al) and al == al):
            raise Exception

        if not (al[0] == 1 and al[-1] == 2):
            raise Exception

        # For backward compatibility because Python 2 does not delegate
        # __ne__ to __eq__
        if not (al[:-1] == al1orig):
            raise Exception

        al[0] = 2

        al_sum = 0
        for el in al:
            al_sum += el

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def python_type_conversion(options, gateway):
    StringBuilder = gateway.jvm.StringBuilder

    def func():
        b = StringBuilder()
        b.append("a")
        b.append(-2)
        b.append(True)
        b.append(3000000000000)
        b.append(1.0/3.0)
        b.append(b)

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def python_medium_string(options, gateway):
    String = gateway.jvm.String
    size = min(MEDIUM_BYTES, options.max_bytes) // DEFAULT_STRING_BYTE_SIZE
    a_string = DEFAULT_STRING * size

    def func():
        String.valueOf(a_string)

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def python_large_string(options, gateway):
    String = gateway.jvm.String
    size = min(LARGE_BYTES, options.max_bytes) // DEFAULT_STRING_BYTE_SIZE
    a_string = DEFAULT_STRING * size

    def func():
        String.valueOf(a_string)

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def python_extra_large_string(options, gateway):
    String = gateway.jvm.String
    size = min(EXTRA_LARGE_BYTES, options.max_bytes)\
        // DEFAULT_STRING_BYTE_SIZE
    a_string = DEFAULT_STRING * size
    iterations = max(10, options.max_iterations // 100)

    def func():
        String.valueOf(a_string)

    return benchmark(func, None, run_gc_collect, iterations)


def python_multiple_calling_threads(options, gateway):

    threads_to_create = options.max_threads

    def inner_thread_func():
        sb = gateway.jvm.StringBuilder()
        sb2 = gateway.jvm.StringBuilder()
        sb.append(1)
        sb2.append("hello")
        sb.append(sb2)

    def func():
        threads = []
        for i in range(threads_to_create):
            t = Thread(target=inner_thread_func)
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def cleanup():
        run_gc_collect()
        gateway.close(keep_callback_server=True)

    return benchmark(func, None, cleanup, options.max_iterations)


def python_garbage_collection(options, gateway):
    """

    Note: there is no corresponding garbage collection test for the JVM because
    it is not deterministric and thus very difficult to reliably test.
    """
    StringBuffer = gateway.jvm.StringBuffer

    # Because Python 2 does not have a clear method on list...
    l = deque()

    def init():
        # 100 objects to compensate for the gc.collect() call
        for i in range(100):
            l.append(StringBuffer())

    def func():
        l.clear()
        # Redundant most of the time and adds time :-(
        gc.collect()

    return benchmark(func, init, run_gc_collect, options.max_iterations)


def python_simple_callback(options, gateway):

    entry_point = gateway.entry_point
    python_echo = Echo()

    def func():
        response = entry_point.callEcho(python_echo, 1)
        if response != 1:
            raise Exception

    return benchmark(func, None, run_gc_collect, options.max_iterations)


def python_recursive_callback(options, gateway):
    startCountdown = gateway.jvm.Py4JBenchmarkUtility.startCountdown
    pythonCountdown = Countdown()

    def func():
        startCountdown(20, pythonCountdown)
        if pythonCountdown.called != 11:
            raise Exception

    def cleanup():
        pythonCountdown.called = 0
        run_gc_collect()

    return benchmark(func, None, cleanup, options.max_iterations)


STD_TESTS = OrderedDict([
    ("java-instance-creation", java_instance_creation),
    ("java-static-method", java_static_method_call),
    ("java-list", java_list),
    ("python-type-conversion", python_type_conversion),
    ("python-medium-string", python_medium_string),
    ("python-large-string", python_large_string),
    ("python-extra-large-string", python_extra_large_string),
    ("python-multiple-calling-threads", python_multiple_calling_threads),
    ("python-garbage-collection", python_garbage_collection),
    ("python-simple-callback", python_simple_callback),
    ("python-recursive-callback", python_recursive_callback),
])

PINNED_THREAD_TESTS = OrderedDict([

])


# BENCHMARK STEPS HERE

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
        "--max-threads", dest="max_threads", action="store",
        type=int, default=DEFAULT_THREAD_COUNT,
        help="Maximum number of explicitly started threads.")
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


def start_java(java_path, py4j_jar_path, main_class, max_bytes):
    """Starts a Java process"""
    java_heap_size = (max_bytes // 1024 // 1024) + 768
    cmd_line = "{0} -Xmx{5}m -cp {1}{2}{3} {4}".format(
        java_path, py4j_jar_path, os.pathsep, "java/bin", main_class,
        java_heap_size)
    process = subprocess.Popen(cmd_line, shell=True, stdout=None, stderr=None,
                               stdin=None, close_fds=True)
    sleep(DEFAULT_SLEEP_TIME * 10)
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
    if has_pinned_thread():
        from py4j.java_gateway import (
            GatewayParameters, CallbackServerParameters)
        return JavaGateway(
            gateway_parameters=GatewayParameters(),
            callback_server_parameters=CallbackServerParameters())
    else:
        return JavaGateway(start_callback_server=True)


def get_pinned_thread_gateway():
    """Get Py4J ClientServer that can work with both sides.
    """
    from py4j.clientserver import ClientServer
    client_server = ClientServer()
    return client_server


def run_standard_tests(options, results):
    """Runs the full standard test suite.
    """
    start_java(options.java_path, options.py4j_jar_path, STD_CLASS_NAME,
               options.max_bytes)
    gateway = get_gateway()

    try:
        _run_tests(options, results, gateway, STD_TESTS)
    finally:
        gateway.shutdown()

    sleep(DEFAULT_SLEEP_TIME * 10)


def run_pinned_thread_tests(options, results):
    pass


def _run_tests(options, results, gateway, test_dict):
    for test_name, test in test_dict.items():
        stats = test(options, gateway)
        results[test_name] = stats
        if options.verbose:
            report_verbose_result(test_name, stats)
        run_gc_collect()
        # This is not perfect because callback connections
        # are not closed and are kept for 30s so next connection will be
        # fast...
        gateway.close(keep_callback_server=True)
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
            stat_list = list(stat)
            writer.writerow(
                [test_name] + stat_list[:-1] + suffix +
                [stat.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")])


def report_verbose_result(test_name, result):
    msg = "Test {0} - avg: {1}s, stddev: {2}s, total: {3}s, "\
        "iterations: {4}".format(
            test_name, result.mean, result.stddev, result.total,
            result.iterations)
    vprint(msg)


def main():
    parser = get_parser()
    args = parser.parse_args()
    results = OrderedDict()

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
