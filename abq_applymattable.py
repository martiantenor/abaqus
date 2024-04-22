#!/usr/bin/env python
# A program to insert information from a material table into an Abaqus input
# file
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair. This work is licensed under a Creative Commons 
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from __future__ import division
import sys, re, argparse

__version__ = "2015.01.30"

######## Options ###############################################################

# What suffix is on the incoming file, and what do you want on the newly created
# file?
inp_tag = "_nomat"
out_tag = ""

# What's the name of the assembly in the model?
assembly_name = "master-1"

# What density value do you want to assign to each material? ("initial",
# "final", or "average"; use "initial" except in special or test cases)
mat_density = "initial"

# Are we writing the gravity loads in addition to the material properties?
write_loads = True

# What material density value is fed into the load definitions for the gravity
# routine? ("initial", "final", or "average"; use "final" except in special or
# test cases)
grav_density = "final"

# Is this a geoid model? If so, omit the following set of unit names
geoid_mode = False
forbidden_names = ["POOL", "CAP", "ANNULUS"]



######## Main Program ##########################################################

class Material:
    """
    A container to hold all the information about a material - or at least all
    the information that's stored in the material table!
    """
    def __init__(self, name, depth, Ti, densi, Tf, densf, alpha_l):
        self.name = name
        self.depth = depth
        self.Ti = Ti
        self.densi = densi
        self.Tf = Tf
        self.densf = densf
        self.alpha_l = alpha_l


def mattable_parser(mattable_file):
    """
    Goes through a table of material properties and grabs all of the information
    """

    materials = {}

    # Grab all of the lines from the material table file
    lines = mattable_file.readlines()

    # Ignoring the first line, process the rest:
    for line in lines[1:]:


        values = line.strip().split()
        name = values[0]
        depth = eval(values[1])
        Ti = eval(values[2])
        densi = eval(values[3])
        Tf = eval(values[4])
        densf = eval(values[5])
        alpha_l = eval(values[6])
        materials[name] = Material(name,
                                  depth,
                                  Ti,
                                  densi,
                                  Tf,
                                  densf,
                                  alpha_l)

    return materials


