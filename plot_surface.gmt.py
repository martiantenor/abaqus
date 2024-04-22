#!/usr/bin/env python
# A program to take a field output report file containing Y coordinates from
# nodes at the surface of a 2D axisymmetric model and plot them (in GMT)
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
import optparse, sys, subprocess, re

__version__ = "2013.02.03"
#__version__ = "2015.05.15"


######## Options ###############################################################

# File ending for the csv file?
csv_suffix = "_surfacecoords.csv"

# Name of the output file?
outfile_name = "surface_coordinates.ps"

# Print out extra text while running?
verbose_mode = True


######## Main Program ##########################################################

def rptfile_parser(rptfile):
    """
    Goes through a .rpt file containing nodal coordinate data and generates
    an easier-to-use .csv file
    """

    data = []
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
            x = eval(line.split()[1]) / 1000
            y = eval(line.split()[2]) / 1000
            data.append((x,y))

        else:
            continue

    data.sort()
    return data


def GMT_plotter(csvfile):
    """
    Plots up the data files passed into it with a quick psxy command
    """

    #print csvfile.name

    proc = subprocess.Popen("psxy -JX%s -R%s -W2 -B%s -X2i -Y2i -P -K"%(
                                "4i/2.0i",
                                "0/2000/-10./10.",
                                'a2000g100:"Radius":/a10g1:"Elevation":WS'),
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
    usage = "%prog [options] foo.SURFACErpt"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True

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
                         csv_suffix,
                         rptfilename)
    if verbose_mode:
        print "Generating csv file %s..."%(csvfilename)

    csvfile = open(csvfilename,'w')
    for xy_pair in data:
        csvfile.write("%14f %14f\n"%(xy_pair[0],xy_pair[1]))

#    # Plot up the csv file
#    if verbose_mode:
#        print "Sending results to psxy..."
#
#    psfilename = GMT_plotter(csvfile)
#
#    # Display the resulting post-script file
#    proc = subprocess.Popen("evince %s"%(psfilename),shell=True)
#    proc.communicate()
