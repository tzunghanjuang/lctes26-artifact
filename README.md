# Artifact for LCTES '26

This repository provides a Docker image and evaluation for a LCTES '26 paper *Artifact for A Functional Approach to Synthesizing Routable Programmable Accelerators.*

The paper presents a functional programming–based approach for expressing synthesizable, runtime-programmable hardware accelerators. It supports dynamic shapes and instruction-like control, significantly reducing routing congestion in applications such as neural networks.
The approach is based on SHIR compiler pipeline and Intel FPGA toolchains.

The Docker image in this artifact reproduces the paper's main results, which are found in Table 2.
Generated VHDL code for all experiments are written to the local `results/` directory for evaluation.

## Folder Structure
```
LCTES26-ARTIFACT
├── scripts             # Scripts for reproducing results
│   ├── figures         # Python scripts for producing figures 15 and s16
│   ├── scores          # Scripts for print performance and resource numbers in Table 2
│   └── profile         # Sample enviroment setup for FPGA
├── Dockerfile          
├── evaluation.py       # Main experiment script
└── README.md           # Documentation
```

``scripts/tables`` prints out performance (Lat., GOP/s, GOP/cycle, and DSP eff.) and resource (ALMs, DSPs, and routing congestions) numbers after synthesis and runtime execution. 
``scripts/syntest`` and  ``scripts/profile`` are required to setup Quartus tool chain environment and perform synthesis jobs.
After that uses will need to run the FPGA bitstream before collecting performance numbers.

## Step-By-Step Instructions (Table 2)

The steps below walk you through the complete workflow for evaluating SkeleShare using our Docker image and server setup.
You'll connect to the server, pull the artifact's Docker container, generate VHDL for all experiments, and run the pre-synthesized designs on the provided Arria-10 FPGA.


### 1. Access the server 

This artifact is supposed to run with Intel Arria 10 PAC.
This step is tailored for the artifact evaluators to execute the experiments on the device. 

Therefore We have created temporary institutional server accounts for evaluation and their private SSH keys has been to the LCTES AE chairs. As an evaluator, you will receive one private key along with a username in the format `csuser<NUM>`.

**I. Add the SSH key to your local machine**
```bash
ssh-add path/to/private-key
```

**II. Connect to our server via the institutional jump host**
```bash
ssh -A -J your-username@jump.cs.mcgill.ca your-username@solaire.cs.mcgill.ca
```
Once connected, you will have access to Intel Arria 10 PAC connected via PCI-Express on the server.

### 2. Pull the Docker image
The docker image can be accessed from Github or Zenodo.

From Github:
```bash
docker pull ghcr.io/tzunghanjuang/lctes26-artifact:latest
```

From Zenodo:
```bash
wget https://zenodo.org/records/17925912/files/lctes26-artifact_image.zip
unzip ./lctes26-artifact_image.zip
docker load -i ./lctes26-artifact.tar
```

### 3. Run the container with mounted results

Create a local results directory and mount it into the container so that all outputs are available on your host machine:

```bash
mkdir -p results
docker run --rm -it \
  --mount type=bind,src=./results,dst=/workspace/results \
  ghcr.io/tzunghanjuang/lctes26-artifact:latest
```

Running the container invokes the evaluation script, which generates a VHDL design for each experiment where equality saturation produces a valid solution. 
The resulting VHDL for each experiment is stored in:

```
./results/<experiment-id>/lowering/
```
After running the container, the script folder is created that contains the hardware wrapper and the required environment setup files for synthesis.
```
./results/scripts
```

Before moving to the next step, please run the following command to confirm that the script directory is correctly set and reachable. The output of ``echo $SCRIPTDIR`` should be the absolute path to the ``scripts`` folder:
```
export SCRIPTDIR=$(pwd)/results/scripts
echo $SCRIPTDIR
```

#### 3.1 Run each test independently
Run the following command to execute the experimental options listed above:

```bash
docker run --rm -it \
  --mount type=bind,src=./results,dst=/workspace/results \
  ghcr.io/jonathanvdc/skeleshare-cgo26-artifact:latest \
  python3 evaluation.py --only <experiment-id>
```

These experiment IDs are:

- `expt-1`
- `expt-2`
- `expt-3`
- `expt-4`
- `expt-5`
- `expt-6`
- `expt-7`

### 4. Running synthesized designs

Because synthesis typically takes **4–8 hours per benchmark** in the paper, we provide pre-synthesized designs that correspond exactly to the VHDL generated for each experiment. 

The pre-synthesized design can be downloaded from zenodo. The experiments will be located in the ``precomputed`` folder after unzipping the file.
```bash
wget https://zenodo.org/records/17925912/files/precomputed.zip
unzip precomputed.zip
```

The unzipped pre-synthesized design may have permission issue. Please run the following command to update the permission.
```bash
chmod -R 777 ./precomputed
```

Inside each experiment (folder ``./precomputed/<experiment-id>``), the software runtime for each experiment might also need to be updated due to different compiling environment.
```bash
cd ./sw
cmake .
make clean
make
cd ..
```

To run an experiment using its pre-synthesized hardware design on the FPGA board, go to the corresponding experiment directory and execute the following commands:

```bash
source $SCRIPTDIR/profile
./real_start.sh
./real_sw.sh
```

### 5. Results

Finally, run the following script to summarize the logic, RAM, and DSP utilization, along with the GOPS measurements collected in the previous step.

```bash
bash $SCRIPTDIR/scores/<experiment-id>.sh
```

A full list of experiment IDs is defined in `evaluation.py` and corresponds to the experiments in the artifact appendix.
These experiment IDs are:

- `expt-1`
- `expt-2`
- `expt-3`
- `expt-4`
- `expt-5`
- `expt-6`
- `expt-7`

The output adheres to the following format and can be directly cross-referenced with Table 2 in the paper.

```
Logic utilization (in ALMs) : 207,520 / 427,200 ( 49 % )
Total RAM Blocks : 943 / 2,713 ( 35 % )
Total DSP Blocks : 1,152 / 1,518 ( 76 % )
GOP/s : 169.936
```


## Plotting Figures 15 and 16

To reproduce Figures 15 and 17, run the following commands to draw the figures with pre-computed data points:

```bash
docker run --rm -it \
  --mount type=bind,src=./results,dst=/workspace/results \
  ghcr.io/tzunghanjuang/lctes26-artifact:latest \
  python3 figures/draw.py
```

The generated figures will be `results/rooflines.pdf` for figure 15 and `results/vgg16_runtime.pdf` for figure 16
