import sys
import csv
import datetime as dt
import os
from warnings import warn

import core as c

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib import style
except OSError as e:
    raise RuntimeError('Could not load matplotlib!').with_traceback()


class _PlotTable:
        """ A class to maintain a specified number of objects to plot to
        matplotlib.

        Manages two lists:
            self.x (takes `datetime.datetime` objects)
            self.y (takes any `float` data type)
        """

        def __init__(self, length=None):
            """ Creates `self.x` and `self.y`, and validates a table `length`.

            Length must be `int` or None. """

            self.x = []
            self.y = []

            if length is not None and type(length) is not int:
                raise TypeError('length must be int or None')

            if length is None:
                self.length = 250
            elif length <= 0:
                raise ValueError('Requires a table length of at least 1')
            else:
                self.length = int(length)

        def appendx(self, a):
            """ Append a new value to the x value of the table. Maintains
            specified length of table upon reaching max.

            "a" - A `datetime.datetime` object.
            """

            if type(a) is not dt.datetime:
                raise TypeError('Requires a datetime.datetime object')

            if len(self.x) < self.length:
                self.x.append(a)
            else:
                self.x.pop(0)
                self.x.append(a)

        def appendy(self, a):
            """ Append a new value to the y value of the table. Maintains
            specified length of table upon reaching max.

            "a" - Any float.
            """

            if type(a) is not float:
                raise TypeError('PlotTable.appendy requires float type data.')

            if len(self.y) < self.length:
                self.y.append(a)
            else:
                self.y.pop(0)
                self.y.append(a)

        def getx(self):  # arbitrary get method
            return self.x

        def gety(self):  # arbitrary get method
            return self.y


class _Plot:
    """ Base class for `Animate` and `PlotFile`, maintains several matplotlib
    properties. """

    fig = plt.figure()

    title_str = ''
    for arg in sys.argv:
        if sys.argv.index(arg) is 0:
            pass
        else:
            title_str += ' ' + arg

    ax1 = plt.axes()

    ptable = _PlotTable()

    def __init__(self, *args, **kwargs):
        """ Validates `self.title_str` and rotates plot labels. """
        super(_Plot, self).__init__(*args, **kwargs)

        # table_length validation
        try:
            table_length = kwargs['table_length']
        except KeyError:
            table_length = None
        if table_length is not None and type(table_length) is not int:
            raise TypeError('table_length is not None or int')
        if table_length is not None:
            self.ptable.length = table_length

        # title_str validation
        if type(self.title_str) is not str:
            raise TypeError('Plot title_str requires a string object')
        if self.title_str.count('\x00'):
            raise(ValueError('Title String must not have null bytes'))

        self.fig.canvas.set_window_title('%s | %s' % (c.buildname,
                                                      self.title_str))
        # style.use('ggplot')
        style.use('seaborn-darkgrid')

        plt.subplots_adjust(left=0.13, bottom=0.33, right=0.95, top=0.89)
        for label in self.ax1.xaxis.get_ticklabels():
            label.set_rotation(45)

    def show_plot(self):
        """ Executes `matplotlib.pyplot.show` """
        return plt.show()


class Animate(_Plot, c.Core):
    """ Handles live plot generation. """
    def _animate(self, i, ptable):
        """ Calls the next iteration of `c.Core.ping_generator`, and yields
        data to the plot.

        "i" - Required by matplotlib.animation.FuncAnimation
        Returns None.
        """
        self.ax1.clear()

        plt.xlabel('Timestamps')
        plt.ylabel('Return Time (in milliseconds)')
        plt.title('Ping Over Time')

        # DRAW POINTS
        self.ax1.plot_date(ptable.getx(), ptable.gety(), 'r-')
        for label in self.ax1.xaxis.get_ticklabels():
            label.set_rotation(45)

        next(self.get_pings(self.ping_generator))

    def animate(self):
        """ A naming semantics wrapper for `_Plot.show_plot`. """
        return self.show_plot()

    def get_pings(self, obj):
        """ Checks for None or appends to `self._PlotTable` """
        for val in obj:
            if val is None:
                yield
            else:
                self.ptable.appendx(dt.datetime.fromtimestamp(val[0]))

                if val[1] is None:
                    self.ptable.appendy(-100.0)
                else:
                    self.ptable.appendy(val[1])

                if not self.nofile:
                    self.write_csv(val)

                yield

    def __init__(self, *args, **kwargs):
        """ Validates kwargs, and generates a _PlotTable object. """
        super(Animate, self).__init__(*args, **kwargs)

        # refresh_freq validation
        try:
            refresh_freq = kwargs['refresh_freq']
        except KeyError:
            refresh_freq = None

        if refresh_freq is not None and type(refresh_freq) is not int:
            raise TypeError('refresh_freq is not None or int')

        if refresh_freq is None:
            self.ani = animation.FuncAnimation(self.fig, self._animate,
                                               fargs=(
                                                   self.ptable,))

        else:
            self.ani = animation.FuncAnimation(self.fig, self._animate,
                                               interval=refresh_freq, fargs=(
                                                    self.ptable,))


class PlotFile(_Plot):
    @staticmethod
    def generate_reader(csv_path):
        """ Yields a `csv.reader` object built from `csv_path`. """
        if not os.access(csv_path, os.F_OK):
            raise RuntimeError('Cannot access %s!' % csv_path)

        return csv.reader(open(csv_path))

    @staticmethod
    def generate_datetime(timestamp):
        """ Yields a `datetime.datetime` object. """
        warn('generate_datetime is deprecated in V2.4', DeprecationWarning)
        if type(timestamp) is not float:
            raise TypeError('timestamp must be float')

        return dt.datetime.fromtimestamp(timestamp)

    @staticmethod
    def yield_points(reader):
        """ Yields an x and y coordinate for each row in `reader` """
        for row in reader:
            x = dt.datetime.fromtimestamp(float(row[0]))

            if row[1] == '':  # none
                y = -100.0

            else:
                try:
                    y = float(row[1])
                except ValueError as e:
                    raise e('Could not handle second data point in row %s' %
                            row)

            yield x, y

    def __init__(self, csv_file, image_path=None, *args, **kwargs):
        super(PlotFile, self).__init__(*args, **kwargs)

        self.image_path = image_path

        self.creader = self.generate_reader(csv_file)

        self.points_generator = self.yield_points(self.creader)

        self.x = []
        self.y = []

        for a, b in self.points_generator:
            self.x.append(a)
            self.y.append(b)

        self.ax1.plot_date(self.x, self.y, 'r-')

        plt.xlabel('Timestamps')
        plt.ylabel('Return Time (in milliseconds)')
        plt.title('Ping Over Time')

    def show_plot(self):
        if self.image_path is not None:
            plt.savefig(self.image_path)
        else:
            super(PlotFile, self).show_plot()
