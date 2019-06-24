#!/usr/bin/env python
from sifting_convolution import SiftingConvolution
import sys
import os
import numpy as np
from argparse import ArgumentParser
import scipy.io as sio
from fractions import Fraction
from dataclasses import asdict, dataclass
sys.path.append(os.path.join(os.environ['SSHT'], 'src', 'python'))
import pyssht as ssht


@dataclass
class Config:
    L: int = 128
    sampling: str = 'MW'
    ncpu: int = 1
    auto_open: bool = True
    save_fig: bool = False

global __location__
__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


def get_angle_num_dem(angle_fraction):
    angle = Fraction(angle_fraction).limit_denominator()
    return angle.numerator, angle.denominator


def filename_std_dev(angle, arg_name):
    filename = '_'
    num, dem = get_angle_num_dem(angle)
    filename += f'{num}{arg_name}'
    if angle < 1:
        filename += f'{dem}'
    return filename


def read_args(spherical_harmonic=False):
    parser = ArgumentParser(description='Create SSHT plot')
    parser.add_argument(
        'flm', type=valid_plotting, choices=list(total.keys()), help='flm to plot on the sphere')
    parser.add_argument(
        '--type', '-t', type=str, nargs='?', default='abs', const='abs',
        choices=['abs', 'real', 'imag', 'sum'], help='plotting type: defaults to abs')
    parser.add_argument(
        '--routine', '-r', type=str, nargs='?', default='north', const='north',
        choices=['north', 'rotate', 'translate'], help='plotting routine: defaults to north')
    parser.add_argument(
        '--extra_args', '-e', type=int, nargs='+', help='list of extra args for functions')
    parser.add_argument(
        '--alpha', '-a', type=float, default=0.75, help='alpha/phi pi fraction - defaults to 0')
    parser.add_argument(
        '--beta', '-b', type=float, default=0.25, help='beta/theta pi fraction - defaults to 0')
    parser.add_argument(
        '--gamma', '-g', type=float, default=0, help='gamma pi fraction - defaults to 0 - rotation only')
    parser.add_argument(
        '--convolve', '-c', type=valid_kernels, choices=list(functions.keys()), help='glm to perform sifting convolution with i.e. flm x glm*')
    parser.add_argument(
        '--annotation', '-n', action='store_false', help='flag which if passed removes any annotation')

    # extra args for spherical harmonics
    if spherical_harmonic:
        parser.add_argument('-l', metavar='ell', type=int, help='multipole')
        parser.add_argument('-m', metavar='m', type=int,
                            help='multipole moment')

    args = parser.parse_args()
    return args


def identity():
    # filename
    func_name = 'identity'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=False
    )
    config = {**config, **extra}
    L = config['L']

    # create identity
    flm = np.ones((L * L)) + 1j * np.zeros((L * L))

    return flm, func_name, config


def dirac_delta():
    # filename
    func_name = 'dirac_delta'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']

    # create flm
    flm = np.zeros((L * L), dtype=complex)
    for ell in range(L):
        ind = ssht.elm2ind(ell, m=0)
        flm[ind] = np.sqrt((2 * ell + 1) / (4 * np.pi))

    return flm, func_name, config


def gaussian(args=[3]):
    # args
    try:
        sig = 10 ** args[0]
    except ValueError:
        print('function requires one extra arg')
        raise

    # filename
    func_name = f'gaussian{filename_std_dev(sig, "sig")}'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']

    # create flm
    flm = np.zeros((L * L), dtype=complex)
    for ell in range(L):
        ind = ssht.elm2ind(ell, m=0)
        flm[ind] = np.exp(-ell * (ell + 1) / (2 * sig * sig))

    return flm, func_name, config


def squashed_gaussian(args=[-2, -1]):
    # args
    try:
        t_sig, freq = [10 ** x for x in args]
    except ValueError:
        print('function requires two extra args')
        raise

    # filename
    func_name = (f'squashed_gaussian{filename_std_dev(t_sig, "tsig")}'
                 f'{filename_std_dev(freq, "freq")}')

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']
    method, reality = config['sampling'], config['reality']

    # function on the grid
    def grid_fun(theta, phi, theta_0=0, theta_sig=t_sig, freq=freq):
        f = np.exp(
            -((((theta - theta_0) / theta_sig) ** 2) / 2)) * np.sin(freq * phi)
        return f

    thetas, phis = ssht.sample_positions(L, Method=method, Grid=True)
    f = grid_fun(thetas, phis)
    flm = ssht.forward(f, L, Method=method, Reality=reality)

    return flm, func_name, config


