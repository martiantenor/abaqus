#!/bin/bash

# Cleans up files from an Abaqus run that involves gravity file production.
# Don't run this until you've made a PDF of the results (although it's
# reversible if you make a mistake)

echo "archiving run files (com, dat, ipm, log, msg, sim, sta)..."
tar -czvf runfiles.tar.gz *.{com,dat,log,msg,sim,sta}

echo "deleting un-archived copies..."
rm -rf *.{com,dat,ipm,log,msg,sim,sta,lck}

echo "archiving gravity calculation products (xy, csv, grav)..."
tar -czvf grav_anomaly_files.tar.gz *.{xy,csv,grav}

echo "deleting un-archived copies..."
rm -rf *.{xy,csv,grav}
