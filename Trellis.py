import sys
import os
import datetime
import pandas
import matplotlib.pyplot
import matplotlib.image
import scipy.interpolate
import numpy


class Trellis:

    """
    visualizes an array of n-D points, specifically those resulting from tuning the parameters of
    the kernel tuner, as a trellis
    """

    def __init__(self, filename,
                 axes_face_color=None,
                 axes_padding=None,
                 cmap='bwr',
                 interp_method_image='nearest',
                 marker='o',
                 marker_size=5 ** 2,
                 nbins_image=100,
                 objective='time',
                 parameter_names=None,
                 show_diagonal=False,
                 show_image=True,
                 show_scatter=True,
                 verbose=False,
                 vmax=None,
                 vmin=None):

        # tie parameters to the instance:
        if axes_face_color is None:
            self._axes_face_color = [0.9, 0.9, 0.9]
        else:
            self._axes_face_color = axes_face_color

        if axes_padding is None:
            self._axes_padding = {
                'left': 0.05,
                'bottom': 0.05,
                'right': 0.05,
                'top': 0.05
            }
        else:
            self._axes_padding = axes_padding

        self._cmap = cmap
        self._interp_method_image = interp_method_image
        self._marker = marker
        self._marker_size = marker_size
        self._nbins_image = nbins_image
        self._objective = objective
        self._parameter_names = None
        self._show_diagonal = show_diagonal
        self._show_image = show_image
        self._show_scatter = show_scatter
        self._verbose = verbose
        self._vmax = vmax
        self._vmin = vmin

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # initialize the array that will hold the axes data from which the trellis is constructed
        self._axesdata = []

        # dataframe that will hold the n-by-m array with parameter combinations
        self._df = None

        self._npars = None

        # load the json data into a pandas dataframe
        self.load_results(filename)

        # construct a sorted list of parameter names (excluding the objective score)
        self.determine_parameter_names(parameter_names)

        # collect the data relevant for each axes
        self.calculate_axes_data()

        # now that we have all the axesdata, determine the global color limits
        self.determine_color_limits(vmin=vmin, vmax=vmax)

    def calculate_axes_data(self):

        left = 0.1
        bottom = 0.1
        width = 0.80
        height = 0.80

        for parameter_name_x in self._parameter_names:
            for parameter_name_y in self._parameter_names:

                ihorizontal = self._parameter_names.index(parameter_name_x)
                ivertical = self._parameter_names.index(parameter_name_y)

                # only collect data for visualizing scatter plots in the lower triangle of the figure
                if ivertical >= ihorizontal:
                    continue

                npars = self._npars
                pad = self._axes_padding

                if self._show_diagonal:
                    position = {
                        'left': left + width * (ihorizontal + pad['left']) / (npars),
                        'bottom': bottom + height * (ivertical + pad['bottom']) / (npars),
                        'width': (1 - pad['left'] - pad['right']) * (width / (npars)),
                        'height': (1 - pad['bottom'] - pad['top']) * (height / (npars))
                    }
                else:
                    position = {
                        'left': left + width * (ihorizontal - 1 + pad['left']) / (npars - 1),
                        'bottom': bottom + height * (ivertical + pad['bottom']) / (npars - 1),
                        'width': (1 - pad['left'] - pad['right']) * (width / (npars - 1)),
                        'height': (1 - pad['bottom'] - pad['top']) * (height / (npars - 1))
                    }


                dedupl = self.identify_list_of_unique_points_per_axes(parameter_name_x, parameter_name_y)

                minimum_series = self.find_minimum_per_axes(parameter_name_x, parameter_name_y, dedupl)

                if self._show_image:
                    minimum_interpolated = self.interpolate_two_dimensional_mimimums(dedupl[parameter_name_x],
                                                                                     dedupl[parameter_name_y],
                                                                                     minimum_series)
                else:
                    minimum_interpolated = None

                axesdata = {
                    'ax': None,
                    'bottom': position['bottom'],
                    'height': position['height'],
                    'horizontal': parameter_name_x,
                    'ihorizontal': ihorizontal,
                    'image-data': {
                        'xmin': dedupl[parameter_name_x].min(),
                        'xmax': dedupl[parameter_name_x].max(),
                        'ymin': dedupl[parameter_name_y].min(),
                        'ymax': dedupl[parameter_name_y].max(),
                        'v': minimum_interpolated
                    },
                    'ivertical': ivertical,
                    'left': position['left'],
                    'scatter-data': {
                        'x': dedupl[parameter_name_x],
                        'y': dedupl[parameter_name_y],
                        'v': minimum_series
                    },
                    'vertical': parameter_name_y,
                    'width': position['width']
                }

                self._axesdata.append(axesdata)

        self.provide_user_feedback("Calculated the per-axes data.")

    def determine_color_limits(self, vmin, vmax):

        calcvmin = vmin is None
        calcvmax = vmax is None

        for axesdata in self._axesdata:

            if calcvmin:
                vmin = axesdata.get('scatter-data').get('v').min()
                if self._vmin is None:
                    self._vmin = vmin
                elif vmin < self._vmin:
                    self._vmin = vmin

            if calcvmax:
                vmax = axesdata.get('scatter-data').get('v').max()
                if self._vmax is None:
                    self._vmax = vmax
                elif vmax > self._vmax:
                    self._vmax = vmax

        if not self._vmin <= self._vmax:
            raise Exception("vmin should be lower than or equal to vmax but isn't")

        if calcvmin:
            self.provide_user_feedback("Identified the lower color limit \"vmin\" as " +
                                       str(self._vmin) + ".")
        else:
            self.provide_user_feedback("The lower color limit \"vmin\" was defined as " +
                                       str(self._vmin) + ".")

        if calcvmax:
            self.provide_user_feedback("Identified the upper color limit \"vmax\" as " +
                                       str(self._vmax) + ".")

        else:
            self.provide_user_feedback("The upper color limit \"vmax\" was defined as " +
                                       str(self._vmax) + ".")

    def determine_parameter_names(self, parameter_names):

        parameter_names_from_data = sorted([column for column in self._df.columns.values if column != self._objective])
        if parameter_names is not None and len(parameter_names) == 1:
            raise Exception("There should be at least 2 parameters to compare.")

        if parameter_names is None:
            self._parameter_names = parameter_names_from_data
            self.provide_user_feedback("Identified the list of parameters present in the data.")
        else:
            for parameter_name in parameter_names:
                if parameter_name not in parameter_names_from_data:
                    raise Exception("\"" + parameter_name + "\" does not occur as a parameter in the data.")
            self._parameter_names = parameter_names

        self._npars = len(self._parameter_names)

    def draw(self):

        for axesdata in self._axesdata:

            axes_position = [axesdata.get('left'),
                             axesdata.get('bottom'),
                             axesdata.get('width'),
                             axesdata.get('height')]

            ax = matplotlib.pyplot.axes(axes_position, facecolor=self._axes_face_color)

            if self._show_image:
                self.draw_image(ax, axesdata)

            if self._show_scatter:
                self.draw_scatter_plot(ax, axesdata)

            self.draw_ticks_and_labels(ax, axesdata)

        # force drawing the figure now
        matplotlib.pyplot.show()

        self.provide_user_feedback("Finished drawing trellis.")

    def draw_image(self, ax, axesdata):
        extent = [axesdata['image-data']['xmin'],
                  axesdata['image-data']['xmax'],
                  axesdata['image-data']['ymin'],
                  axesdata['image-data']['ymax']]
        ax.matshow(axesdata['image-data']['v'], extent=extent, aspect='auto',
                   cmap=self._cmap, vmin=self._vmin, vmax=self._vmax)
        ax.autoscale(False)

    def draw_scatter_plot(self, ax, axesdata):

        x = axesdata['scatter-data']['x']
        y = axesdata['scatter-data']['y']
        c = axesdata['scatter-data']['v']

        ax.scatter(x, y, c=c,
                   cmap=self._cmap,
                   vmin=self._vmin,
                   vmax=self._vmax,
                   marker=self._marker,
                   s=self._marker_size,
                   edgecolors='k')

    def draw_ticks_and_labels(self, ax, axesdata):

        matplotlib.pyplot.tick_params(axis='both', which='both', bottom='off', left='off',
                                      top='off', right='off', labelleft='off', labelright='off',
                                      labeltop='off', labelbottom='off')

        if axesdata['ivertical'] == 0:
            matplotlib.pyplot.tick_params(axis='x', which='both', bottom='on', labelbottom='on')
            matplotlib.pyplot.xlabel(axesdata['horizontal'])

        if axesdata['ivertical'] == axesdata['ihorizontal'] - 1:
            matplotlib.pyplot.tick_params(axis='x', which='both', top='on', labeltop='on')

        if axesdata['ihorizontal'] == self._npars - 1:
            matplotlib.pyplot.tick_params(axis='y', which='both', right='on', labelright='on')
            matplotlib.pyplot.ylabel(axesdata['vertical'])
            ax.yaxis.set_label_position('right')

    def find_minimum_per_axes(self, parameter_name_x, parameter_name_y, dedupl):

        # initialize an empty series the same size as dedupl, using the same index
        minimum_series = pandas.Series(data=None, name='per_axes_min', index=dedupl.index)

        if parameter_name_x is parameter_name_y:
            return pandas.DataFrame({'per_axes_min': []})
        else:
            for index, deduplRow in dedupl.iterrows():
                cond1 = self._df[parameter_name_x] == deduplRow[parameter_name_x]
                cond2 = self._df[parameter_name_y] == deduplRow[parameter_name_y]
                per_axes_min = self._df.loc[cond1 & cond2, self._objective].min()
                minimum_series[index] = per_axes_min
            return minimum_series

    def identify_list_of_unique_points_per_axes(self, parameter_name_x, parameter_name_y):

        if parameter_name_x is parameter_name_y:
            return pandas.DataFrame({parameter_name_x: []})
        else:
            dedupl = self._df.loc[:, [parameter_name_x, parameter_name_y]]
            dedupl.drop_duplicates(inplace=True)
            return dedupl

    def interpolate_two_dimensional_mimimums(self, x, y, z):

        points = pandas.concat([x, y], axis=1)

        pointsi = []
        for xi in numpy.linspace(x.min(), x.max(), self._nbins_image):
            for yi in numpy.linspace(y.max(), y.min(), self._nbins_image):
                pointsi.append([xi, yi])

        zi = scipy.interpolate.griddata(points.as_matrix(),
                                        z.values,
                                        pointsi,
                                        method=self._interp_method_image,
                                        fill_value=numpy.nan)

        return zi.reshape(self._nbins_image, self._nbins_image, order='F')

    def load_results(self, filename):
        if os.path.exists(filename) and os.access(filename, os.R_OK):
            # read the json file, return a Pandas dataframe with the json content
            self._df = pandas.read_json(filename, orient='columns', typ='frame')
            self.provide_user_feedback("Loaded the data from \"" + filename + "\".")
        else:
            raise Exception("File \"" + filename + "\" does not exist or is not readable.")

        assert self._objective in self._df.columns.values
        self.provide_user_feedback("Using objective \"" + self._objective + "\".")

    def provide_user_feedback(self, message_text):
        if self._verbose:
            print(datetime.datetime.now().strftime('%H:%M:%S') + " " + message_text)


if __name__ == '__main__':

    if len(sys.argv) == 2:
        jsonfile = sys.argv[1]
        trellis = Trellis(jsonfile, verbose=True, show_diagonal=True, show_image=False)
        fig = matplotlib.pyplot.figure(facecolor=[0.8, 0.8, 0.8])
        trellis.draw()
