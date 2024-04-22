#!/bin/bash

abqcmd='/project/taylor/a/abaqus/Commands/abaqus'

for thisjob in $@
do
    echo "------------submitting job: $thisjob------------"
    #$abqcmd int job=$thisjob
    $abqcmd int job=$thisjob cpus=8
done

#This will hang if you have other files with the same name, while it waits for
#you to enter Y or N for overwriting those files, so be careful
