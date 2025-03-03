int: n_jobs; % Number of jobs
int: n_tasks; % Number of tasks in each job
int: n_machines; % Number of machines
int: total_bandwidth; % Total shared bandwidth available
int: total_power; % Total shared system power available
int: total_memory; % Total shared memory available
int: MAX_MAKESPAN;
int: MIN_MAKESPAN;
int: total_cpus;
int: total_gpus;

array[1..n_jobs,1..n_machines,1..n_tasks] of int: task_duration_per_machine;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: task_bandwidth_per_machine;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: task_power_per_machine;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: task_compatibility_per_machine;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: task_memory_per_machine;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: cpus_used_per_task;
array[1..n_jobs,1..n_machines,1..n_tasks] of int: gpus_used_per_task;


% Variables
array[1..n_jobs, 1..n_tasks] of var 1..n_machines: task_machine; % Machine on which task is run
array[1..n_jobs, 1..n_tasks] of var 0..sum([task_duration_per_machine[i,j,k] | i in 1..n_jobs, j in 1..n_machines, k in 1..n_tasks]): task_start_time; % Start time of task

% Functions
function var int: task_end_time(int: i, int: j) = task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j];

% Objective
var int: makespan = max(i in 1..n_jobs, j in 1..n_tasks)(task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j]);
solve minimize makespan;

% Constraints
% Ensure that no two tasks are scheduled at the same time on the same machine
constraint forall(i in 1..n_jobs, k in 1..n_tasks, j in i+1..n_jobs, l in 1..n_tasks) (
  (task_machine[i,k] = task_machine[j,l]) -> 
  ((task_start_time[i,k] + task_duration_per_machine[i,task_machine[i,k],k] <= task_start_time[j,l]) \/ 
  (task_start_time[j,l] + task_duration_per_machine[j,task_machine[j,l],l] <= task_start_time[i,k]))
);

% Ensure that tasks only run on machines that they are compatible with
constraint forall(i in 1..n_jobs, j in 1..n_tasks) (
  task_compatibility_per_machine[i,task_machine[i,j],j] = 1
);

var set of int: relevant_times = {task_start_time[i,j] | i in 1..n_jobs, j in 1..n_tasks} union 
    {task_start_time[i,j] + task_duration_per_machine[i, task_machine[i,j], j] | 
    i in 1..n_jobs, j in 1..n_tasks};

%% BANDWIDTH %%
constraint forall(t in relevant_times) (
  sum(i in 1..n_jobs, j in 1..n_tasks) (
    if t >= task_start_time[i,j] /\ t <
        task_start_time[i,j] + task_duration_per_machine[i, task_machine[i,j], j] then task_bandwidth_per_machine[i, task_machine[i,j], j] else 0 endif
  ) <= total_bandwidth
);

%% POWER %%
constraint forall(t in relevant_times) (
  sum(i in 1..n_jobs, j in 1..n_tasks) (
    if t >= task_start_time[i,j] /\ t <
        task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j] then task_power_per_machine[i,task_machine[i,j],j] else 0 endif
  ) <= total_power
);

%% Active CPUs %%
% This makes sure that when a kernel is executing on the cpu that no setup or teardown can occur
constraint forall(t in relevant_times) (
  sum(i in 1..n_jobs, j in 1..n_tasks) (
    if t >= task_start_time[i,j] /\ t <
        task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j] then cpus_used_per_task[i,task_machine[i,j],j] else 0 endif
  ) <= total_cpus
);

%% Active GPUs %%
% This makes sure that of all of the available GPU configs, only 1 executes at a time.
constraint forall(t in relevant_times) (
  sum(i in 1..n_jobs, j in 1..n_tasks) (
    if t >= task_start_time[i,j] /\ t <
        task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j] then gpus_used_per_task[i,task_machine[i,j],j] else 0 endif
  ) <= total_gpus
);

% This version of memory footprint constrait keeps task memory around during gaps to the next task.
%% MEMORY %%
% constraint forall(t in 0..MAX_MAKESPAN) (
%     sum(i in 1..n_jobs, j in 1..n_tasks) (
%         if (j < n_tasks /\ t >= task_start_time[i,j] /\ t < task_start_time[i,j+1]) \/ 
%            (j == n_tasks /\ t >= task_start_time[i,j] /\ t < task_end_time(i, j)) then
%             task_memory_per_machine[i,task_machine[i,j],j]
%         else 0 endif
%     ) <= total_memory
% );

%% This version allows gaps between tasks %%
% Tasks within a job must be scheduled sequentially
constraint forall(i in 1..n_jobs, j in 1..n_tasks-1) (
  task_start_time[i,j] + task_duration_per_machine[i,task_machine[i,j],j] <= task_start_time[i,j+1]
);
%% This version DOES NOT allow gaps between tasks %%
% Tasks within a job must be scheduled sequentially
%constraint forall(i in 1..n_jobs, j in 1..n_tasks-1) (
%  task_start_time[i,j] + task_duration_per_machine[i,j,task_machine[i,j]] = task_start_time[i,j+1]
%);

% Symmetry Constraints
% A job must start at time 0
constraint exists(i in 1..n_jobs, j in 1..n_tasks) (task_start_time[i,j] = 0);
constraint makespan <= MAX_MAKESPAN;
constraint makespan >= MIN_MAKESPAN;


output ["Start Workload Schedule\n"];
output ["job,task,machine,start_time,duration,bandwidth,power\n"];
output ["\(i),\(j),\(task_machine[i,j]),\(task_start_time[i,j]),\(task_duration_per_machine[i,task_machine[i,j],j]),\(task_bandwidth_per_machine[i,task_machine[i,j],j]),\(task_power_per_machine[i,task_machine[i,j],j])\n" | i in 1..n_jobs, j in 1..n_tasks];
output ["End Workload Schedule\n"];
output ["Makespan: \(makespan)\n" ];