def inpfile_processor(inpfile, materials, outfile):
    """
    Goes through an Abaqus .inp file and inserts material properties where
    needed
    """

    # Read all of the data into a set
    inpfilelines = inpfile.readlines()

    # Go through the inp file. If we run into one of our dummy variables, make
    # the necessary change. Also, as we go through, we'll keep track of what
    # material we're in.
    # Dummy variables are:
    #       4.2e-41 for viscosity
    #       42.42 for density
    #       0.00042 for thermal expansion

    current_material = ""
    for line in inpfilelines:

        # Take note of any material definitions
        if line.upper().startswith("*MATERIAL"):
            current_material = line.split("=")[-1].strip()
            outfile.write(line)
            continue

        # Viscosity dummy variable response
        if line.strip().upper().startswith("4.2E-42"):

            # It's different for the crust vs. other regions:
            # DEPRECATED
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-30,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  1200.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  1201.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-30,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  1200.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  1201.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  2000.\n")
            #continue

            # 3-viscosity setup (ori60km30Ka,b,c,NOT D,e,f
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-30,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-30,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-30,     1.0,    0.,  1100.\n")
            #    outfile.write("    3.0e-26,     1.0,    0.,  1101.\n")
            #    outfile.write("    3.0e-26,     1.0,    0.,  1300.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  1301.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  2000.\n")
            #continue

            # Viscosity setup with gradients: minimum 1e23
            # FIRST USED 2013-05-17 in model ori60km30K
            # Models: ... oriC02, oriC02b
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1100.\n")
            #    outfile.write("    1.0e-27,     1.0,    0.,  1101.\n")
            #    outfile.write("    3.0e-26,     1.0,    0.,  1300.\n")
            #    outfile.write("    1.0e-24,     1.0,    0.,  1350.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  1351.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  2000.\n")
            #continue

            # Mantle & melt: gradients with a minimum of 1e24 Pa.s
            # Crust: Elastic crust
            # Models: oriC02c, oriC03a, oriC04/a/b/c/d/e/f/g, oriC05/a,
            # oriC09b_*_gradientvisco
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1100.\n")
            #    outfile.write("    1.0e-27,     1.0,    0.,  1101.\n")
            #    outfile.write("    3.0e-26,     1.0,    0.,  1300.\n")
            #    outfile.write("    1.0e-24,     1.0,    0.,  1350.\n")
            #    outfile.write("    1.0e-24,     1.0,    0.,  2000.\n")
            #continue

            # Mantle & melt: gradients with a minimum of 1e22 Pa.s
            # Crust: Elastic crust
            # Models: oriC04i/j
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1100.\n")
            #    outfile.write("    1.0e-27,     1.0,    0.,  1101.\n")
            #    outfile.write("    3.0e-26,     1.0,    0.,  1300.\n")
            #    outfile.write("    1.0e-22,     1.0,    0.,  1350.\n")
            #    outfile.write("    1.0e-22,     1.0,    0.,  2000.\n")
            #continue

            # Mantle & melt: new-style single-rollover structure, with the
            #                rollover point = 1250 K
            # Crust: Elastic crust
            # Models: oriC05b
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1250.\n")
            #    outfile.write("    1.0e-22,     1.0,    0.,  1251.\n")
            #    outfile.write("    1.0e-22,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: new-style single-rollover structure, with the
            ##                rollover point = 1100 K
            ## Crust: Elastic crust
            ## Models: oriC05c, oriC06-09
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1100.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  1101.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: new-style single-rollover structure, with the
            ##                rollover point = 1300 K
            ## Crust: Elastic crust
            ## Models: oriC05c
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  1300.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  1301.\n")
            #    outfile.write("    1.0e-23,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: new-style single-rollover structure, with the
            ##                rollover region from 1075-1125 K
            ## Crust: Elastic crust
            ## Models: oriC09c_visco_ps7_1e26Pas, oriF01a-c
            #if "CRUST" in current_material.upper():
            #    outfile.write("    1.0e-40,     1.0,    0.,     0.\n")
            #    outfile.write("    1.0e-40,     1.0,    0.,  2000.\n")
            #else:
            #    outfile.write("    2.5e-41,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-41,     1.0,    0.,  1075.\n")
            #    outfile.write("    2.5e-27,     1.0,    0.,  1125.\n")
            #    outfile.write("    2.5e-27,     1.0,    0.,  3000.\n")
            #continue

            ## Mantle & melt: 2 layers at 1e30 and 1e22 plus transition
            ##                zone; minimum viscosity at > 1280 K;
            ##                transition from 1101-1280 K
            ## Crust: Elastic crust
            ## Models: oriF01d
            #if "CRUST" in current_material.upper():
            #    outfile.write("    2.5e-41,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-40,     1.0,    0.,  9999.\n")
            #else:
            #    outfile.write("    2.5e-31,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-31,     1.0,    0.,  1100.\n")
            #    outfile.write("    2.5e-23,     1.0,    0.,  1280.\n")
            #    outfile.write("    2.5e-23,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: 2 layers at 1e30 and 1e22 plus transition
            ##                zone; minimum viscosity at > 1250 K;
            ##                transition from 1100-1250 K
            ## Crust: Elastic crust
            ## Models: oriF01j, oriF02a, oriF03a
            #if "CRUST" in current_material.upper():
            #    outfile.write("    2.5e-41,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-40,     1.0,    0.,  9999.\n")
            #else:
            #    outfile.write("    2.5e-31,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-31,     1.0,    0.,  1100.\n")
            #    outfile.write("    2.5e-23,     1.0,    0.,  1250.\n")
            #    outfile.write("    2.5e-23,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: 2 layers at 1e30 and 1e22 plus transition
            ##                zone; minimum viscosity at > 1250 K;
            ##                transition from 1100-1250 K
            ## Crust: Elastic crust
            ## Models: oriF03b, oriF03d
            #if "CRUST" in current_material.upper():
            #    outfile.write("    2.5e-41,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-40,     1.0,    0.,  9999.\n")
            #else:
            #    outfile.write("    2.5e-31,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-31,     1.0,    0.,  1100.\n")
            #    outfile.write("    2.5e-24,     1.0,    0.,  1250.\n")
            #    outfile.write("    2.5e-24,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle & melt: 2 layers at 1e30 and 1e22 plus transition
            ##                zone; minimum viscosity at > 1250 K;
            ##                transition from 1100-1250 K
            ## Crust: Elastic crust
            ## Models: oriF03c, oriF03e, oriF04a, oriF04b, oriF05a/b/c,
            ##         oriC10a
            #if "CRUST" in current_material.upper():
            #    outfile.write("    2.5e-41,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-40,     1.0,    0.,  9999.\n")
            #else:
            #    outfile.write("    2.5e-31,     1.0,    0.,     0.\n")
            #    outfile.write("    2.5e-31,     1.0,    0.,  1100.\n")
            #    outfile.write("    2.5e-25,     1.0,    0.,  1250.\n")
            #    outfile.write("    2.5e-25,     1.0,    0.,  9999.\n")
            #continue

            ## Mantle, melt, and crust: 2 layers at 1e30 and 1e24 plus
            ##      transition zone; minimum viscosity at > 800 K;
            ##      transition from 700-800 K
            ## Models: oriC11i, oriC11j, oriC12*
            if True:
                outfile.write("    2.5e-31,     1.0,    0.,     0.\n")
                outfile.write("    2.5e-31,     1.0,    0.,   700.\n")
                outfile.write("    2.5e-25,     1.0,    0.,   800.\n")
                outfile.write("    2.5e-25,     1.0,    0.,  9999.\n")
            continue

        # Material density assignment. Check for a density dummy variable, and
        # replace it with the correct value
        if line.strip().startswith("42.42"):

            # Materials given initial density (normal usage)
            if mat_density == "initial":
                this_density = materials[current_material].densi
            # Materials given final density (special uses only)
            elif mat_density == "final":
                this_density = materials[current_material].densf
            # Materials given average density (special uses only)
            elif mat_density == "average":
                this_density = (materials[current_material].densi +
                               materials[current_material].densf ) / 2.0

            outfile.write("    %f,\n"%this_density)
            continue

        # Expansion dummy variable response
        if line.strip().startswith("0.00042"):
            this_alpha_l = materials[current_material].alpha_l
            outfile.write("    %.12f,\n"%this_alpha_l)
            continue

        # Load section; fill in loads for each material, with the correct
        # densities (average of initial and final density for each section, or
        # initial density, or final density)
        if write_loads:
            if line.strip().endswith("LOADS"):

                #if geoid_mode:
                #    for this_forbidden_name in forbidden_names:
                #        for this_material in materials.keys():
                #            if this_forbidden_name in this_material.upper():
                #                del materials[this_material]

                for material_name in materials.keys():

                    # Check if it's a geoid file, and if move along
                    if geoid_mode:
                        if any(forbidden_name in material_name.upper()
                               for forbidden_name in forbidden_names):
                            continue

                    outfile.write("** Name: %s_grav  Type: Body force\n"%material_name)

                    # Gravity based on final density (best results)
                    if grav_density == "final":
                        this_density = materials[material_name].densf
                        outfile.write("** using material's final density for Fg\n")
                    # Gravity based on average density
                    elif grav_density == "average":
                        this_density = (materials[material_name].densi +
                                        materials[material_name].densf)/2.0
                        outfile.write("** using material's average density for Fg\n")
                    # Gravity based on initial density
                    elif grav_density == "initial":
                        this_density = materials[material_name].densi
                        outfile.write("** using material's initial density for Fg\n")

                    # Write the load
                    outfile.write("*Dload\n")
                    outfile.write("%s.%s, BRNU, %f\n"%(assembly_name, material_name,
                                               this_density))
                    outfile.write("%s.%s, BZNU, %f\n"%(assembly_name, material_name,
                                               this_density))
            outfile.write(line)

        else:
            outfile.write(line)


