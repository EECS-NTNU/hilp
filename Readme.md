# HILP: Accounting for Workload-Level Parallelism in System-on-Chip Design Space Exploration

HILP is an early-stage design space exploration tool for modeling the performance of heterogeneous SoCs while fully accounting for the limits of Workload-Level Parallelism. For more details, please see the full paper.

>@inproceedings{hilp,
  title        = {HILP: Accounting for Workload-Level Parallelism in System-on-Chip Design Space Exploration},
  booktitle    = {Proceedings of the International Symposium on High Performance Computer Architecture (HPCA)},
  author       = {Rogers, Joseph and Eeckhout, Lieven and Jahre, Magnus},
  year         = {2025}
  }

#### Repository Contents
This repository provides the full HILP Minzinc model, as well as the profiled performance data and scripts needed to generate inputs and run the model. To guide users through this process, we provide three example experiments demonstrating each of these steps.

#### Installation
Python requirements:
* numpy
* pandas

Minizinc: To install Minizinc, we recommend downloading one of the official binary packages, available [here](https://www.minizinc.org/downloads/). After Minizinc has been downloaded and extracted, export it's location to a shell variable e.g., `export MINIZINC_HOME=/path_to_minizinc_folder` for integration into HILP's associated scripts.

## Guided Examples
In this section we present several examples of how to use HILP at varying levels of SoC complexity. These examples are meant to demonstrate HILP's core functionality, and then be adapted to the user's own needs.

To begin, export HILP's location to a shell variable
`export HILP_HOME=/path_to_your_hilp_folder`

The starting point for each example is its corresponding data generation script e.g., `./scripts/example1_generate_dzns.sh`. In these scripts, the user may configure the desired SoC, as well as the resource constraints it operates under. Various other parameters for things such as controlling the workload are available as well. Executing one of these scripts generates the DZN input files necessary to run the HILP ILP model. For convenience, these are automatically exported to a corresponding folder for each example e.g., `./experiments/example1/dzns`. 

### Example 1: HILP Hello World (Minimalistic SoC).
This example is designed to verify that HILP has been installed correctly, and that all aspects of it's toolchain function as intended. Running this example requires a relatively small amount of compute and memory resources, and should solve to a 0.9 optimality gap after several minutes on an average laptop.

##### Step 1, create input data:
`cd scripts`
`./example1_generate_dzns.sh`
Running the generate dzns script invokes several python scripts, which sample the profiled CPU and GPU data located in the "rodinia_profiled_data" folder, and use them to create the necessary input matrices used by the HILP model.

##### Step 2, run HILP!:
`cd ../experiments/example1`
`./explore_socs.sh`
The "explore_socs.sh" script uses the export DZN files, along with the Minizinc executable to invoke the HILP ILP model and send it to the Ortools solver. Solver outputs are written real-time to the `ouputs` folder, and can be monitored with standard tools such as `watch` and `tail`. By default, solver output is highly verbose, as this makes it easier to monitor and debug the solving process. Whenever a new solution is found, it is prefaced with the string "Start Workload Schedule
". What then follows is a full print detailing the specifics of how the workload was successfully scheduled on the SoC. Note: HILP variables names and solver prints are done using typical JSSP terminology. Please note as well that Minizinc uses 1, not 0 indexing.

Typical output snippit.
>Start Workload Schedule
job,task,machine,start_time,duration,bandwidth,power
1,1,1,1,2,1,8
1,2,2,3,1,70,22
1,3,1,4,1,10,8
2,1,1,0,1,205,9
2,2,12,2,1,9,50
2,3,1,3,1,1,8
3,1,1,5,1,1,8
3,2,3,6,1,26,23
3,3,1,7,2,1,8
4,1,1,9,2,1,8
4,2,11,11,1,85,46
4,3,1,12,2,1,8
5,1,1,6,1,1,8
5,2,9,7,1,2,41
5,3,1,11,1,4,8
6,1,1,14,1,1,8
6,2,4,15,2,61,25
6,3,1,17,1,10,8
7,1,1,15,1,1,8
7,2,5,17,1,1,28
7,3,1,18,1,2,8
8,1,1,16,1,205,9
8,2,6,18,1,321,33
8,3,1,19,1,6,8
9,1,1,20,2,1,8
9,2,7,22,1,109,34
9,3,1,23,1,4,8
10,1,1,22,1,1,8
10,2,2,23,1,222,23
10,3,1,24,1,205,9
End Workload Schedule
Makespan: 25

Each sequence of numbers in the above output snippit represents how each workload phase (task), for each application (job), was executed on each SoC component (machine). For example, the first line "1,1,1,1,2,1,8" says that phase 1 of application 1 executed on SoC component 1. It started at time 1, ran for 2 time steps, used 1GB/s of memory bandwidth, and 8 Watts of power. The full makespan of the schedule "25" is printed at the bottom after the end of the phase schedule.

Between prints of newly found solutions, the solver will occasionally print out status updates when it tightens the optimality bounds.
>%% #Bound  14.41s best:25    next:[18,24]    reduced_costs

The above print means that the best found solution still only has a makespan of 25, and that only the gap between 18 to 24 remains unexplored. These numbers can also be used to calculate the current optimality gap e.g., 18/24 = 0.75.

As explained in the paper, it can happen that solving fully to optimalities of 1.0 can extreme amounts of compute, without yielding any useful design insights. We therefore advise to use a timer when invoking the solver, e.g., `timeout 4h` to gather initial results, and then analyze whether or not it makes sense to continue.


### Example 2: Bandwidth Limiting a GPU (CPUs and GPU SoC).
This example shows how to sweep the memory bandwidth constraint and view its effects on a SoC comprising both CPUs and GPUs. We reccommend using a system with 32GB of RAM to run this example. Expect execution to a 0.9 optimality gap to take several hours.

### Example 3: Power Efficiency (Complex Heterogeneous SoC).
This example sweeps the power limit constraint and gathers data about how it affects performance of a complex SoC comprising CPUs, a GPU, and many DSAs. It additionally uses adaptive timestep resolutions, as described in the full paper. We recommend this to be executed on a cluster computer, with nodes equipped with at least 256GB of RAM. Expect execution to a 0.9 optimality gap take several hours per SoC design point.


## Other
For questions or comments regaurding this repository, or HILP in general, please get in touch!