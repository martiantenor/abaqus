#!/usr/bin/env python
# A program to take a report file containing the coordinates of the Moho and
# record those at set radial distances as positive numbers (depths)
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
from math import radians, pi
import optparse, sys, subprocess, re

__version__ = "2015.02.03"


######## Options ###############################################################

# File ending for the csv file?
csv_suffix = "_crustalthickness.csv"

# Name of the postscript output file?
outfile_name = "crustal_thickness.ps"

# Is the model curved?
curved_mode = False

# Lateral spacing?
spacing = 5000 #m

# Print out extra text while running?
verbose_mode = True

# For curved models, we'll need this:
planet_radius = 1740e3 #m
#planet_radius = 99990000 #m


######## Main Program ##########################################################

def rptfile_parser(rptfile):
    """
    Goes through a .rpt file containing nodal coordinate data and organizes those
    values into depths at a given spacing of lateral coordinates
    """


    # Make a new dictionary to hold our data
    data = {}

    # Go through the file#
    for line in rptfile:

        # Skip blank lines
        if line.strip() == "":
            continue

        # Check for erroneous file types
        if line.strip().upper().endswith("COOR1"):
            print "ERROR: Please order file as COORD1, COORD2"
            sys.exit()

        # But if it's a number, grab the values (and convert to kilometers)
        if line.strip()[0].isdigit():

            # For the horizontal position, round to some value (given by the
            # "spacing" variable in Options). To do this, divide by the spacing
            # (which is given in meters!) so we get a number that's in units of
            # "X m". Then round to the nearest integer (round(X,0)), and then
            # multiply by 5 to get the real number. Finally, divide by 1000 to
            # convert the answer to km.
            x = ( float(spacing) * (round(eval(line.split()[1])/float(spacing)))) / 1000.0

            # For the depth, divide by 1000 (m -> km) and flip the sign
            y = eval(line.split()[2]) / -1000.0

            # If there's already data at this x coordinate, add our new value to
            # the average. If there isn't, start a new set.
            if x in data:
                data[x] = [sum(data[x],y) / (len(data[x])+1)]
            else:
                data[x] = [y]

        else:
            continue

    return data


def rptfile_parser_curved(rptfile):
    """
    Goes through a curved .rpt file containing nodal coordinate data and
    organizes those values into depths at a given spacing of lateral coordinates
    """

    planet_circumference = 2 * pi * planet_radius

    # Make a new dictionary to hold our data
    data = {}

    # Go through the file
    for line in rptfile:

        # Skip blank lines
        if line.strip() == "":
            continue

        # Check for erroneous file types
        if line.strip().upper().endswith("COOR1"):
            print "ERROR: Please order file as COORD1, COORD2"
            sys.exit()

        # But if it's a number, grab the values (and convert to kilometers)
        if line.strip()[0].isdigit():

            # For the horizontal position, round to some value (given by the
            # "spacing" variable in Options). To do this, divide by the spacing
            # (which is given in meters!) so we get a number that's in units of
            # "X m". Then round to the nearest integer (round(X,0)), and then
            # multiply by 5 to get the real number. Finally, divide by 1000 to
            # convert the answer to km.
            theta = eval(line.split()[2])
            x = float(spacing) \
                * round((theta/(2*pi) * planet_circumference)/spacing) \
                / 1000.0

            # For the depth, divide by 1000 (m -> km) and flip the sign
            R = eval(line.split()[1])
            y = (R - planet_radius) / -1000.0 #m

            # If there's already data at this x coordinate, add our new value to
            # the average. If there isn't, start a new set.
            if x in data:
                data[x] = [sum(data[x],y) / (len(data[x])+1)]
            else:
                data[x] = [y]

        else:
            continue

    return data


