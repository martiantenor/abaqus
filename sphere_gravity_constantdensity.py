#!/usr/bin/env python
# A program to calculate the radial displacement at a given radius (r) of a
# self-compressing sphere, and the pressure at its center. Can accommodate
# spheres with up to 3 layers.

from __future__ import division
from math import pi

# Universal gravity constant
G = 6.67384e-11 #N.m2.kg-2, or m3.kg-1.s-2

def u(r, R=10, rho=1000, E=1e10, sigma=0.25):
    """
    Calculate radial displacement at a given radius within a sphere
    self-compressing under gravity, using the equation from Theory of
    Elasticity by L. Landau and E. Lifshitz (2nd ed, English, 1970, Section 7,
    Problem 3).

    Takes as input the radius of interest r, plus the overall radius of the
    sphere R, Poisson's ratio sigma, Young's modulus E, and sphere density rho.
    """

    # Calculate the mass within our radius of interest
    mass_within_r = (4/3)*pi * rho * r**3

    # Calculate local gravity using this newly-found mass_within_r number (this
    # is an old equation, but can be found in e.g. Turcotte & Schubert, Eq.
    # 2-66)
    g_local = G * mass_within_r * r**-2

    # Calculate radial displacement, using the equation from Theory of
    # Elasticity by Landau & Lifshitz (2nd ed., English, 1970), Section 7,
    # Problem 3.
    radial_displacement = - r * g_local * rho * R               \
                          * (1-2*sigma) * (1+sigma)             \
                          * ((3-sigma)/(1+sigma) - r**2/R**2)   \
                          / (10*E*(1-sigma))

    return radial_displacement, g_local


# Plugging in values

# Hand-calculated answer
print "Calculated by hand, 10 m sphere, 1000 kg.m-3, E=1e10 Pa, nu = .25"
print "    u = -2.79553e-12 m"

# Single-layered test sphere
# Parameters: R = 10 m, rho = 1000 km/m3, E = 1e10 Pa, sigma = 0.25
print "20 m diameter test sphere (at r = 10 m):"
print "    u = %.5e m"%u(10, R=10, rho=1000, E=1e10, sigma=0.25)[0]
print "    g = %.5e m.s-2"%u(10, R=10, rho=1000, E=1e10, sigma=0.25)[1]
print "20 m diameter test sphere (at r = 8 m):"
print "    u = %.5e m"%u(8, R=10, rho=1000, E=1e10, sigma=0.25)[0]
print "2000 km diameter test sphere (at r = 8 m):"
print "    u = %.5e m"%u(8, R=2e6, rho=3000, E=1e10, sigma=0.25)[0]
print "    g = %.5e m.s-2"%u(2e6, R=2e6, rho=3000, E=1e10, sigma=0.25)[1]
