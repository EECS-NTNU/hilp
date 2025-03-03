#!/bin/bash
# Launch script for executing a single invokcation of ORTOOLs solver for HILP
# Set this to the path of the Minizinc binary
#MINIZINC=/home/joseph/research/hilp/minizinc_ide/MiniZincIDE-2.8.2-bundle-linux-x86_64/bin/minizinc
MINIZINC=$MINIZINC_HOME/bin/minizinc

MZN_FILE=$1 # Constraint model to use
DZN_FILE=$2 # Input DZN to use
OUTPUT_LOG=$3 # Solver output log
SOLVER_THREADS=$4
# Solve command
$MINIZINC -O1 --solver com.google.ortools.sat $MZN_FILE $DZN_FILE -a -s -v -p $SOLVER_THREADS --params "symmetry_level:3,num_workers:$SOLVER_THREADS" &> $OUTPUT_LOG