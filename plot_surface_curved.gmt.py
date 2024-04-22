#!/usr/bin/env python
# A program to take a field output report file containing R and Theta
# coordinates from nodes at the surface of a curved 2D axisymmetric model and
# plot them (in GMT)
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
from math import radians, pi
#import optparse, sys, subprocess, re
import optparse, sys, os, re

__version__ = "2013.12.19"


######## Options ###############################################################

# Name of the output file?
outfile_name = "surface_coordinates.ps"

# Plot the output, or just generate .csv file?
plot_mode = False

# Print out extra text while running?
verbose_mode = True

# Diameter of the body?
planet_radius = 1740e3 #m
#planet_radius = 99990000.0 #m


######## Main Program ##########################################################

def rptfile_parser(rptfile):
    """
    Goes through a .rpt file containing nodal coordinate data and generates
    an easier-to-use .csv file
    """

    planet_circumference = 2*pi*planet_radius

    data = []
    for line in rptfile:

        # Skip blank lines
        if line.strip() == "":
            continue

        # Check for erroneous file types
        if line.strip().upper().endswith("COOR1"):
            print "ERROR: Please order file as COORD1, COORD2"
            sys.exit()

        # But if it's a number, grab the values and do the curved-to-flat
        # converstion right here
        if line.strip()[0].isdigit():
            R = eval(line.split()[1])
            Th = eval(line.split()[2])

            x = ( Th/(2*pi) * planet_circumference ) / 1000
            y = ( R - planet_radius) / 1000

            data.append((x,y))

        else:
            continue

    data.sort()
    return data


def GMT_plotter(csvfilename):
    """
    Plots up the data files passed into it with a quick psxy command
    """

    #proc = subprocess.Popen("psxy -%s -%s -%s -%s"%(
    #                        "JX8i/6i",
    #                        "R0/1200/-10./10.",
    #                        "Ba100g50:'Distance':/a5g1:'Elevation':WS",
    #                        "Wthickest,blue -X1.5i -Y1.5i -K"),
    #                        shell=True,
    #                        stdout = subprocess.PIPE)
    #psfile_contents = proc.communicate(csvfile.name)[0]
    #
    ## Write that file
    #psfilename = re.sub(".csv",".ps",csvfile.name)
    #psfile = open(psfilename,'w')
    #psfile.write(psfile_contents)
    #psfile.close()

    # Since the subprocess() plotter doesn't seem to work, I'm mimicking the way
    # I did this successfully in "plot_temperatures.gmt.sh"
    psfilename = re.sub(".csv",".ps",csvfilename)
    os.system("psxy %s -%s -%s -%s -%s > %s"%(
               csvfilename,
               'JX8i/6i',
               'R0/1200/-5./5.',
               'Ba100g50:"Distance (km)":/a5g1:"Elevation (km)":WS',
               'Wthickest,blue -X1.5i -Y1.5i -K',
               psfilename))
    print "Plot saved as %s"%psfilename
    os.system("evince %s"%psfilename)


######## Command-line Implementation############################################

if __name__ == "__main__":

    # Start the parser, and define options
    usage = "%prog [options] foo.COORDrpt"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")
    parser.add_option("--noGMT",action="store_true",
                      dest="noGMT",default=False,
                      help="suppress GMT plotting of generated .csv file")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True
    if options.noGMT:
        plot_mode = False

    # Process positional arguments. There should be exactly one specified: the
    # nodal temperature field output file, which we will then open
    if len(args) != 1:
        print "ERROR: Please specify one and only one coordinates .rpt file"
        sys.exit()
    else:
        rptfilename = args[0]
        rptfile = open(rptfilename, 'r')

    # Print out status about the files we're acting on
    if verbose_mode:
        print "Reading file %s..."%(rptfilename)

    # Run the rpt file parser to get the data we need
    data = rptfile_parser(rptfile)

    # Generate a csv file from this data
    csvfilename = re.sub(".%s"%rptfilename.split(".")[-1],
                         "_surfacecoords.csv",
                         rptfilename)
    if verbose_mode:
        print "Generating csv file %s..."%(csvfilename)

    csvfile = open(csvfilename,'w')
    for xy_pair in data:
        csvfile.write("%14f %14f\n"%(xy_pair[0],xy_pair[1]))
    csvfile.close()

    # Plot up the csv file, if we're in plot_mode
    if plot_mode:
        if verbose_mode:
            print "Sending results to psxy..."
        GMT_plotter(csvfilename)
