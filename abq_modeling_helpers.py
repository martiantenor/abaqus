#!/usr/bin/env python
# A collection of scripts to automate some of the Abaqus modeling process. These
# are meant to be imported into CAE
#
# Contact Dave Blair (dblair@purdue.edu) with questions
#
# (c) David Blair, 2015. This work is licensed under a Creative Commons
# Attribution-ShareAlike Unported License
# (http://creativecommons.org/licenses/by-sa/3.0)

from abaqus import *
from material import *
from section import *

# Define some variables up front that should be global
global current_viewport
current_viewport = session.viewports[session.currentViewportName]


def material_property_assigner(model_name):
    """
    Assigns various properties to the materials in a file.
    """
    #TODO: Expand this to making materials!

    these_materials = mdb.models[model_name].materials.keys()
    creep_table = (4.2e-40,1.0,0.0)

    for this_material in these_materials:
        mdb.models[model_name].materials[this_material].Creep(table=(creep_table, ))


def section_maker(model_name):
    """
    Makes a new solid, homogeneous section for every material that's been
    defined, for a specified model
    """

    this_model = mdb.models[model_name]

    these_materials = this_model.materials.keys()

    for this_material in these_materials:
        this_model.HomogeneousSolidSection(material=this_material,
                                           name="section_%s"%this_material,
                                           thickness=None)


def section_assigner(model_name,part_name):
    """
    Takes specified sets and assigns the appropriate section to each one
    """

    this_model = mdb.models[model_name]
    #this_part = mdb.models[model_name].parts[part_name]
    this_part = this_model.parts[part_name]

    # Grab the names of all the sets and all of the sections, and strip off the
    # "set_" or "section_" that comes before the associated material name,
    # keeping the full, real name in the stored value of the dictionary

    these_sets = this_part.sets.keys()
    these_set_materialnames = {}
    for item in these_sets:
        these_set_materialnames[item.split("_")[-1]] = item

    these_sections = this_model.sections.keys()
    these_section_materialnames = {}
    for item in these_sections:
        these_section_materialnames[item.split("_")[-1]] = item

    # Create a Section Assignment for each set, with the appropriate Section
    for this_set_materialname in these_set_materialnames:

        # Remember the name of the actual set associate with this
        # set_materialname
        this_setname = these_set_materialnames[this_set_materialname]

        # Iterate over section material names, taking action if they match
        for this_section_materialname in these_section_materialnames:
            if this_set_materialname == this_section_materialname:
                this_sectionname = these_section_materialnames[this_section_materialname]
                this_part.SectionAssignment(region=this_part.sets[this_setname],
                                            sectionName=this_sectionname)
            else:
                pass


def thermal_pdf_maker(model_name,part_name):
    """
    Creates a predefined field for every set having "innerpool" or "outerpool"
    in the name. These PDFs don't have the right temperatures assigned, but it's
    a step in the right direction.
    """

    this_model = mdb.models[model_name]
    this_part = this_model.parts[part_name]

    # Set a few variables up top here that might need changing for different
    # models
    applicable_set_names = ["innerpool","outerpool","crust","surfacemelt",
                            "mantleannulus","poolA","poolB","pool"]
    #backup_instance_name = "orientale_axi-1"
    backup_instance_name = "part_merged-1"

    # Grab the instance name automatically if there's only one instanced part,
    # ask the user otherwise (and quit)
    if len(this_model.rootAssembly.instances.keys()) == 1:
        this_instancename = this_model.rootAssembly.instances.keys()[0]
        this_instance = this_model.rootAssembly.instances[this_instancename]
    else:
        if backup_instance_name in this_model.rootAssembly.instances.keys():
            this_instance = this_model.rootAssembly.instances[backup_instance_name]
        else:
            print "ERROR: Please specify an instance name in abq_modeling_helpers that exists in the model!"

    # Find the appropriate set names 
    these_sets = []
    for this_set_name in this_part.sets.keys():
        for matching_name in applicable_set_names:
            if matching_name.upper() in this_set_name.upper():
                name = "pdf_%s"%(this_set_name.split("set_")[-1])
                this_model.Temperature(name,
                                       "Initial",
                                       this_instance.sets[this_set_name],
                                       magnitudes=4242)


