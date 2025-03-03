#!/bin/bash
MZN_FILE=$1 # Constraint model to use

# Parameters
CPUS=1
GPU_SMS=32
TOTAL_BANDWIDTH=400
TIMESTEP_RES=2.0
SETUP_TEARDOWN_SCALING=0.05
SOLVER_THREADS=8

# Run model for each SoC config
SOC_CONFIG=hilp_200tdp_"$TOTAL_BANDWIDTH"bw_"$TIMESTEP_RES"ts_"$SETUP_TEARDOWN_SCALING"s_10jobs_"$CPUS"cpus7W_"$GPU_SMS"sms3W_0dsas4cus3W
DZN_FILE=./dzns/$SOC_CONFIG.dzn
../../scripts/run_hilp_model.sh ../../scripts/hilp_model.mzn $DZN_FILE ./output/$SOC_CONFIG.txt $SOLVER_THREADS