#!/usr/bin/env python
# A program to take a field output report file containing nodal temperatures
# from nodes at both edges of a 2D axisymmetric model and split them into two
# plain XY files for plotting (currently, in GMT).
#
# (c) David Blair, 2013. This work is licensed under a Creative Commons
# Attribution-NonCommercial-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-nc-sa/3.0/deed.en_US)

from __future__ import division
import optparse, sys, subprocess

__version__ = "2014.01.03"


######## Options ###############################################################

# Flat or curved model?
#model_type = "flat"
model_type = "curved"

# Basin depth to subtract from left-edge (center-of-basin) results
basin_depth = 8000.0 #m

# For curved models: what's the radius of the surface?
planet_radius = 1740e3 #m

# Distance to R side of the model? (give in radians for curved models
#rightside_distance_flat = 2.7e6 #m
rightside_angle_curved = -3.14159   # 180 deg
#rightside_angle_curved = 1.5708     # 90 deg
#rightside_angle_curved = 1.04720    # 60 deg

# TEST CASE 1:
#planet_radius = 1e8 - 10000 #m
#rightside_angle_curved = 0.0270002 # 1.547 degrees


# Plot only nodes from the right edge or left edge of the model?
plot_right_only = False
plot_left_only = False

# Print out extra text while running?
verbose_mode = True


######## Main Program ##########################################################

def rptfile_parser(rptfile):
    """
    Goes through a .rpt file containing nodal temperature data for the left and
    right edges of a model, and splits it into two much simpler sets of XY data
    """

    TYdata_left = []
    TYdata_right = []
    TYdata_rest = []

    for line in rptfile:

        # Skip blank lines
        if line.strip() == "":
            continue

        # Check for erroneous file types
        if line.strip().upper().endswith("COOR1"):
            print "ERROR: Please order file as COORD1, COORD2, NT"
            sys.exit()

        # But if it's a number...
        if line.strip()[0].isdigit():

            if model_type == "flat":
                x = eval(line.split()[1])
                y = eval(line.split()[2])
                T = eval(line.split()[3])

                if x == 0:
                    #print "LEFT!"
                    TYdata_left.append([T,(y + basin_depth)])
                elif x == rightside_distance_flat:
                    #print "RIGHT!"
                    TYdata_right.append([T,y])
                else:
                    TYdata_rest.append([T,y])

            elif model_type == "curved":
                depth = -(planet_radius - eval(line.split()[1]))
                theta = eval(line.split()[2])
                T = eval(line.split()[3])

                if theta == 0:
                    #print "LEFT!"
                    TYdata_left.append([T,(depth + basin_depth)])
                        # these should both be positive numbers...
                elif theta == rightside_angle_curved:
                    #print "RIGHT!"
                    TYdata_right.append([T,depth])
                else:
                    TYdata_rest.append([T,depth])

        else:
            continue

    return TYdata_left, TYdata_right, TYdata_rest


def GMT_plotter(datasets,plotname):
    """
    Plots up the data files passed into it by sending them to a bash script for
    GMT plotting (by way of writing output files)
    """

    import os

    # What's the name of the GMT plotting script?
    plotter="plot_temperatures.gmt.sh"

    # Go throught the data and make two simple XY files
    for dataset in datasets:
        this_outfile = open("%s.thermprofile"%["edgeleft","edgeright","middle"][datasets.index(dataset)],'w')
        for item in dataset:
            this_outfile.write("%14f %14f\n"%(item[0],item[1]))
        this_outfile.close()

    ###DEBUG - DEFUNCT?
    # Make a temporary file for use below
    #os.system("touch .plot_temperatures.gmt.tmp")

    # Call the "thermal.gmt" script with the outfile names as arguments
    # Supposedly "subprocess" is the better way to do this, but it doesn't work...
    #subprocess.call(["thermal.gmt","edge0.thermprofile","edge1.thermprofile"])
    # ...so I'll use an os.system call instead
    if plot_right_only and not plot_left_only:
        print "Sending results to GMT for right side only..."
        os.system("%s %s edgeright.thermprofile"%(plotter,plotname))
    elif plot_left_only and not plot_right_only:
        print "Sending results to GMT for left side only..."
        os.system("%s %s edgeleft.thermprofile"%(plotter,plotname))
    elif plot_right_only and plot_left_only:
        print "Sending results to GMT for left and right edges..."
        os.system("%s %s edgeleft.thermprofile edgeright.thermprofile"%(plotter,plotname))
    else:
        print "Sending results to GMT..."
        os.system("%s %s edgeleft.thermprofile edgeright.thermprofile middle.thermprofile"%(plotter,plotname))

    # Delete the (empty) temporary file
    os.system("rm -f .plot_temperatures.gmt.tmp")



######## Command-line Implementation############################################

if __name__ == "__main__":

    # Start the parser, and define options
    #this_usage = "%prog [options] foo.NTrpt\n(foo.NTrpt format: COORD1, COORD2, NT)"
    #this_epilog = j
    parser = optparse.OptionParser(
        usage="%prog [options] foo.NTrpt\n(foo.NTrpt format: COORD1, COORD2, NT)",
        epilog="In plots with more than one edge shown, the left edge of the "\
               "model is shown in blue, while the right edge is shown in "\
               "red. When present, nodes from the middle of the model are "\
               "shown in green.")
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")
    parser.add_option("-c","--curved",action="store_true",
                      dest="curved_mode",default=False,
                      help="process data from a curved, instead of flat, axisymmetric model")
    parser.add_option("-r","--rightonly",action="store_true",
                      dest="plot_right_only",default=False,
                      help="plot up results only from the far (right) edge")
    parser.add_option("-l","--leftonly",action="store_true",
                      dest="plot_left_only",default=False,
                      help="plot up results only from the center of the basin (the left edge)")
    parser.add_option("-e","--edgesonly",action="store_true",
                      dest="plot_edges_only",default=False,
                      help="plot up results from the left and right edges of the "
                           "basin, but not the middle of the basin")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True
    if options.curved_mode:
        model_type = "curved"
    if options.plot_right_only:
        plot_left_only = False
        plot_right_only = True
    if options.plot_left_only:
        plot_left_only = True
        plot_right_only = False
    if options.plot_edges_only:
        plot_left_only = True
        plot_right_only = True

    # Process positional arguments. There should be exactly one specified: the
    # nodal temperature field output file, which we will then open
    if len(args) != 1:
        print "ERROR: Please specify one and only one a nodal temperature .rpt file"
        sys.exit()
    else:
        rptfilename = args[0]
        rptfile = open(rptfilename, 'r')

    # Print out status about the files we're acting on
    if verbose_mode:
        print "Reading file %s..."%(rptfilename)

    # Run the rpt file parser to get the data we need
    TYdata_left, TYdata_right, TYdata_rest = rptfile_parser(rptfile)

    # Plot up the data
    #GMT_plotter([[[1,1],[2,2],[3,3]],[[11,11],[22,22],[33,33]]])
    GMT_plotter([TYdata_left,TYdata_right,TYdata_rest],rptfilename)
