#!/bin/bash
#SBATCH -p hpc4-el7-3d
#SBATCH -J diff_percent_NiO100
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --mem-per-cpu=8G       # например, если vasp требует ~4 GB/ядро
#SBATCH --cpus-per-task=1

# Launch MPI-based executable

export OMP_NUM_THREADS=1
export MKL_THREADING_LAYER=INTEL

module purge
module load nvhpc/22.7
module load intel-oneApi
module load mkl

mpirun -np 1 /s/ls4/sw/vasp/5.4.4/standard/vasp

echo "vasp script"
echo "1" >> is_vasp_finished.txt