######## Command-line Implementation############################################

if __name__ == "__main__":

    # Start the parser and define options
    #parser = optparse.OptionParser(usage="%prog inputfile.inp materialfile.txt")
    parser = argparse.ArgumentParser(
        description = ("Apply material table to Abaqus input file"))

    # Add the positional argument for the input file
    parser.add_argument("inp_filename",
        help = "the Abaqus .inp file")

    # Add an "optional" argument for the material table
    parser.add_argument("-m","--mattable_filename", metavar = "FILENAME",
        help = "give the name of the material table file [REQUIRED]")

    # Add a parser argument for selecting which densities to use for the
    # material and load definitions, separately, plus one for whether we're
    # writing the loads at all
    parser.add_argument("-d", "--mat_density", metavar = "STRING",
        help = "Select which density value to use for materials " +\
               "([\"initial\"], \"average\", or \"final\")")
    parser.add_argument("-g", "--grav_density", metavar = "STRING",
        help = "Select which density value to use for load definitions " +\
               "(\"initial\", \"average\", or [\"final\"])")
    parser.add_argument("--writeloads", action = "store_true",
        help = "Write load definitions as well as material properties " +\
               "(necessary for curved models)")

    # Add a parser argument for doing this to geoid files, which automatically
    # omits non-applicable materials
    parser.add_argument("--geoid",
        action = "store_true",
        help = "Run in geoid mode, ommitting melt pool, crustal cap, and "+\
               "mantle annulus units")

    # Run the parser
    #(options, args) = parser.parse_args()
    args = parser.parse_args()

    ## Process the positional arguments. There should be two, one for the input
    ## file and one for the material file
    #if len(args) != 2:
    #    print "ERROR: Please specify two files, an input (.inp) and material table (ASCII) file."
    #else:
    #    inp_filename = sys.argv[1]
    #    mattable_filename = sys.argv[2]

    # Check to make sure a material table filename has been given
    if not args.mattable_filename:
        print "ERROR: Must specify a material file with '-m'"
        sys.exit()

    # Get the filenames
    if args.inp_filename:
        inp_filename = args.inp_filename
    if args.mattable_filename:
        mattable_filename = args.mattable_filename

    # Read in density assignments for materials and load definitions
    if args.mat_density:
        mat_density = args.mat_density
    if args.grav_density:
        grav_density = args.grav_density

    # Check to see if we're writing loads in the first place
    if args.writeloads:
        print "Writing LOAD definitions as well as material properties..."
        write_loads = True

    # Check for geoid mode
    if args.geoid:
        print "Running in geoid model mode..."
        geoid_mode = True

    ## Open the files that correspond to the input and material file names given
    #inp_filename = 
    #out_filename = re.sub(inp_tag,out_tag,inp_filename)
    #inp_file = open(inp_filename,'r')
    #mattable_file = open(mattable_filename,'r')
    #out_file = open(out_filename,'w')

    ## Open the files that correspond to the input and material file names given
    out_filename = re.sub(inp_tag,out_tag,args.inp_filename)
    inp_file = open(inp_filename,'r')
    mattable_file = open(args.mattable_filename,'r')
    out_file = open(out_filename,'w')

    # Print out some info about what's going on
    print "Reading files %s and %s..."%(inp_filename,mattable_filename)
    print "Writing (or overwriting!) file %s..."%out_filename

    # Run the routines defined above on those files
    materials = mattable_parser(mattable_file)

    ###DEBUG
    #print len(materials)
    #for material in materials:
     #print material.name

    # Create the new input file
    inpfile_processor(inp_file, materials, out_file)
