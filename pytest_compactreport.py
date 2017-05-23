# -*- coding: utf-8 -*-
from collections import defaultdict

import pytest
import sys
from _pytest.terminal import TerminalReporter


def pytest_addoption(parser):
    group = parser.getgroup('compactreport')
    group.addoption(
        '--compactreport',
        action='store_true',
        dest='compactreport',
        default=False,
        help='Compact reports by grouping failures.'
    )

    parser.addini('HELLO', 'Dummy pytest.ini setting')


@pytest.fixture
def compact_report(request):
    return request.config.option.compactreport



@pytest.mark.trylast
def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave, we are already active on the master
    if config.option.compactreport:
        # Get the standard terminal reporter plugin...
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        compacting_reporter = CompactingReporter(standard_reporter)

        # ...and replace it with our own compacting reporter.
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(compacting_reporter, 'terminalreporter')


def pytest_report_teststatus(report):
    pass


class CompactingReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw
        self.summary = defaultdict(set)

    def pytest_collectreport(self, report):
        # Show errors occurred during the collection instantly.
        TerminalReporter.pytest_collectreport(self, report)
        if report.failed:
            if self.isatty:
                self.rewrite('')  # erase the "collecting"/"collected" message
            self.print_summary(report)

    def pytest_runtest_logreport(self, report):
        # Show failures and errors occurring during running a test
        # instantly.
        TerminalReporter.pytest_runtest_logreport(self, report)
        if report.failed and not hasattr(report, 'wasxfail'):
            if self.verbosity <= 0:
                self._tw.line()
            self.print_summary(report)

    def print_summary(self, report):
        last_few_lines = tuple(report.longrepr.split('\n')[-4:])
        self.summary[last_few_lines].add(report)
        #sys.stderr.write("\x1b[2J\x1b[H")
        key_counts = list(
            (len(reports), key)
            for key, reports in self.summary.iteritems()
        )
        key_counts.sort(reverse=True)
        log_file = open('test_summary.log', 'w')
        log_file.seek(0)
        for count, key in key_counts:
            log_file.write('\n')
            log_file.write(str(count) + ':')
            for line in key:
                log_file.write(line)
                log_file.write('\n')
        # if self.config.option.tbstyle != "no":
        #     if self.config.option.tbstyle == "line":
        #         line = self._getcrashline(report)
        #         self.write_line(line)
        #     else:
        #         msg = self._getfailureheadline(report)
        #         if not hasattr(report, 'when'):
        #             msg = "ERROR collecting " + msg
        #         elif report.when == "setup":
        #             msg = "ERROR at setup of " + msg
        #         elif report.when == "teardown":
        #             msg = "ERROR at teardown of " + msg
        #         self.write_sep("_", msg)
        #         if not self.config.getvalue("usepdb"):
        #             self._outrep_summary(report)


