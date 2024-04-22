#!/usr/bin/env python
# A program to take a report file containing alternating rows of X and Y
# coordinates from the end state of a model and subtract alternate rows to
# arrive at a crustal thickness data set. To create this file, do a "probe
# values" operation on an Abaqus ODB, probing values from a given radius at the
# top of the crust, then that same radius at the bottom of the crust, then the
# next radius out at the top, then at the bottom, and so on.
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
import optparse, sys, subprocess, re

__version__ = "2013.05.16"


######## Options ###############################################################

# Part instance name
instancename = "MASTER-1"

# File ending for the csv file?
csv_suffix = "_crustalthickness.csv"

# Name of the postscript output file?
outfile_name = "crustal_thickness.ps"

# Print out extra text while running?
verbose_mode = True


######## Main Program ##########################################################

def rptfile_parser(rptfile):
    """
    Goes through a .rpt file containing nodal coordinate data and subtract
    alternate lines to get at a crustal thickness data set
    """

    oddlines_data = []
    data = []
    dataline_number = 1
    for line in rptfile:

        # Skip blank lines
        if line.strip() == "":
            continue

        # Check for erroneous file types
        if line.strip().upper().endswith("COOR1"):
            print "ERROR: Please order file as COORD1, COORD2"
            sys.exit()

        # If the line starts with the part instance name, do stuff
        if line.strip().startswith(instancename):

            # Get the values of interest
            this_x = eval(line.split()[5]) #/ 2000 #DEBUG: Why do I sometimes need a factor of 2?
            this_y = eval(line.split()[6]) #/ 2000

            # If it's an odd numbered line, store the value
            if dataline_number % 2 != 0:
                oddlines_data.append((this_x,this_y))

                ###DEBUG
                print "EVEN: %f %f"%(this_x, this_y)

            # If it's an even number, use the last odd-numbered line's values
            # for comparison
            elif dataline_number %2 == 0:
                top_of_crust_x = oddlines_data[-1][0]
                top_of_crust_y = oddlines_data[-1][1]

                avg_x = (top_of_crust_x + this_x)/2.0
                diff_y = abs(top_of_crust_y - this_y)

                ###DEBUG
                print "ODD: top %f top %f"%(top_of_crust_x, top_of_crust_y)
                print "ODD: %f %f"%(avg_x, diff_y)

                data.append((avg_x,diff_y))

            else:
                print "WHAT THE HELL KINDA CRAZY MATH IS THIS?!?!?"

            dataline_number += 1

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
    usage = "%prog [options] foo.NTrpt"
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
