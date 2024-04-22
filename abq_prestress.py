#!/usr/bin/env python
# A program to take an Abaqus report file of vertical stresses in a model and
# insert the data back into another Abaqus input file as a lithostatic
# "prestress"
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
import string, re, sys, optparse
# Note - I'm using the deprecated "optparse" instead of the newer "argparse"
# because Taylor is running Python 2.6, and argparse wasn't introduced until
# Python 2.7

__version__ = "0.2"
__changedate__ = "2013.10.15"


######## Options ###############################################################

# What suffix is on the incoming file, and what do you want on the newly created
# file?
rptfile_tags = ["ps0","ps1","ps2","ps3","ps4","ps5","ps6","ps7","ps8","ps9","ps10"] #Iteration number stepping-up
outfile_tags = ["ps1","ps2","ps3","ps4","ps5","ps6","ps7","ps8","ps9","ps10","ps11"] #Iteration number stepping-up

#rptfile_tags = ["ps0","hyd1","hyd2","hyd3","hyd4","hyd5","hyd6","hyd7","hyd8","hyd9","hyd10"] #Iteration number stepping-up
#outfile_tags = ["hyd1","hyd2","hyd3","hyd4","hyd5","hyd6","hyd7","hyd8","hyd9","hyd10","hyd11"] #Iteration number stepping-up

#rptfile_tags = ["ps0","poi1","poi2","poi3","poi4","poi5","poi6","poi7","poi8","poi9","poi10"] #Iteration number stepping-up
#outfile_tags = ["poi1","poi2","poi3","poi4","poi5","poi6","poi7","poi8","poi9","poi10","poi11"] #Iteration number stepping-up

# Mode: flat, curved, threedee
mode = "flat"

# Print lots of stuff while running?
verbose_mode = True


######## Options ###############################################################

def rptfile_parser_flat(rptfile):
    """
    Goes through an Abaqus .rpt file and grabs all of the S.S22 (vertical)
    stresses, creating a set of entries (part, elemID, stress)
    """

    stresses = []

    for line in rptfile:

        # Totally ignore blank lines
        if line.strip() == "":
            continue

        # Figure out when we're in a new part
        if line.upper().startswith("FIELD OUTPUT REPORTED AT"):
            this_part = line.split()[-1]
            continue

        # We only care about lines starting with a number
        if line.strip()[0].isdigit():

            # First, make sure we're looking at the right kind of file!
            line_checker(line,2)

            # Next, process the data and add it to the stress set
            this_elemID = eval(line.split()[0])
            this_stress = eval(line.split()[-1])
            stresses.append((this_part, this_elemID, this_stress))

    return stresses


def rptfile_parser_curved(rptfile):
    """
    Goes through an Abaqus .rpt file and grabs the radial stress component (S11,
    after coordinate transformation), creating a series of entries (part,
    elemID, [S11])

    This code assumes gravity was only at 1% of its full value in the prestress
    run, and that the stress fed into it is the radial component.
    """

    stresses = []
    values_are_centroidal = False
    values_are_transformed = False

    for line in rptfile:

        # Totally ignore blank lines
        if line.strip() == "":
            continue

        # Check every line to see if the word "Centroidal" pops up, and set our
        # flag to True if it ever does
        if "CENTROIDAL" in line.upper():
            values_are_centroidal = True

        # Same idea, but checking to make sure we're in transformed coords
        if "COORDINATE SYSTEM" in line.upper():
            values_are_transformed = True

        # Figure out when we're in a new part
        if line.upper().startswith("FIELD OUTPUT REPORTED AT"):
            this_part = line.split()[-1]
            continue

        # We only care about lines starting with a number
        if line.strip()[0].isdigit():

            # First, check what kind of file we're in to make sure it's OK
            # (in that it only has 2 entries per line)
            line_checker(line,2)

            # Then, split up the line and add the data to our stress set
            this_elemID = eval(line.split()[0])
            this_stress = eval(line.split()[-1])
            stresses.append((this_part, this_elemID, this_stress))

    # Before proceeding, make sure that the file we just processed was using
    # centroidal values and transformed coords. If not, raise an error and exit.
    if not values_are_centroidal:
        print "ERROR: Stress report file values are not element-centroidal"
        sys.exit()
    if not values_are_transformed:
        print "ERROR: Stress report file values are not in transformed coordinates"
        sys.exit()

    return stresses


def rptfile_parser_3D(rptfile):
    """
    Goes through an Abaqus .rpt file and grabs all of the stress components,
    creating a series of stress entries (part, elemID, [S11, S22, S33])
    """

    stresses = []
    values_are_centroidal = False

    for line in rptfile:

        # Totally ignore blank lines
        if line.strip() == "":
            continue

        # Check every line to see if the word "Centroidal" pops up, and set our
        # flag to True if it ever does
        if "CENTROIDAL" in line.upper():
            values_are_centroidal = True

        # Figure out when we're in a new part
        if line.upper().startswith("FIELD OUTPUT REPORTED AT"):
            this_part = line.split()[-1]
            continue

        # We only care about lines starting with a number
        if line.strip()[0].isdigit():

            # First, check what kind of file we're in to make sure it's OK
            line_checker(line,4)

            # Then, split up the line and add the data to our stress set
            this_elemID = eval(line.split()[0])
            this_stress = [eval(line.split()[1]),
                           eval(line.split()[2]),
                           eval(line.split()[3])]
            stresses.append((this_part, this_elemID, this_stress))

    # Before proceeding, make sure that the file we just processed was using
    # centroidal values. If not, raise an error and exit.
    if not values_are_centroidal:
        print "ERROR: Stress report file values are not element-centroidal"
        sys.exit()

    return stresses


