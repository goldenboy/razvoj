"""
This is a procedural interface to the matplotlib object-oriented
plotting library.

The following plotting commands are provided; the majority have
Matlab(TM) analogs and similar argument.

_Plotting commands
  acorr     - plot the autocorrelation function
  annotate  - annotate something in the figure
  arrow     - add an arrow to the axes
  axes      - Create a new axes
  axhline   - draw a horizontal line across axes
  axvline   - draw a vertical line across axes
  axhspan   - draw a horizontal bar across axes
  axvspan   - draw a vertical bar across axes
  axis      - Set or return the current axis limits
  bar       - make a bar chart
  barh      - a horizontal bar chart
  broken_barh - a set of horizontal bars with gaps
  box       - set the axes frame on/off state
  boxplot   - make a box and whisker plot
  cla       - clear current axes
  clabel    - label a contour plot
  clf       - clear a figure window
  clim      - adjust the color limits of the current image
  close     - close a figure window
  colorbar  - add a colorbar to the current figure
  cohere    - make a plot of coherence
  contour   - make a contour plot
  contourf  - make a filled contour plot
  csd       - make a plot of cross spectral density
  delaxes   - delete an axes from the current figure
  draw      - Force a redraw of the current figure
  errorbar  - make an errorbar graph
  figlegend - make legend on the figure rather than the axes
  figimage  - make a figure image
  figtext   - add text in figure coords
  figure   - create or change active figure
  fill     - make filled polygons
  gca      - return the current axes
  gcf      - return the current figure
  gci      - get the current image, or None
  getp      - get a handle graphics property
  grid     - set whether gridding is on
  hist     - make a histogram
  hold     - set the axes hold state
  ioff     - turn interaction mode off
  ion      - turn interaction mode on
  isinteractive - return True if interaction mode is on
  imread   - load image file into array
  imshow   - plot image data
  ishold   - return the hold state of the current axes
  legend   - make an axes legend
  loglog   - a log log plot
  matshow  - display a matrix in a new figure preserving aspect
  pcolor   - make a pseudocolor plot
  pcolormesh - make a pseudocolor plot using a quadrilateral mesh
  pie      - make a pie chart
  plot     - make a line plot
  plot_date - plot dates
  plotfile  - plot column data from an ASCII tab/space/comma delimited file
  pie      - pie charts
  polar    - make a polar plot on a PolarAxes
  psd      - make a plot of power spectral density
  quiver   - make a direction field (arrows) plot
  rc       - control the default params
  rgrids   - customize the radial grids and labels for polar
  savefig  - save the current figure
  scatter  - make a scatter plot
  setp      - set a handle graphics property
  semilogx - log x axis
  semilogy - log y axis
  show     - show the figures
  specgram - a spectrogram plot
  spy      - plot sparsity pattern using markers or image
  stem     - make a stem plot
  subplot  - make a subplot (numrows, numcols, axesnum)
  subplots_adjust - change the params controlling the subplot positions of current figure
  subplot_tool - launch the subplot configuration tool
  table    - add a table to the plot
  text     - add some text at location x,y to the current axes
  thetagrids - customize the radial theta grids and labels for polar
  title    - add a title to the current axes
  xcorr   - plot the autocorrelation function of x and y
  xlim     - set/get the xlimits
  ylim     - set/get the ylimits
  xticks   - set/get the xticks
  yticks   - set/get the yticks
  xlabel   - add an xlabel to the current axes
  ylabel   - add a ylabel to the current axes

  autumn - set the default colormap to autumn
  bone   - set the default colormap to bone
  cool   - set the default colormap to cool
  copper - set the default colormap to copper
  flag   - set the default colormap to flag
  gray   - set the default colormap to gray
  hot    - set the default colormap to hot
  hsv    - set the default colormap to hsv
  jet    - set the default colormap to jet
  pink   - set the default colormap to pink
  prism  - set the default colormap to prism
  spring - set the default colormap to spring
  summer - set the default colormap to summer
  winter - set the default colormap to winter
  spectral - set the default colormap to spectral

_Event handling

  connect - register an event handler
  disconnect - remove a connected event handler

_Matrix commands

  cumprod   - the cumulative product along a dimension
  cumsum    - the cumulative sum along a dimension
  detrend   - remove the mean or besdt fit line from an array
  diag      - the k-th diagonal of matrix
  diff      - the n-th differnce of an array
  eig       - the eigenvalues and eigen vectors of v
  eye       - a matrix where the k-th diagonal is ones, else zero
  find      - return the indices where a condition is nonzero
  fliplr    - flip the rows of a matrix up/down
  flipud    - flip the columns of a matrix left/right
  linspace  - a linear spaced vector of N values from min to max inclusive
  logspace  - a log spaced vector of N values from min to max inclusive
  meshgrid  - repeat x and y to make regular matrices
  ones      - an array of ones
  rand      - an array from the uniform distribution [0,1]
  randn     - an array from the normal distribution
  rot90     - rotate matrix k*90 degress counterclockwise
  squeeze   - squeeze an array removing any dimensions of length 1
  tri       - a triangular matrix
  tril      - a lower triangular matrix
  triu      - an upper triangular matrix
  vander    - the Vandermonde matrix of vector x
  svd       - singular value decomposition
  zeros     - a matrix of zeros

_Probability

  levypdf   - The levy probability density function from the char. func.
  normpdf   - The Gaussian probability density function
  rand      - random numbers from the uniform distribution
  randn     - random numbers from the normal distribution

_Statistics

  corrcoef  - correlation coefficient
  cov       - covariance matrix
  amax       - the maximum along dimension m
  mean      - the mean along dimension m
  median    - the median along dimension m
  amin       - the minimum along dimension m
  norm      - the norm of vector x
  prod      - the product along dimension m
  ptp       - the max-min along dimension m
  std       - the standard deviation along dimension m
  asum       - the sum along dimension m

_Time series analysis

  bartlett  - M-point Bartlett window
  blackman  - M-point Blackman window
  cohere    - the coherence using average periodiogram
  csd       - the cross spectral density using average periodiogram
  fft       - the fast Fourier transform of vector x
  hamming   - M-point Hamming window
  hanning   - M-point Hanning window
  hist      - compute the histogram of x
  kaiser    - M length Kaiser window
  psd       - the power spectral density using average periodiogram
  sinc      - the sinc function of array x

_Dates

  date2num  - convert python datetimes to numeric representation
  drange    - create an array of numbers for date plots
  num2date  - convert numeric type (float days since 0001) to datetime

_Other

  angle     - the angle of a complex array
  load     - load ASCII data into array
  polyfit   - fit x, y to an n-th order polynomial
  polyval   - evaluate an n-th order polynomial
  roots     - the roots of the polynomial coefficients in p
  save      - save an array to an ASCII file
  trapz     - trapezoidal integration

__end

"""
import sys, warnings