def thickness_calculator(moho_data, surface_data):
    """
    Subtracts the topography from the Moho data to get a crustal thickness
    """

    thickness_data = {}
    x_coords = []

    # Get a sorted version of each dictionary's key set
    moho_x_coords = moho_data.keys()
    moho_x_coords.sort()
    surface_x_coords = surface_data.keys()
    surface_x_coords.sort()

    # Go through the x coordinates of whichever set is shorter
    for this_x_coord in \
        (moho_x_coords,surface_x_coords)[len(surface_x_coords)<len(moho_x_coords)]:

        if (this_x_coord in moho_x_coords) and \
           (this_x_coord in surface_x_coords):

            x_coords.append(this_x_coord)

            #print this_x_coord, float(moho_data[this_x_coord][0])

            thickness_data[this_x_coord] = float(moho_data[this_x_coord][0]) - \
                                           float(surface_data[this_x_coord][0])


    return thickness_data, x_coords


def GMT_plotter(csvfile):
    """
    Plots up the data files passed into it with a quick psxy command
    """

    #print csvfile.name

    proc = subprocess.Popen("psxy -JX%s -R%s -W2 -B%s -X2i -Y2i -P -K"%(
                                "4i/2.0i",
                                "0/2000/-10./10.",
                                'a2000g100:"Radius":/a10g1:"Depth Below Geoid":WS'),
                            shell=True,
                            stdout = subprocess.PIPE)
    psfile_contents = proc.communicate(csvfile.name)[0]

    # Write that file
    psfilename = re.sub(".csv",".ps",csvfile.name)
    psfile = open(psfilename,'w')
    psfile.write(psfile_contents)
    psfile.close()

    return psfilename


######## Command-line Implementation############################################


if __name__ == "__main__":

    # Start the parser, and define options
    usage = "%prog [options] foo.MOHOrpt foo.SURFACErpt"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")

    parser.add_option("-c","--curved",action="store_true",
                        help="run for a curved instead of flat model")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True
    if options.curved:
        curved_mode = True

    # Process positional arguments. There should be exactly one specified: the
    # nodal temperature field output file, which we will then open
    if len(args) != 2:
        print "ERROR: Please specify a MOHO and SURFACE .rpt file, in that order"
        sys.exit()
    else:
        moho_filename = args[0]
        surface_filename = args[1]
        moho_file = open(moho_filename, 'r')
        surface_file = open(surface_filename, 'r')

    # Print out status about the files we're acting on
    if verbose_mode:
        print "Reading file %s..."%(moho_filename)
        print "Reading file %s..."%(surface_filename)

    ###DEBUG: Single file usage
    #complete_data, x_coords = rptfile_parser(surface_file)

    # Run the rpt file parser on the two files
    if curved_mode:
        moho_data = rptfile_parser_curved(moho_file)
        surface_data = rptfile_parser_curved(surface_file)
    else:
        moho_data = rptfile_parser(moho_file)
        surface_data = rptfile_parser(surface_file)

    # Run them through the difference calculator to get a crustal thickness data
    # set
    thickness_data, x_coords = thickness_calculator(moho_data, surface_data)


    # Generate a csv file where we'll put the data
    csvfilename = re.sub(".%s"%moho_filename.split(".")[-1],
                         csv_suffix,
                         moho_filename)
    if verbose_mode:
        print "Generating csv file %s..."%(csvfilename)

    # Now write that data out
    csvfile = open(csvfilename, 'w')
    for x_coord in x_coords:
        csvfile.write("%14f %14f\n"%(x_coord, thickness_data[x_coord]))

    #surface_csvfile = open(surface_csvfilename, 'w')
    #for x_coord in x_coords:
    #    surface_csvfile.write("%14f %14f\n"%(x_coord, surface_data[x_coord][0]))

#    # Plot up the csv file
#    if verbose_mode:
#        print "Sending results to psxy..."
#
#    psfilename = GMT_plotter(csvfile)
#
#    # Display the resulting post-script file
#    proc = subprocess.Popen("evince %s"%(psfilename),shell=True)
#    proc.communicate()
