#!/usr/bin/env python
# A program to add gravity loading to an Abaqus .inp file
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair, 2013. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
import re, sys, optparse
# Note - I'm using the deprecated "optparse" instead of the newer "argparse"
# because Taylor is running Python 2.6, and argparse wasn't introduced until
# Python 2.7

__version__ = "2012.12.18"



######## Options ###############################################################

# Constants
gravity = 1.622 #m.s-2

# File name variables
infile_tag = "_noload"
outfile_tag = ""

# Print lots of stuff while running?
verbose_mode = True


######## Main Program ##########################################################

def inpfile_parser(infile,outfile):
    """
    Goes through an Abaqus .inp file and inserts a new *Dload for gravity in a
    spherical reference frame, based on data it found earlier in the file.
    """

    # Read all of the data into a set
    infilelines = infile.readlines()

    # Go through all of the lines, and take appropriate actions. There is some
    # bit-switching going on here, too, to keep track of what part of the .inp
    # file we're looking at (in the read/write_* variables). The newlines
    # variable holds a complete set of lines for a new output file, with added
    # content inserted where appropriate into lines copied over one-by-one from
    # the original input file.
    read_dens = False       # Behavioral switch for reading densities
    write_load = False      # Behavioral switch for writing out load definitions
    material_densities = {} # Each material, and its density
    set_materials = {}      # Each set, and the material it's made of
    newlines = ""
    for line in infilelines:
        # Always make a[Ma>n exact copy of the line we're on, because this is going
        # to go into the new file verbatim
        #original_lines += line

        # First, see if we're at any of the *KEYWORD lines. These are all in
        # upper-case so that we can parse the file in a case-insensitive way,
        # like Abaqus itself.
        if line.startswith("*"):

            # These keywords contain relevant information about the model,
            # either one-off variables (instance_name) or things that apply to
            # the coming section of the file (this_material)
            if line.upper().startswith("*INSTANCE"):
                instance_name = line.split(",")[1].split("=")[-1]
                newlines += line
                continue
            elif line.upper().startswith("*SOLID SECTION"):
                this_set = line.split(",")[1].split("=")[-1]
                this_set_material = line.split(",")[2].split("=")[-1].strip()
                set_materials[this_set] = this_set_material
                newlines += line
                continue
            elif line.upper().startswith("*MATERIAL, NAME"):
                this_material = line.split("=")[-1].strip()
                newlines += line
                continue

            # If it's a Density declaration, we set a flag so we know to do
            # something with the next line
            elif line.upper().startswith("*DENSITY"):
                read_dens  = True
                write_load = False
                newlines += line
                continue

            # Here, we're going to look for this line, write out a bunch of crap
            # before it, and then write it
            elif line.upper().startswith("** OUTPUT REQUESTS"):
                read_dens  = False
                write_load = True

            # If it's any other keyword (line starting with *X) or comment (**),
            # we're not in a section with defined behavior, so we'll switch off
            # the read/write flags
            else:
                read_dens  = False
                write_load = False

        # For non-*KEYWORD lines, perform behavior based on which section of the
        # file we're in, as determined by the read/write_* flags

        # Read in the density of each material
        if read_dens:
            material_densities[this_material] = eval(line)[0]
            newlines += line

        # Write out the loads, using the sets, sections, and material densities
        elif write_load:

            # Combine the set/material pairings with the material/density
            # pairings to get set/density (this is safe to do, because we're
            # already past all of this information in the file)
            set_densities = {}
            for set in set_materials.keys():
                this_material = set_materials[set]
                set_densities[set] = material_densities[this_material]

            # Start writing out our load declarations, one for each density
            newlines += "** LOADS\n"
            newlines += "**\n"

            # Write out the loads using each unit's original density
            #for this_set in set_densities.keys():
            #    this_density = set_densities[this_set]

            #    # Write in a comment line to make sure this has gone correctly
            #    # Then the load definition: this is for curved models
            #    # Real density values
            #    newlines += "**\n"
            #    newlines += "** MATERIAL: %s, DENSITY: %f\n"%(this_set, this_density)
            #    newlines += "*Dload\n"
            #    newlines += "%s.%s, BRNU, %f\n"%(instance_name,
            #                                      this_set,
            #                                      this_density)
            #    newlines += "%s.%s, BZNU, %f\n"%(instance_name,
            #                                      this_set,
            #                                      this_density)

            # Finish up the load section with a commented-out line, and then
            # add in the "** OUTPUT REQUESTS" marker that we're still
            # holding in "line"
            newlines += "**\n"
            newlines += line

        # If we're not in a keyword section, and nothing else is going on, then
        # just copy the current line over to the new set
        else:
            newlines += line

    # As the output of this function, write all of the lines we've just
    # accumulated, including the copied-over ones, to the output file
    outfile.write(newlines)



######## Command-line Implementation ###########################################

if __name__ == "__main__":

    # Start the parser, and define options
    parser = optparse.OptionParser(usage="%prog [options] foo.inp")
    parser.add_option("-v","--verbose",action="store_true",
                      dest="verbose",default=False,
                      help="print extra information while running")

    # Run the parser, collecting the options and positional arguments
    (options,args) = parser.parse_args()

    # Deal with processing options
    if options.verbose:
        verbose_mode = True

    # Process positional arguments. There should be exactly one specified: the
    # .inp file that we're working on
    if len(args) < 1:
        print "ERROR: Please specify a .inp file"
        sys.exit()
    elif len(args) > 1:
        print "ERROR: More than one file specified. Please specify only one .inp file."
        sys.exit()
    else:
        infilename = args[0]

    # Use that filename we grabbed above to open the inp file, and create and
    # open the output file we're going to write to
    infile = open(infilename, 'r')
    #outfilename = infilename.split(".")[0] + "_withgrav.inp"
    outfilename = re.sub(infile_tag,outfile_tag,infilename)
    outfile = open(outfilename, 'w')

    # Print out status about the files we're acting on
    if verbose_mode:
        print "Reading file %s..."%infilename
        print "Creating (or overwriting!) file %s..."%outfilename

    # Run the processor
    inpfile_parser(infile,outfile)
