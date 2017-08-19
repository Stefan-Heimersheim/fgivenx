import tqdm
import os
import numpy
from joblib import Parallel, delayed
from mpi4py import MPI


def openmp_apply(f, array, nprocs=None, **kwargs):
    """ Apply a function to an array with openmp parallelisation.

    Equivalent to [f(x) for x in array], but parallelised. Will parallelise
    using the environment variable OMP_NUM_THREADS, unless nprocs is provided.

    Parameters
    ----------
    f: function
        Univariate function to apply to each element of array

    array: array-like
        Array to apply f to

    Keywords
    --------
    nprocs: int
        Force to parallelise with nprocs.

    precurry: tuple
        arguments to pass to f before 

    postcurry: tuple
        arguments to pass to f after 
    """

    precurry = kwargs.pop('precurry',())
    postcurry = kwargs.pop('postcurry',())

    if nprocs is None:
        if not os.environ['OMP_NUM_THREADS']:
            raise EnvironmentError(
                    "You have requested to use openmp, but the environment"
                    "variable OMP_NUM_THREADS is not set"
                    )
        if os.environ['OMP_NUM_THREADS'] is 1:
            print("Warning: You have requested to use openmp, but environment"
                  "variable OMP_NUM_THREADS=1")

        nprocs = int(os.environ['OMP_NUM_THREADS'])

    return Parallel(n_jobs=nprocs)(
                                   delayed(f)(*precurry,x,*postcurry) for x in tqdm.tqdm(array)
                                  )


def mpi_apply(function, array, **kwargs):
    """ Distribute a function applied to an array across an MPI communicator

    Parameters
    ----------
    function:
        function maps x -> y where x and y are numpy ND arrays, and the
        dimensionality of x is determined by xdims
    array:
        ndarray to apply function to

    Keywords
    comm:
        MPI communicator. If not supplied, one will be created
    """

    comm = kwargs.pop('comm', MPI.COMM_WORLD)
    rank = comm.Get_rank()

    array_local = mpi_scatter_array(array, comm)
    if rank is 0:
        answer_local = numpy.array([function(x)
                                    for x in tqdm.tqdm(array_local)])
    else:
        answer_local = numpy.array([function(x)
                                    for x in array_local])

    return mpi_gather_array(answer_local, comm)


def mpi_scatter_array(array, comm):
    """ Scatters an array across all processes across the first axis"""
    rank = comm.Get_rank()

    if rank is 0:
        array = array.astype('d').copy()
        n = len(array)
        nprocs = comm.Get_size()

        sendcounts = numpy.array([n//nprocs]*nprocs)
        sendcounts[:n-sum(sendcounts)] += 1

        displacements = numpy.insert(numpy.cumsum(sendcounts)[:-1], 0, 0)

        shape = array.shape
    else:
        sendcounts = displacements = shape = None

    shape = comm.bcast(shape)
    sendcount = comm.scatter(sendcounts)
    array_local = numpy.zeros((sendcount,) + shape[1:])

    if rank is 0:
        sendcounts *= numpy.prod(shape[1:])
        displacements *= numpy.prod(shape[1:])

    comm.Scatterv([array, sendcounts, displacements, MPI.DOUBLE], array_local)
    return array_local


def mpi_gather_array(array_local, comm):
    """ Gathers an array from all processes"""
    rank = comm.Get_rank()
    sendcounts = numpy.array(comm.gather(len(array_local)))
    shape = array_local.shape

    if rank is 0:
        displacements = numpy.insert(numpy.cumsum(sendcounts)[:-1], 0, 0)
        array = numpy.zeros((numpy.sum(sendcounts),) + shape[1:])
        sendcounts *= numpy.prod(shape[1:])
        displacements *= numpy.prod(shape[1:])
    else:
        displacements = array = None

    comm.Gatherv(array_local, [array, sendcounts, displacements, MPI.DOUBLE])
    return array