prestresses_written = False
def inpfile_processor(inpfile, stresses, outfile):
    """
    Goes through an Abaqus .inp file and inserts stresses as an initial
    condition
    """

    # Define the preamble line up front
    preamble = "** PRESTRESSES\n*Initial Conditions, type=stress, unbalanced stress=step\n"

    # Read all of the data into a set
    inpfilelines = inpfile.readlines()

    # Tell the user what's going on, assuming we're in verbose mode
    if verbose_mode:
        print "Creating (or overwriting!) file %s..."%outfilename

    # Go through the inp file. If it's not the section we're looking for (right
    # before the first "STEP" definition), then just copy the line to the new
    # file. If we're in the right place, though, write out the stresses.
    for line in inpfilelines:

        # Check first to see if we're in the right place
        if line.startswith("** STEP"):

            # Write out the first declaration line
            outfile.write(preamble)

            # Go through the stresses and write each of them out - this is
            # different if we're in 3D mode
            if mode.upper() == "FLAT":
                for (part, element, stress) in stresses:
                    outfile.write("%s.%5g, %18G, %18G, %18G\n"%(part,
                                                            element,
                                                            stress,stress,stress))
            elif mode.upper() == "CURVED":
                for (part, element, Srr) in stresses:
                    outfile.write("%s.%5g, %18G, %18G, %18G\n"%(part,
                                                            element,
                                                            Srr,Srr,Srr))
            elif mode.upper() == "THREEDEE":
                for (part, element, [S11, S22, S33]) in stresses:
                    outfile.write("%s.%5g, %11.11e, %11.11e, %11.11e\n"%(part,
                                                            element,
                                                            S11,S22,S33))
            else:
                print "ERROR: Mode not recognized. Specify flat/curved/3D"


            # Dont' forget to write the line we just read ("** STEP: foo")
            outfile.write(line)

        else:
            outfile.write(line)


def line_checker(dataline,num_entries):
    """
    Checks a data line to see if it has the right number of entries. If not, it
    raises an error and quits the program.
    """
    if len(dataline.split()) != num_entries:
        print "ERROR: Please check .rpt file type and contents!"
        sys.exit()


######## Command-line Implementation############################################

if __name__ == "__main__":

    # Start the parser, and define options
    usage = "%prog [options] foo.inp foo.Srpt"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")
    parser.add_option("-f","--flat",action="store_true",
                      dest="flat_mode",default=False,
                      help="use this option if the .rpt file axisymmetric with a flat surface")
    parser.add_option("-c","--curved",action="store_true",
                      dest="curved_mode",default=False,
                      help="use this option if the .rpt file is axisymmetric with a curved surface")
    parser.add_option("-3","--3D",action="store_true",
                      dest="threedee_mode",default=False,
                      help="use this option if the .rpt file is 3D and not axisymmetric")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True
    if options.flat_mode:
        mode = "flat"
    if options.curved_mode:
        mode = "curved"
    if options.threedee_mode:
        mode = "threedee"

    # Process positional arguments. There should be exactly one specified: the
    # .inp file that we're working on
    if len(args) < 2:
        print "ERROR: Please specify a .inp file and a .rpt file"
        sys.exit()
    elif len(args) > 2:
        print "ERROR: More than two files specified. Please specify only one .inp and one .rpt file."
        sys.exit()
    else:
        inpfilename = args[0]
        rptfilename = args[1]

    # Check that we specified the files in the right order!
    if not (rptfilename.upper().endswith("RPT") and
            inpfilename.upper().endswith("INP")):
        print "ERROR: Please specify input file, then report file, in that order"
        sys.exit()

    # Use that filename we grabbed above to open the inp file
    rptfile = open(rptfilename, 'r')
    inpfile = open(inpfilename, 'r')

    # Step up the "iteration" number (i#)
    old_iteration_number = "ERROR"
    next_iteration_number = "ERROR"
    for this_rptfile_tag in rptfile_tags:
        if this_rptfile_tag in inpfilename:
            old_iteration_number = this_rptfile_tag
        if this_rptfile_tag in rptfilename:
            next_iteration_number = outfile_tags[rptfile_tags.index(this_rptfile_tag)]
    if old_iteration_number == "ERROR" or next_iteration_number == "ERROR":
        print "ERROR: Input file does not end with a suffix listed in Options section.\n"+\
              "Program stopped to prevent overwriting original file."
        sys.exit()
    outfilename = re.sub(old_iteration_number,next_iteration_number,inpfilename)

    outfile = open(outfilename, "w")

    # Print out status about the files we're acting on
    if verbose_mode:
        print "Reading files %s and %s..."%(rptfilename, inpfilename)
        print "Processing as a %s model..."%(mode)

    # Run the rpt file parser to get the data we need
    if mode == "flat":
        stresses = rptfile_parser_flat(rptfile)
    elif mode == "curved":
        stresses = rptfile_parser_curved(rptfile)
    elif mode == "threedee":
        stresses = rptfile_parser_3D(rptfile)
    else:
        print "ERROR: Mode not recognized. Please specify flat/curved/3D"

    # Create our new .inp file
    inpfile_processor(inpfile,stresses,outfile)
