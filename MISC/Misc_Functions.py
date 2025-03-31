# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

import math
import numpy as np


def sinc(ui, value):
    '''
    Function to calculate the sinc function of a given value. Function take 'self' as an argument in order to get access to the main UI input values.

    Parameters
    ----------
    value: Float
        Value for which to calculate the sinc function.
    '''

    if value == 0:
        return 1
    else:
        spatial_frequency_1 = 1/(ui.pixelSize.value()/1000)
        f_ratio = value / spatial_frequency_1
        return math.sin(math.pi*f_ratio) / (math.pi*f_ratio)


def PolyCoefficients(x, coeffs):
    '''
    Function to calculate the magnitude of a polynomial equation at a given value 'x', for a set of coefficients 'coeffs'

    Parameters
    ----------
    x: Float
        variable for which to calculate the polynomial value (y), given the coefficients.
    coeffs: List
        List of the coefficients for the polynomial function
    '''

    o = len(coeffs)
    y = 0
    for i in range(o):
        y += coeffs[i]*x**(o - 1 - i)
    return y


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    '''
    Custom implementation of the Savitzky Golay filter

    Parameters
    ----------
    y: list of initial values
        blah
    window_size: int
        blah
    order: int
        Order of polynomial fit
    deriv: Optional
        Something
    rate: Optional
        Something

    Returns
    ----------
    Numpy Array of new filtered values
    '''

    from math import factorial
    
    try:
        window_size = np.abs(int(window_size))
        order = np.abs(int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.asmatrix([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')


def get_line_from_equation(m, b):
    '''
    Function to generate two end points of a line from a linear equation
    
    Parameters
    ----------
    m: Float
        Gradient of the linear line.
    b: Float
        Y-intersection of the linear line.

    Returns:
    ----------
    Two tuples, (x1, y1), (x2, y2), which are two extreme points on the line.
    '''

    x1 = -1000
    x2 = 1000
    y1 = int(m * x1 + b)
    y2 = int(m * x2 + b)

    return (x1, y1), (x2, y2)


def f_logistic(data, a, b, c, d):
    '''
    Function to return the logistic function

    a / (1 + (np.exp(-b * (data - c)))) + d
    
    Parameters
    ----------
    data:

    a:

    b:

    c:

    d:


    Returns:
    ----------
    Returns a / (1 + (np.exp(-b * (data - c)))) + d
    '''
    return a / (1 + (np.exp(-b * (data - c)))) + d


def rotate2d(origin, point, angle):
    '''
    Function to rotate a point about an origin by a given angle, and return a new 3-d point
    
    Parameters
    ----------
    origin:
        The point about which to rotate the point
    point:
        The point to be rotated about the origin point
    angle:
        The angle about which to rotate the point about the origin point

    Returns:
    ----------
    Numpy array, 3-D point, [x, y, 0] of the new point.
    '''

    ox, oy, pz = origin
    px, py, pz = point

    theta = math.radians(angle)

    qx = ox + math.cos(theta) * (px - ox) - math.sin(theta) * (py - oy)
    qy = oy + math.sin(theta) * (px - ox) + math.cos(theta) * (py - oy)

    return np.array([qx, qy, 0])