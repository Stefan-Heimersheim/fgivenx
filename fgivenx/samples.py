import numpy
import tqdm
from fgivenx.parallel import parallel_apply
from fgivenx.io import CacheError, Cache


def trim_samples(samples, weights, ntrim=-1):
    """ Make samples equally weighted, and trim if desired.

    Parameters
    ----------
    samples: numpy.array
        See argument of fgivenx.compute_contours for more detail.

    weights: numpy.array
        See argument of fgivenx.compute_contours for more detail.

    ntrim: int (optional)
    Returns
    -------

    """

    state = numpy.random.get_state()

    numpy.random.seed(1)
    n = len(weights)
    choices = numpy.random.rand(n) < weights

    new_samples = samples[choices]

    numpy.random.set_state(state)

    return new_samples.copy()


def compute_samples(f, x, samples, **kwargs):
    """ Apply f(x,theta) to x array and theta in samples.

    Parameters
    ----------
    See arguments of fgivenx.compute_contours

    Keywords
    --------
    parallel: str
        See arguments of fgivenx.compute_contours

    Returns
    -------
    An array of samples at each x. shape=(len(x),len(samples),)
    """

    parallel = kwargs.pop('parallel', False)
    cache = kwargs.pop('cache', None)
    if kwargs:
        raise TypeError('Unexpected **kwargs: %r' % kwargs)

    if cache is not None:
        cache = Cache(cache + '_fsamples')
        try:
            return cache.check(x, samples)  
        except CacheError as e:
            print(e.msg())

    fsamples = []
    for fi, s in zip(f, samples):
        if len(s) > 0:
            fsamps = parallel_apply(fi, s, precurry=(x,), parallel=parallel)
            fsamps = numpy.array(fsamps).transpose().copy()
            fsamples.append(fsamps)
    fsamples = numpy.concatenate(fsamples,axis=1)

    if cache is not None:
        cache.save(x, samples, fsamples)

    return fsamples


def samples_from_getdist_chains(params,file_root=None,chains_file=None,paramnames_file=None,latex=False):
    """ Extract samples and weights from getdist chains.

    Parameters
    ----------
    params: list(str)
        Names of parameters to be supplied to second argument of f(x|theta).

    file_root: str
        Root name for getdist chains files. This script requires
        - file_root.txt
        - file_root.paramnames

    Keywords
    --------

    Returns
    -------
    samples: numpy.array
        2D Array of samples. samples.shape=(# of samples, len(params),)

    weights: numpy.array
        Array of weights. samples.shape = (len(params),)
    """

    # Get the full data
    if file_root is not None:
        chains_file = file_root + '.txt'
        paramnames_file = file_root + '.paramnames' 

    data = numpy.loadtxt(chains_file)
    if len(data) is 0:
        return numpy.array([[]]), numpy.array([])
    if len(data.shape) is 1:
        data = data.reshape((1,) + data.shape)
    weights = data[:, 0]

    # Get the paramnames
    paramnames = [line.split()[0].replace('*','') for line in open(paramnames_file,'r')]

    # Get the relevant samples
    indices = [2+paramnames.index(p) for p in params]
    samples = data[:, indices]

    if latex:
        latex = [' '.join(line.split()[1:])  for line in open(paramnames_file,'r')]
        latex = [latex[i-2] for i in indices]
        return samples, weights, latex
    else:
        return samples, weights
