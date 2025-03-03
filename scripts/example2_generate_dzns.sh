#!/bin/bash
# Remember, this script needs an appropritate python env activated to work!
###########################################################
# Default ARGS for workload csv generation (change as desired)
###########################################################
# Num CPUs in the SoC
CPUS=4
# Num GPU SMs in the SoC
GPU_SMS=64
# Num DSAs in the SoC
DSAS=0
# Num compute units in each DSA
DSA_CUS=4
# Watts per CPU core
CPU_TDP=7
# Watts per GPU SM
GPU_SM_TDP=3
# Watts per DSA CU
DSA_CU_TDP=3
# DSA Perf. Advantage vs GPU at same power/area
DSA_SPEEDUP=4 
# Number of times to duplicate each benchmark in the workload (default 0)(makes more work for the SoC if desired)
N_DUPS=0
# Location to export tmp csvs used in DZN generation
CSV_OUTPUT=$HILP_HOME/experiments/example2/csvs/
# Location of profiled CPU data for each benchmark
CPU_DATA=$HILP_HOME/rodinia_profiled_data/cpu_data.csv
# Location of profiled GPU data for each benchmark
GPU_DATA=$HILP_HOME/rodinia_profiled_data/gpu_data.csv
# Timestep resolution of the model in seconds.
TIMESTEP_RES=1.0 # Must best specified as float (e.g., 1.0 not 1)
# Number of unique benchmarks/applications in the workload
N_JOBS=10
# Amount to squash setup and teardown phase times to reduce Amdahl effects.
SETUP_TEARDOWN_SCALING=0.05


###########################################################
# ARGS for converting workload csv to DZN
###########################################################
# DZN output folder
DZN_FOLDER=$HILP_HOME/experiments/example2/dzns
# Max power usage of the SoC (W)
TOTAL_TDP=200
# Max total bandwidth of the SoC (GB/s)
TOTAL_BANDWIDTH=400
# WIP, Max total memory of the SoC (GB)
TOTAL_MEMORY=64
# Max makespan for the solver to consider
MAX_MAKESPAN=200
# Min makespan for the solver to consider
MIN_MAKESPAN=10
# Whether or not to enforce shared global resource constraints (1 on, 0 off).
RESOURCE_CONSTRAINTS=1
# Energy usage of DRAM transfers (pJ/bit)
EXT_MEM_ENERGY=7

###########################################################
# Example 2: Generate SoCs to explore bandwidth limits on GPUs
###########################################################
# Clean out the CSV and DZN folder
rm $CSV_OUTPUT/*.csv
rm $DZN_FOLDER/*.dzn
# Change parameters to create different SoC configs to see how performance changes.
for TOTAL_BANDWIDTH in {50..400..50}
do
        # Combine all CSV args together
        GEN_ARGS="$CPUS $GPU_SMS $DSAS $DSA_CUS $CPU_TDP $GPU_SM_TDP $DSA_CU_TDP $DSA_SPEEDUP $N_DUPS $CSV_OUTPUT $CPU_DATA $GPU_DATA $TIMESTEP_RES $N_JOBS $SETUP_TEARDOWN_SCALING"
        # Generate workload CSV
        python $HILP_HOME/scripts/generate_workload.py $GEN_ARGS
        # Grab workload CSV path
        INPUT=$CSV_OUTPUT/"$TIMESTEP_RES"ts_"$SETUP_TEARDOWN_SCALING"s_"$N_JOBS"jobs_"$CPUS"cpus"$CPU_TDP"W_"$GPU_SMS"sms"$GPU_SM_TDP"W_"$DSAS"dsas"$DSA_CUS"cus"$DSA_CU_TDP"W.csv
        # Setup output path for DZN
        OUTPUT=$DZN_FOLDER/hilp_"$TOTAL_TDP"tdp_"$TOTAL_BANDWIDTH"bw_"$TIMESTEP_RES"ts_"$SETUP_TEARDOWN_SCALING"s_"$N_JOBS"jobs_"$CPUS"cpus"$CPU_TDP"W_"$GPU_SMS"sms"$GPU_SM_TDP"W_"$DSAS"dsas"$DSA_CUS"cus"$DSA_CU_TDP"W.dzn
        # Export DZN for use with HILP Minizinc model
        EXPORT_ARGS="$INPUT $OUTPUT $TOTAL_TDP $TOTAL_BANDWIDTH $TOTAL_MEMORY $MAX_MAKESPAN $MIN_MAKESPAN $CPUS $RESOURCE_CONSTRAINTS $EXT_MEM_ENERGY $GPU_DATA $TIMESTEP_RES"
        python $HILP_HOME/scripts/export_minizinc_model_data.py $EXPORT_ARGS
done