from cbook import flatten, is_string_like, exception_to_str, popd, \
     silent_list, iterable, enumerate, dedent

import numpy as npy
# The masked array namespace is brought in as ma; getting
# this from numerix allows one to select either numpy.ma or
# Pierre G-M's maskedarray implementation, which may
# replace the present numpy.ma implementation in a future
# numpy release.
from matplotlib.numerix import npyma as ma

from matplotlib import mpl  # pulls in most modules

# catch more than an import error here, since the src could fail too,
# eg a bad pytz install.  I don't want to break all of matplotlib for
# date support
try:
    from matplotlib.dates import date2num, num2date,\
            datestr2num, strpdate2num, drange,\
            epoch2num, num2epoch, mx2num,\
            DateFormatter, IndexDateFormatter, DateLocator,\
            RRuleLocator, YearLocator, MonthLocator, WeekdayLocator,\
            DayLocator, HourLocator, MinuteLocator, SecondLocator,\
            rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY,\
            WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY, relativedelta
except:
    __dates_all__ = []
    pass
else:
    import matplotlib.dates
    __dates_all__ = matplotlib.dates.__all__


# bring all the  symbols in so folks can import them from
# pylab in one fell swoop

from matplotlib.mlab import  window_hanning, window_none,\
        conv, detrend, detrend_mean, detrend_none, detrend_linear,\
        polyfit, polyval, entropy, normpdf,\
        levypdf, find, trapz, prepca, fix, rem, norm, orth, rank,\
        sqrtm, prctile, center_matrix, rk4, exp_safe, amap,\
        sum_flat, mean_flat, rms_flat, l1norm, l2norm, norm, frange,\
        diagonal_matrix, base_repr, binary_repr, log2, ispower2,\
        bivariate_normal, load, save, stineman_interp

from numpy import *
from numpy.fft import *
from numpy.random import *
from numpy.linalg import *

from matplotlib.mlab import window_hanning, window_none, conv, detrend, demean, \
     detrend_mean, detrend_none, detrend_linear, entropy, normpdf, levypdf, \
     find, longest_contiguous_ones, longest_ones, prepca, prctile, prctile_rank, \
     center_matrix, rk4, bivariate_normal, get_xyz_where, get_sparse_matrix, dist, \
     dist_point_to_segment, segments_intersect, fftsurr, liaupunov, movavg, \
     save, load, slopes, stineman_interp, inside_poly, poly_below, poly_between, exp_safe, \
     amap, rms_flat, l1norm, l2norm, norm_flat, frange, diagonal_matrix, identity, \
     base_repr, binary_repr, log2, ispower2, fromfunction_kw, rem, norm, orth, rank, sqrtm,\
     mfuncC, approx_real, rec_append_field, rec_drop_fields, rec_join, csv2rec, rec2csv


     

# old style--if True, override standard numpy with oldnumeric
if False:
    from numpy.oldnumeric import array, zeros, shape, rank, size, fromstring,\
            take, put, putmask, reshape, repeat, choose, searchsorted,\
            cumsum, product, cumproduct, alltrue, sometrue, allclose,\
            arrayrange, arange, asarray, convolve, swapaxes, concatenate,\
            transpose, sort, argsort, argmax, argmin, innerproduct, dot,\
            outerproduct, resize, indices, fromfunction, diagonal, trace,\
            ravel, nonzero, shape, where, compress, clip, zeros, ones,\
            identity, add, logical_or, exp, subtract, logical_xor,\
            log, multiply, logical_not, log10, divide, maximum, sin,\
            minimum, sinh, conjugate, bitwise_and, sqrt, power, bitwise_or,\
            tan, absolute, bitwise_xor, tanh, negative, ceil, greater, fabs,\
            greater_equal, floor, less, arccos, arctan2, less_equal, arcsin,\
            fmod, equal, arctan, hypot, not_equal, cos, around, logical_and,\
            cosh, arccosh, arcsinh, arctanh, cross_correlate,\
            pi, ArrayType, matrixmultiply

    from numpy.oldnumeric import sum as asum

    from numpy.oldnumeric import Int8, UInt8, Int16, UInt16, Int32, UInt32, Float32,\
            Float64, Complex32, Complex64, Float, Int, Complex

    pymin, pymax = min, max
    from numpy.oldnumeric.mlab import *
    min, max = pymin, pymax
    from numpy import amin, amax
    from numpy.oldnumeric.linear_algebra import eigenvectors
            # not quite the same as linalg.eig
    from numpy.linalg import inv as inverse


from matplotlib.pyplot import *



