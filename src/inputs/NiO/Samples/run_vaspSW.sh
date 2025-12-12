#!/bin/bash
#SBATCH -p hpc4-el7-3d
#SBATCH -J diff_percent_NiO100         # Job name
#SBATCH -N 1                  # Total number of nodes requested
#SBATCH -n 48                 # Total number of mpi tasks requested
#SBATCH --mem=18G            # Total memory requested

# Launch MPI-based executable

export OMP_NUM_THREADS=1
export MKL_THREADING_LAYER=INTEL

module purge
module load nvhpc/22.7
module load intel-oneApi
module load mkl

mpirun -np 48 /s/ls4/sw/vasp/5.4.4/standard/vasp

echo "vasp script"
echo "1" >> is_vasp_finished.txt
