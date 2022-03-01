from numpy import array, zeros, ones, flipud, fliplr
from scipy.signal import lfilter
from math import sqrt

def __gausscoeff(s):
    if s < .5: raise ValueError('Sigma for Gaussian filter must be >0.5 samples')

    q = 0.98711*s - 0.96330 if s > 0.5 else 3.97156 \
    - 4.14554*sqrt(1.0 - 0.26891*s)
    b = zeros(4)
    b[0] = 1.5785 + 2.44413*q + 1.4281*q**2 + 0.422205*q**3
    b[1] = 2.44413*q + 2.85619*q**2 + 1.26661*q**3
    b[2] = -(1.4281*q**2 + 1.26661*q**3)
    b[3] = 0.422205*q**3
    B = 1.0 - ((b[1] + b[2] + b[3])/b[0])
    # convert to a format compatible with lfilter's
    # difference equation
    B = array([B])
    A = ones(4)
    A[1:] = -b[1:]/b[0]

    return B,A

def Gaussian1D(signal, sigma, padding=0):
    n = signal.shape[0]
    tmp = zeros(n + padding)
    if tmp.shape[0] < 4: raise ValueError('Signal and padding too short')
    tmp[:n] = signal
    B,A = __gausscoeff(sigma)
    tmp = lfilter(B, A, tmp)
    tmp = tmp[::-1]
    tmp = lfilter(B, A, tmp)
    tmp = tmp[::-1]
    
    return tmp[:n]

def Gaussian2D(image, sigma, padding=0):
    n,m = image.shape[0],image.shape[1]
    tmp = zeros((n + padding, m + padding))
    if tmp.shape[0] < 4: raise ValueError('Image and padding too small')
    if tmp.shape[1] < 4: raise ValueError('Image and padding too small')

    B,A = __gausscoeff(sigma)
    tmp[:n,:m] = image
    tmp = lfilter(B, A, tmp, axis=0)
    tmp = flipud(tmp)
    tmp = lfilter(B, A, tmp, axis=0)
    tmp = flipud(tmp)
    tmp = lfilter(B, A, tmp, axis=1)
    tmp = fliplr(tmp)
    tmp = lfilter(B, A, tmp, axis=1)
    tmp = fliplr(tmp)

    return tmp[:n,:m]