def elongated_gaussian(args=[0, -3]):
    # args
    try:
        t_sig, p_sig = [10 ** x for x in args]
    except ValueError:
        print('function requires two extra args')
        raise

    # filename
    func_name = (f'elongated_gaussian{filename_std_dev(t_sig, "tsig")}'
                 f'{filename_std_dev(p_sig, "psig")}')

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']
    method, reality = config['sampling'], config['reality']

    # function on the grid
    def grid_fun(theta, phi, theta_0=0, phi_0=np.pi, theta_sig=t_sig, phi_sig=p_sig):
        f = np.exp(-((((theta - theta_0) / theta_sig) **
                      2 + ((phi - phi_0) / phi_sig) ** 2) / 2))
        return f

    thetas, phis = ssht.sample_positions(L, Method=method, Grid=True)
    f = grid_fun(thetas, phis)
    flm = ssht.forward(f, L, Method=method, Reality=reality)

    return flm, func_name, config


def spherical_harmonic(ell, m):
    # filename
    func_name = f'spherical_harmonic_l{ell}_m{m}'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=False
    )
    config = {**config, **extra}
    L = config['L']

    # create flm
    flm = np.zeros((L * L), dtype=complex)
    ind = ssht.elm2ind(ell, m)
    flm[ind] = 1

    return flm, func_name, config


def earth():
    # filename
    func_name = 'earth'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']

    # extract flm
    matfile = os.path.join(
        __location__, 'data', 'EGM2008_Topography_flms_L2190')
    mat_contents = sio.loadmat(matfile)
    flm = np.ascontiguousarray(mat_contents['flm'][:, 0])

    # fill in negative m components so as to
    # avoid confusion with zero values
    for ell in range(L):
        for m in range(1, ell + 1):
            ind_pm = ssht.elm2ind(ell, m)
            ind_nm = ssht.elm2ind(ell, -m)
            flm[ind_nm] = (-1) ** m * np.conj(flm[ind_pm])

    # don't take the full L
    # invert dataset as Earth backwards
    flm = np.conj(flm[:L * L])

    return flm, func_name, config


def wmap_helper(file_ending):
    # filename
    func_name = 'wmap'

    # setup
    config = asdict(Config())
    extra = dict(
        reality=True
    )
    config = {**config, **extra}
    L = config['L']

    # create flm
    matfile = os.path.join(os.environ[
        'SSHT'], 'src', 'matlab', 'data', f'wmap{file_ending}')
    mat_contents = sio.loadmat(matfile)
    cl = np.ascontiguousarray(mat_contents['cl'][:, 0])

    # same random seed
    np.random.seed(0)

    # Simulate CMB in harmonic space.
    flm = np.zeros((L * L), dtype=complex)
    for ell in range(2, L):
        cl[ell - 1] = cl[ell - 1] * 2 * np.pi / (ell * (ell + 1))
        for m in range(-ell, ell + 1):
            ind = ssht.elm2ind(ell, m)
            if m == 0:
                flm[ind] = np.sqrt(cl[ell - 1]) * np.random.randn()
            else:
                flm[ind] = np.sqrt(cl[ell - 1] / 2) * np.random.randn() + \
                    1j * np.sqrt(cl[ell - 1] / 2) * np.random.randn()

    return flm, func_name, config


def wmap():
    # file_ending = '_lcdm_pl_model_yr1_v1'
    # file_ending = '_tt_spectrum_7yr_v4p1'
    file_ending = '_lcdm_pl_model_wmap7baoh0'
    return wmap_helper(file_ending)


def valid_plotting(func_name):
    # check if valid function
    if func_name in total:
        return func_name
    else:
        raise ValueError('Not a valid function name to plot')


def valid_kernels(func_name):
    # check if valid function
    if func_name in functions:
        return func_name
    else:
        raise ValueError('Not a valid kernel name to convolve')


functions = {
    'dirac_delta': dirac_delta,
    'gaussian': gaussian,
    'identity': identity,
    'squashed_gaussian': squashed_gaussian,
    'elongated_gaussian': elongated_gaussian,
    'spherical_harmonic': spherical_harmonic
}
maps = {
    'earth': earth,
    'wmap': wmap
}
# form dictionary of all functions
total = {**functions, **maps}

if __name__ == '__main__':
    # initialise to None
    glm, glm_name = None, None

    # if flm is spherical harmonics then
    # obviously not a convolution
    if sys.argv[1] == 'spherical_harmonic':
        args = read_args(True)
        flm_input = total[args.flm]
        flm, flm_name, config = flm_input(args.l, args.m)
    else:
        args = read_args()
        flm_input = total[args.flm]
        glm_input = functions.get(args.convolve)
        # if not a convolution
        if glm_input is None:
            num_args = flm_input.__code__.co_argcount
            if args.extra_args is None or num_args == 0:
                flm, flm_name, config = flm_input()
            else:
                flm, flm_name, config = flm_input(args.extra_args)
        # if convolution then flm is a map so no extra args
        else:
            flm, flm_name, _ = flm_input()
            num_args = glm_input.__code__.co_argcount
            if args.extra_args is None or num_args == 0:
                glm, glm_name, config = glm_input()
            else:
                glm, glm_name, config = glm_input(args.extra_args)

    # if use input from argparse
    config['routine'] = args.routine
    config['type'] = args.type
    config['annotation'] = args.annotation

    sc = SiftingConvolution(flm, flm_name, config, glm, glm_name)
    sc.plot(args.alpha, args.beta, args.gamma)
