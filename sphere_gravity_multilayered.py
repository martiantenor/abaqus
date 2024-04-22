#!/usr/bin/env python
# A program to calculate the radial displacement at a given radius (r) of a
# self-compressing sphere, and the pressure at its center. Can accommodate
# spheres with up to 3 layers.

from math import pi

# Universal gravity constant
G = 6.67384e-11 #N.m2.kg-2, or m3.kg-1.s-2

def u(r, E=1e10, sigma=0.25, layers=[(10,1000)]):
    """
    Calculate radial displacement at a given radius within a sphere
    self-compressing under gravity. The main equation for this comes from Theory of
    Elasticity by L. Landau and E. Lifshitz (2nd ed, English, 1970, Section 7,
    Problem 3). Here, that equation has been modified to work for spheres with
    layered densities (but equal Young's moduli and poisson ratios). [IN
    PROGRESS]

    Takes as input the radius of interest r, plus, as a set containing tuples
    for each layer, layers=[(layer radius R, Poisson's ratio sigma, Young's
    modulus E, sphere density rho)]
    """

    # Pull out the parameters for each layer (really just nested spheres)
    layer_radii = []
    for layer in layers:
        layer_radii.append(layer[0])
    densities = []
    for layer in layers:
        densities.append(layer[1])

    # Local g is a function of the summed mass of all the layers within your
    # radius, r. To account for this, we'll first sum up the mass of all
    # layers whose outer radius R is smaller than r, since those whole
    # spheres are enclosed by a sphere of radius r. The first sphere where R
    # > r is the only one we have to consider, and only the parts of it that
    # are within r; spheres that have inner radii R_inner > r don't matter,
    # as they can be treated as spherical shells that don't exert any force
    # at our radius
    mass_within_r = 0
    for i in range(len(layer_radii)):

        # Get the properties of the current layer we're looking at
        this_R = layer_radii[i]
        this_rho = densities[i]

        ###DEBUG
        #print this_R, this_rho, r

        # If the layer is totally within r, add the whole thing
        if this_R <= r:
            mass_within_r += (4.0/3.0)*pi * this_rho * this_R**3

        # If we're exactly at the edge of this layer, stop now
        if this_R == r:
            break

        # If this is the first layer where R > r, use its density to figure out
        # the last part of mass_within_r, and then break out of this loop
        # (because layers farther out can be treated as spherical shells that
        # don't matter for gravity on points interior to them)
        if this_R > r:

            # Add the mass of a sphere with the current density and our
            # radius of interest...
            mass_within_r += (4.0/3.0)*pi * this_rho * r**3

            # ... and then subtract the mass of a sphere with the current
            # density and the radius of the next sphere inward (the bottom edge
            # of the current layer), unless this is our only layer
            if len(layer_radii) != 0:
                mass_within_r -= (4.0/3.0)*pi * this_rho * layer_radii[i-1]**3
            else:
                pass

            # Now break out of the loop to avoid counting layers farther out
            break

    ###DEBUG
    #print "Mass within r is", mass_within_r

    # Calculate local gravity using this newly-found mass_within_r number (this
    # is an old equation, but can be found in e.g. Turcotte & Schubert, Eq.
    # 2-66)
    local_g = G * mass_within_r * r**-2

    ###DEBUG
    #local_g = 10*r/this_R

    # Finally, calculate radial displacement, using the equation from Theory of
    # Elasticity by Landau & Lifshitz (2nd ed., English, 1970), Section 7,
    # Problem 3.
    radial_displacement = - r * local_g * this_rho * this_R         \
                          * (1-2*sigma) * (1+sigma)                 \
                          * ((3-sigma)/(1+sigma) - r**2/this_R**2)  \
                          / (10*E*(1-sigma))

    ###DEBUG
    #print "1:", local_g
    #print "2:", radial_displacement
    #return local_g

    return radial_displacement, local_g


# Plugging in values

###DEBUG
#value1, value2 = u(10)
#print value1
#print value2

# Hand-calculated answer
print "Calculated by hand, 10 m sphere, 1000 kg.m-3, E=1e10 Pa, nu = .25"
print "    u = -2.79553e-12 m"

# Single-layered test sphere
# Parameters: R = 10 m, rho = 1000 km/m3, E = 1e10 Pa, sigma = 0.25
#print "Single-layered test sphere (at r = 10 m):"
#print "    u = %.5e m"%u(10, E=1e10, sigma=0.25, layers=[(10,1000)])[0]
#print "Single-layered test sphere (at r = 8 m):"
#print "    u = %.5e m"%u(8)[0]

# Two-layered test sphere, layers of equal density, effectively same as above
# Parameters: R = 5 / 10, rho = 1000 / 1000, E = 1e10, sigma = 0.25
#print "Sphere with two layers of equal density (total R same as above):"
#print "    u = %.5e m"%u(10, E=1e10, sigma=0.25, layers = [(5,1000),(10,1000)])[0]

# Two-layered test sphere, but with r at edge of inner layer
# Parameters: R = 10 / 20,  rho = 1000 / 2000, E = 1e10, sigma = 0.25
#print "Two-layered test sphere (r @ edge of inner layer):"
#print "    u = %.5e m"%u(10, E=1e10, sigma=0.25, layers = [(10,1000),(20,1000)])[0]

# Earth
# Parameters: R = 1210 / 3470 / 6325 / 6360
#print "Very rough approximation of gravitational acceleration within the Earth:"
#print "    u = %.5e m.s-2"%(u( 6360e3, E=1e10, sigma=0.25,
#                               layers=[(1210e3,13000),(3470e3,11000),
#                                       (6325e3,3000),(6360e3,2600)]
#                             )[1])
