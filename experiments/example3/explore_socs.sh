#!/bin/bash
MZN_FILE=$1 # Constraint model to use

# Parameters
CPUS=4
GPU_SMS=64
TIMESTEP_RES=1.0
SETUP_TEARDOWN_SCALING=0.05
SOLVER_THREADS=8

# Run model for each SoC config
for TOTAL_TDP in {40..400..20}
do
    for TIMESTEP_RES in 2.0 0.4 0.08
    do
        SOC_CONFIG=hilp_"$TOTAL_TDP"tdp_800bw_"$TIMESTEP_RES"ts_"$SETUP_TEARDOWN_SCALING"s_10jobs_"$CPUS"cpus7W_"$GPU_SMS"sms3W_10dsas16cus3W
        DZN_FILE=./dzns/$SOC_CONFIG.dzn
        ../../scripts/run_hilp_model.sh ../../scripts/hilp_model.mzn $DZN_FILE ./output/$SOC_CONFIG.txt $SOLVER_THREADS
    done
done