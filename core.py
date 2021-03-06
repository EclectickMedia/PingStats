import time
import socket
import datetime as dt
import csv
import os

from pythonping import ping as pyping

from log import core_logger as logger

# GLOBALS
buildname = "PingStats"
version = "2.4.1"
versiondate = "Fri Jun  2 06:35:35 2017"
versionstr = "PingStats Version %s (C) Ariana Giroux, Eclectick Media " \
             "Solutions. circa %s" % (
                 version, versiondate)


def validate_string(text):
    """ Checks `text` for illegal characters. Returns True on validation. """
    invalid_characters = ['*', '\x00', '\x80']
    for character in invalid_characters:
        if character == '*':
            if text.startswith(character):
                logger.warning('Bad character: %s' % character)
                return False
        elif text.count(character):
            logger.warning('Bad character: %s' % character)
            return False

    return True


def buildfile(path, name):
    """ Opens a CSV file at specified `path` + `name` + '.csv'.

    Returns an open TextIOWrapper. """

    if not validate_string(path):
        raise ValueError('Illegal path!')

    if not validate_string(name):
        raise ValueError('Illegal file name!')

    name += '.csv'

    try:
        return open(os.path.join(path, name), 'a+')
    except OSError:
        print('Failed to open \'%s\', defaulting to \'%sLog.csv\'.' % (
            (path + name), buildname))
        return open('%sLog.csv' % buildname, 'a+')


def write_csv_data(writer, data):
    """ Writes a row of CSV data and returns the data that was read. """
    if data is None:  # TODO Should None data be handled by super?
        return data
    else:
        logger.debug(data)
        writer.writerow(data)
        return data


def ping(address, timeout=3000, size=64, verbose=True, delay=0.22):
    """ A generator that repeatedly calls `python-ping.single_ping`, and
    yields the results.

    All kwargs are passed to the underlying call to `python-ping`, aside
    from `delay` which specifies the length of time to wait before the
    next call to `python-ping` is performed.

    Returns None if it is waiting for time to occur. """

    host_name = socket.gethostname()

    i = 1
    last_ping = time.time() - delay
    while 1:
        if (time.time() - last_ping) > delay:
            try:
                yield (time.time(),
                       pyping.single_ping(address, host_name, timeout, i,
                       size, verbose=verbose)[0],
                       timeout, size, address)

            except TypeError:
                yield (dt.datetime.fromtimestamp(time.time()),
                       -100.00, timeout, size, address)

            i += 1
            last_ping = time.time()
        else:
            yield


class Core:
    """ Provides core functionality for `PingStats`. """

    def write_csv(self, data):
        """ Provides a wrapper to `core.write_csv_data`. """
        write_csv_data(self.cwriter, data)

    def __init__(self, address, file_path=None, file_name=None, nofile=False,
                 quiet=False, delay=0.22, timeout=3000, *args, **kwargs):
        """ Constructs a `Core` object.

        Instantiates a `ping` generator at `self.ping_generator`, and an
        open CSV writer at `self.cwriter`"""

        logger.debug((address, file_path, file_name, nofile, quiet, delay,
                      timeout, args, kwargs))

        self.quiet = not quiet  # flip bool
        self.delay = delay
        # core.Core.ping
        if address is None:
            raise RuntimeError('core.Core requires address')
        self.address = address
        self.ping_generator = ping(self.address, timeout=timeout,
                                   verbose=not self.quiet, delay=self.delay)

        # core.Core.build files
        self.file_path = file_path  # validated in self.build file
        self.file_name = file_name  # validated in self.build file
        self.nofile = nofile
        if not self.nofile:
            self.built_file = buildfile(self.file_path, self.file_name)
            logger.info('Log file at %s' % self.built_file.name)
            self.cwriter = csv.writer(self.built_file)

    def yield_generator(self):
        return self.ping_generator


if __name__ == '__main__':
    raise DeprecationWarning('Direct execution of PingStats has been '
                             'deprecated, please use main.py')