def start_material_file(model_name):
    """
    Gets a material file started by writing out column headers and material
    names
    """

    this_model = mdb.models[model_name]

    # Create an output file that shares a "base" name with our model
    outfile_basename = this_model.name.split("_")[0]
    outfilename = "%s_mat_noalpha.txt"%outfile_basename
    outfile = open(outfilename,'w')

    # Write out a line of column headers
    outfile.write("%-15s %-11s %-11s %-11s %-11s %-11s %-11s\n"%("Region",
                    "Depth", "Temp_i", "Dens_i", "Temp_f",
                    "Dens_f", "Alpha_l"))

    # Write out all of the material names in the first column
    for material_name in this_model.materials.keys():
        outfile.write("%-11s\n"%material_name)

    # Finally, close the file so that it's readable!
    outfile.close()


def vertical_point_maker(model_name,part_name,starty,stopy,interval):
    """
    Creates a bunch of points down the left and right sides of the model
    """

    this_model = mdb.models[model_name]
    this_part = this_model.parts[part_name]

    # Keeping x and z constant here
    x = (0, 2e6)
    z = 0

    # Loop over desired x and y values
    y_values = range(starty,stopy,interval)
    for this_x in x:
        for this_y in y_values:
            this_part.DatumPointByCoordinate(coords=(this_x, this_y, z))


def fixfonts():
    """
    Changes the fonts in the current viewport to something readable
    """
    current_viewport.viewportAnnotationOptions.setvalues(
        triadFont='-*-dejavu sans-ultralight-r-normal-*-*-100-*-*-p-*-*-*',
        legendFont='-*-dejavu sans-ultralight-r-normal-*-*-100-*-*-p-*-*-*',
        titleFont='-*-dejavu sans-ultralight-r-normal-*-*-100-*-*-p-*-*-*',)


def make_csys():
    """
    Makes a spherical coordinate system
    """

    current_viewport = session.viewports[session.currentViewportName]
    odb_file = current_viewport.displayedObject
    odb_pathname = os.path.split(odb_file.path)[0]
    odb_filename = os.path.split(odb_file.path)[1].split(".")[0]  #.odb is removed

    scratchOdb = session.ScratchOdb('odb_filename')
    scratchOdb.rootAssembly.DatumCsysByThreePoints(name='CSYS-1', 
        coordSysType=SPHERICAL, origin=(0.0, 0.0, 0.0), point1=(0.0, 1.0, 0.0), 
        point2=(1.0, 0.0, 0.0))
    dtm = session.scratchOdbs['/project/taylor/a/dave/orientale/oriC11c_litho_ps4.odb'].rootAssembly.datumCsyses['CSYS-1']
    session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(
        transformationType=USER_SPECIFIED, datumCsys=dtm)


def make_colors():
    """
    Creates various "spectra" for odb use
    """
    session.Spectrum(name="Blues",
        colors =('#0004C6', '#005DFF', '#21A1FF', '#71EBFF', '#D6FAFF', ))
    session.Spectrum(name="Blues-backwards",
        colors =('#0004C6', '#D6FAFF', '#71EBFF', '#21A1FF', '#005DFF', ))
    session.Spectrum(name="Reds",
        colors =('#F7FFC9', '#FDFF7A', '#FFC54D', '#FF7E01', '#FF0400', ))
    session.Spectrum(name="Reds-backwards",
        colors =('#F7FFC9', '#FF0400', '#FF7E01', '#FFC54D', '#FDFF7A', ))
    session.Spectrum(name="Greens",
        colors =('#3A4B1D', '#688734', '#9CCB4E', '#C7FF7C', '#D9FFC7', ))
    session.Spectrum(name="Greens-backwards",
        colors =('#3A4B1D', '#D9FFC7', '#C7FF7C', '#9CCB4E', '#688734', ))
    session.Spectrum(name="Retro",
        colors =('#0000FF', '#519EFF', '#75D3FF', '#CCFAFF', '#FDFFC0',
        '#FFDD51', '#FF9627', '#FF1300', ))
    session.Spectrum(name="Retro-backwards",
        colors =('#FF1300', '#ff9627', '#ffdd51', '#fdffc0', '#ccfaff',
        '#75d3ff', '#519eff', '#0000ff'))
    session.Spectrum(name="Retro-whitespace",
        colors =('#0000FF', '#519EFF', '#75D3FF', '#FFFFFF', '#FFFFFF',
        '#FFDD51', '#FF9627', '#FF1300', ))


def define_log_scale():
    """
    Sets up a log-based color scale with whitespace
    """
    session.viewports['Viewport: 1'].odbDisplay.contourOptions.setValues(
        spectrum='Retro-whitespace')
    session.viewports['Viewport: 1'].odbDisplay.contourOptions.setValues(
        intervalType=USER_DEFINED, intervalValues=(-0.001, -0.0001, -1e-05, -1e-06,
        0, 1e-06, 1e-05, 0.0001, 0.001, ))

