#!/bin/bash

codedir="/project/taylor/a/dave/Dropbox/Code/bin"
#codedir="/Users/Dave/Code/bin"

#geoidmodel="oriF01/oriF01b_geoid_ps2"
#geoidmodel="oriC10a_geoid"
#geoidmodel="oriC11b_geoid"
geoidmodel="oriC11/oriC11c_geoid"

# Get command-line arguments as input filenames
#models[0]="$1"
models=$@


# Define functions for easier re-use
run_geoid_acceleration_curved () {
    $codedir/grav_anomaly.py -n 51 --GMT --curved --acceleration "$geoidmodel".grav
}
run_geoid_acceleration_flat () {
    $codedir/grav_anomaly.py -n 51 --GMT --acceleration "$geoidmodel".grav
}

run_freeair_curved () {
    $codedir/grav_anomaly.py -n 51 --GMT --curved --geoidname "$geoidmodel"_acc.xy --freeair "$model"_ff.grav
    $codedir/grav_anomaly.py -n 51 --GMT --curved --geoidname "$geoidmodel"_acc.xy --freeair "$model".grav
}
run_freeair_flat () {
    $codedir/grav_anomaly.py -n 51 --GMT --geoidname "$geoidmodel"_acc.xy --freeair "$model"_ff.grav
    $codedir/grav_anomaly.py -n 51 --GMT --geoidname "$geoidmodel"_acc.xy --freeair "$model".grav
}

run_bouguer_curved () {
    $codedir/grav_anomaly.py -n 51 --GMT --curved --geoidname "$geoidmodel"_acc.xy --bouguer "$model"_ff.grav
    $codedir/grav_anomaly.py -n 51 --GMT --curved --geoidname "$geoidmodel"_acc.xy --bouguer "$model".grav
}
run_bouguer_flat () {
    $codedir/grav_anomaly.py -n 51 --GMT --geoidname "$geoidmodel"_acc.xy --bouguer "$model"_ff.grav
    $codedir/grav_anomaly.py -n 51 --GMT --geoidname "$geoidmodel"_acc.xy --bouguer "$model".grav
}

run_topo_curved () {
    $codedir/plot_surface_curved.gmt.py "$model"_ff.SURFACErpt
    $codedir/plot_surface_curved.gmt.py "$model".SURFACErpt
}
run_topo_flat () {
    $codedir/plot_surface.gmt.py "$model"_ff.SURFACErpt
    $codedir/plot_surface.gmt.py "$model".SURFACErpt
}

run_crust_curved () {
    $codedir/plot_crustalthickness.gmt.py --curved "$model".MOHOrpt "$model".SURFACErpt
}
run_crust_flat () {
    $codedir/plot_crustalthickness.gmt.py "$model".MOHOrpt "$model".SURFACErpt
}



# Loop over supplied model names
for model in $models; do

    # Curved models:
    #run_geoid_acceleration_curved
    run_freeair_curved
    run_bouguer_curved
    run_topo_curved
    run_crust_curved

    # Flat models:
    #run_geoid_acceleration_flat
    #run_freeair_flat
    #run_bouguer_flat
    #run_topo_flat
    #run_crust_flat

    # Plot
    $codedir/moon-4xy-horiz.gmt.sh $model &

    # Backup to Dropbox
    sleep 10
    cp $model*{xy,csv,pdf} /project/taylor/a/dave/Dropbox/
done
