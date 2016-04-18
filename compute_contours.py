#!/usr/bin/python

# This script computes the grid for contours of a function
# reconstruction plot.
#
# If one has
#  * independent variable x
#  * dependent variable y
#  * functional form y = f(x,theta) parameterised by theta
#
# This script assumes a linear spline, with theta being interpolation
# knots, but the file fgivenx/samples.py can easily be modified
#
# Assuming that you have obtained samples of theta from an MCMC
# process, we aim to compute:
#
#               /
# P( y | x ) =  | P( y = f(x,theta) | x, theta ) dtheta ,  (1)
#               /
#
# which gives our degree of knowledge for each y value given an x value.
#
# In fact, for a more representative plot, we are not actually
# interested in the value of the probability density (1), but in fact
# require the "iso-probablity posterior mass:"
#
#                     /
# m( y | x ) =        | P(y'|x) dy'
#                     /
#             P(y'|x) < P(y|x)
#
# We thus need to compute this function on a rectangular grid of x and y's
#
# Once this is done, you should then use the plot_fgivenx.py script
#
# If you encounter an error, the first thing to check should be the
# limits: xmin,xmax,ymin,ymax
#
# Any questions, please email Will Handley <wh260@mrao.cam.ac.uk>

import numpy
from fgivenx.read_data import save_contours
from fgivenx.sample import trim_samples
from fgivenx.contours import Contours

from fgivenx.data_storage import FunctionalPosterior
import sys

# Settings
# --------
xmin = 4                       # minimum of x range
xmax = 12                      # maximum of x range
nsamp = 500                    # number of samples to use


# Load posteriors 
chains_file = 'chains/mps10_detec_nliv200_ident_sub.txt'
paramnames_file = 'chains/mps10_detec_nliv200_ident_sub.paramnames'
posterior = FunctionalPosterior(chains_file,paramnames_file)

#posterior.trim_samples(nsamp)
posterior.trim_samples(nsamp)

#self.f = interp1d(xdat,ydat,bounds_error=False,fill_value=0)

# Define the function
def logspectrum(logE, params):
    """ Spectrum with logE0 and logEc fixed """
    logE0 = numpy.log(4016.0)
    logEc = float('inf')
    logN0, alpha, beta = params

    logdNdE = logN0
    logdNdE -= (logE - logE0) * (alpha + beta*(logE - logE0) )
    logdNdE -= numpy.exp(logE-logEc) - numpy.exp(logE0 - logEc)

    return logdNdE

function = logspectrum
choices = [['log_N0_' + str(i), 'alpha_PS_' + str(i), 'beta_PS_' + str(i)] for i in range(1,11)]


# Compute a grid for making a contour plot
for i, chosen_parameters in enumerate(choices):
    print chosen_parameters
    posterior.set_function(function, chosen_parameters)
    contours = Contours(posterior,[xmin, xmax],progress_bar=True)
    filename = 'contours/posterior' + str(i) + '.pkl'
    contours.save(filename)