def oriC12d_mesh_colors():
    """
    Pretty colors for printing Orientale meshes
    """
    import section
    import regionToolset
    import displayGroupMdbToolset as dgm
    import part
    import material
    import assembly
    import step
    import interaction
    import load
    import mesh
    import optimization
    import job
    import sketch
    import visualization
    import xyPlot
    import displayGroupOdbToolset as dgo
    import connectorBehavior
    session.viewports[session.currentViewportName].enableMultipleColors()
    session.viewports[session.currentViewportName].setColor(initialColor='#BDBDBD')
    cmap = session.viewports[session.currentViewportName].colorMappings['Material']
    cmap.updateOverrides(overrides={'CRUST000':(True, '#673B0A', 'Default', 
        '#673B0A'), 'CRUST010':(True, '#97570E', 'Default', '#97570E'), 
        'CRUST020': (True, '#CB7512', 'Default', '#CB7512'), 'CRUST030':(True, 
        '#CBB17B', 'Default', '#CBB17B'), 'CRUSTALCAP000':(True, '#ECA730', 
        'Default', '#ECA730'), 'MANTLE030':(True, '#465426', 'Default', 
        '#465426'), 'MANTLE050':(True, '#617434', 'Default', '#617434'), 
        'MANTLE075': (True, '#839D46', 'Default', '#839D46'), 'MANTLE100':(
        True, '#9EBD54', 'Default', '#9EBD54'), 'MANTLE125':(True, '#BEE365', 
        'Default', '#BEE365'), 'MANTLE150':(True, '#99E3A3', 'Default', 
        '#99E3A3'), 'MANTLE175':(True, '#84E3D6', 'Default', '#84E3D6'), 
        'MANTLE200': (True, '#65C0E3', 'Default', '#65C0E3'), 'MANTLE225':(
        True, '#46A8D6', 'Default', '#46A8D6'), 'MANTLE250':(True, '#357EA0', 
        'Default', '#357EA0'), 'MANTLE275':(True, '#003FA0', 'Default', 
        '#003FA0'), 'MANTLE300':(True, '#002D71', 'Default', '#002D71'), 
        'MANTLEANNULUS000': (True, '#EEE8AA', 'Default', '#EEE8AA'), 
        'POOLA000': (True, '#2B0006', 'Default', '#2B0006'), 'POOLA030':(True, 
        '#49000A', 'Default', '#49000A'), 'POOLA050':(True, '#64000E', 
        'Default', '#64000E'), 'POOLA075':(True, '#870014', 'Default', 
        '#870014'), 'POOLA100':(True, '#A80019', 'Default', '#A80019'), 
        'POOLA125': (True, '#C32908', 'Default', '#C32908'), 'POOLA150':(True, 
        '#F62B2F', 'Default', '#F62B2F'), 'POOLA175':(True, '#F6646E', 
        'Default', '#F6646E'), 'POOLA200':(True, '#F66D80', 'Default', 
        '#F66D80'), 'POOLA225':(True, '#F6A3AC', 'Default', '#F6A3AC'), 
        'POOLA250': (True, '#F6C5CA', 'Default', '#F6C5CA'), 'POOLB030':(True, 
        '#461264', 'Default', '#461264'), 'POOLB050':(True, '#5E1887', 
        'Default', '#5E1887'), 'POOLB075':(True, '#7A1FB0', 'Default', 
        '#7A1FB0'), 'POOLB100':(True, '#9225D3', 'Default', '#9225D3'), 
        'POOLB125': (True, '#A455D3', 'Default', '#A455D3'), 'POOLB150':(True, 
        '#BA82D3', 'Default', '#BA82D3'), 'POOLB175':(True, '#C5A8D3', 
        'Default', '#C5A8D3'), 'POOLB200':(True, '#E3CCE9', 'Default', 
        '#E3CCE9'), 'POOLB225':(True, '#E9D8E7', 'Default', '#E9D8E7'), 
        'POOLB250': (True, '#DED8F6', 'Default', '#DED8F6'), 'SPACE':(True, 
        '#6E7B8B', 'Default', '#6E7B8B')})
    session.viewports[session.currentViewportName].setColor(colorMapping=cmap)
    session.viewports[session.currentViewportName].disableMultipleColors()
