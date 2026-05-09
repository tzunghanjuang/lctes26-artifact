# Artifact for LCTES '26 Paper #99

This repository provides a Docker image and evaluation for a LCTES '26 paper *Artifact for A Functional Approach to Synthesizing Routable Programmable Accelerators.*

The paper presents a functional programming–based approach for expressing synthesizable, runtime-programmable hardware accelerators. It supports dynamic shapes and instruction-like control, significantly reducing routing congestion in applications such as neural networks.
The approach is based on SHIR compiler pipeline and Intel FPGA toolchains.

## Getting Started Guide
**Warning:** Note that this artifact requires the Intel Quartus tool chain, which is not included in the artifact due to license and copyright issue. For artifact evaluators, we have provided a evaluation server's ssh keys to the AE chairs. 

### 1. Reference Server Setup
**Hardware:** A dual-socket Intel Xeon Gold 6254 server, an Intel Programmable Accelerator Card with Arria 10 GX1150 FPGA connected to the host server via PCI-Express.

**Software:** Docker version 26.1.4 builds, RHEL 7.6, Intel Quartus Prime Pro V19.2, Intel FPGA OPAE SDK V1.3.0, Intel Acceleration Stack for Intel Arria 10 V1.2.1

### 2. Access the Server (Artifact Evaluators Only)

This artifact is supposed to run with Intel Arria 10 PAC.
This step is tailored for the artifact evaluators to execute the experiments on the device. 

Therefore We have created temporary institutional server accounts for evaluation and their private SSH keys has been to the LCTES AE chairs. As an evaluator, you will receive one private key along with a username in the format `csuser<NUM>`.

**I. Add the SSH key to your local machine**
```bash
ssh-add path/to/private-key
```

**II. Connect to our server via the institutional jump host**
```bash
ssh -A -Y -J your-username@jump.cs.mcgill.ca your-username@solaire.cs.mcgill.ca
```
Once connected, you will have access to Intel Arria 10 PAC connected via PCI-Express on the server.

### 3. Acceess the Artifact
The artifact can be downloaded from Zenodo ``zenodo.org/records/20046007`` with the following command.
The entire artifact has more than 10 GB so it might takes several minutes to download.
```bash
wget https://zenodo.org/records/20046007/files/99.zip
```

After downloading the artifact, please unzip it and enter the unzipped directory. In this artifact, we sticks to the base folder ``99/``.
```bash
unzip 99.zip 
cd 99
```

In the directory, please run the following commands to unzip the inner files.
```bash
unzip data.zip 
tar -xvzf pre_synthesis_cleaned.tar.gz
tar -xvzf venv.tar.gz
unzip ./lctes26-artifact_image.zip
```

**Please make sure to set current folder (/path/to/99) as the `BASEDIR`.**
``` bash
export BASEDIR="$(pwd)"
```

### 4. Folder Structure
After unzipping the files in the previous sectiond the folder structure is as follows:
```
99
├── data                   # Data and weights for accelerators
├── driver                 # FPGA driver
├── pre_synthesis_cleaned  # FPGA wrappers with pre-synthesized bitstreams
├── scores                 # Shell scripts to print the results for Table 2
├── src                    # Main Python scripts
├── tests                  # Experiment scripts
├── tmp                    # Pre-computed results and scripts
├── venv                   # Python virtual environment
├── profile                # FPGA tool chain setup script
├── pyproject.toml         # Local Python package setup
├── requirements.txt       # Python package list 
└── lctes26-docker.tar     # Docker immage for the compiler infrastructure
```

The Docker image ``lctes26-docker.zip`` in this artifact reproduces the paper's accelerator HDL files, which are required for Table 2.
Generated VHDL code for all experiments are written to the local `results/` directory for evaluation. The generated VHDL will synthesized into FPGA bitstreams via Intel Quartus tool chain. 

The virtual environment ``venv`` are required to run the pytorch interface to execute the models on generated accelerators.

## Step-By-Step Instructions (Table 2)

The steps below walk you through the complete workflow for evaluating using our Docker image and Python virtual evironment.

In this artifact, we sticks to the ``BASEDIR`` in ``99/``. Please run the following command to check if the setup is correct. It will print out a path ending with ``99``.
```bash
echo $BASEDIR
```


### 1. Load the Docker image
The docker image can be loaded with the folling command.

```bash
sudo docker load -i $BASEDIR/lctes26-artifact.tar
```

### 2. Run the container with mounted results

Create a local results directory and mount it into the container so that all outputs are available on your host machine. Note that this step only covers the experiements from this paper. The entire processing time for this step will be 15-20 minutes.

```bash
mkdir -p results
sudo docker run --rm -it \
  --mount type=bind,src=$BASEDIR/results,dst=/workspace/results \
  ghcr.io/tzunghanjuang/lctes26-artifact:latest
```

Running the container invokes the evaluation script, which generates a VHDL design for each experiment where equality saturation produces a valid solution. 
The resulting VHDL for each experiment is stored in:

```
$BASEDIR/results/<experiment-id>/lowering/
```


#### 3.1 Run each test independently
Run the following command to execute the experimental options listed below:

```bash
sudo docker run --rm -it \
  --mount type=bind,src=$BASEDIR/results,dst=/workspace/results \
  ghcr.io/tzunghanjuang/lctes26-artifact:latest \
  python3 evaluation.py --only <experiment-id>
```

These experiment IDs are:

- `expt-3`
- `expt-4`
- `expt-6`
- `expt-8`
- `expt-9`
- `expt-10`
- `expt-11`

### 4. Running Synthesized Designs

#### 4.1 Environment Setup 

Some experiments require PyTorch packages. Please use the following command to setup Python environment
```bash
export PREDIR=$(realpath "$BASEDIR/..")
sed -i "s#/home/pteng#${PREDIR}#g" $BASEDIR/venv/bin/*
source $BASEDIR/venv/bin/activate
pip install --editable $BASEDIR
```

Please follow the instruction below to set up the the access to Intel Quartus tools and the FPGA driver.
```bash
source $BASEDIR/profile
``` 

#### 4.2 Synthsize FPGA Bitstreams (Optional)

**Warning:** Each synthesis job typically takes **6–10 hours** with Intel Quartus tool chain. We provide pre-synthesized designs that correspond exactly to the VHDL generated for each experiment. Please skip this section and move to 4.3 if long synthsis time is a concern.

After the step 3, the generated VHDL files should be located in the ``results`` folder. The next step is to copy them to the synthesis folder `pre_synthesis_cleaned` with the following commands;
```bash
bash $BASEDIR/scores/copy-<experiment-id>.sh
```

The available options are:
- `expt-3`
- `expt-4`
- `expt-6`
- `expt-8`
- `expt-9`
- `expt-10`
- `expt-11`

After the above step, the generated VHDL files will replace the existing pre-computed files in ``pre_systhesis_cleaned``. To synthesis the FPGA bitstreams, please follow the below commands.
**Warning: the command could take 6-10 hours, please consider using tmux or background execution.**
```bash 
bash $BASEDIR/pre_systhesis_cleaned/<experiment-id>/real.sh
```


#### 4.3 Running Programs on FPGA

If the previous step is skipped or synthesis has done, FPGA bitstreams (.gbs files) should locate at ``$BASEDIR/pre_systhesis_cleaned/<experiment-id>/build_synth/``.

Pleas make setup tool environment before the following steps.
```bash
source $BASEDIR/venv/bin/activate
source $BASEDIR/profile
```


To run an experiment using its synthesized hardware design on the FPGA board, go to the corresponding experiment directory and execute the following commands:
```bash
bash $BASEDIR/scores/run-<experiment-id>.py
```

The available options are:
- `expt-3`
- `expt-4`
- `expt-6`
- `expt-8`
- `expt-9`
- `expt-10`
- `expt-11`

### 5. Results

Finally, run the following script to summarize the logic, RAM, and DSP utilization, along with the GOPS measurements collected in the previous step.

```bash
bash $BASEDIR/scores/perf-<experiment-id>.sh
```

A full list of experiment IDs is defined in `evaluation.py` and corresponds to the experiments in the artifact appendix.
These experiment IDs are:

- `expt-3`
- `expt-4`
- `expt-6`
- `expt-8`
- `expt-9`
- `expt-10`
- `expt-11`

<!-- We also include the following experiments from the prior work (only FPGA bitstreams, no compiling infra is included). Note that `expt-7` is not included. 
- `expt-1`
- `expt-2`
- `expt-5` -->


The output adheres to the following format and can be directly cross-referenced with Table 2 in the paper.

```
Latency (ms) : 72.2355
OP/cycle : 2124.53
GOP/s : 424.905
DSP efficiency (%) : 92.2104
Logic utilization (in ALMs) : 186,283 / 427,200 ( 44 % )
Total DSP Blocks : 576 / 1,518 ( 38 % )
Average Routing Congestion: 31.2%
Peak Routing Congestion: 69.3%
```


## Plot Figures 15 and 16

To reproduce Figures 15 and 16, run the following commands to draw the figures with pre-computed data points:

```bash
bash $BASEDIR/tmp/figures.sh
```

The generated figures will be `tmp/rooflines.pdf` for Figure 15 and `tmp/vgg16_runtime.pdf` for Figure 16. Please use ``xdg-open`` to open the pdf gui for them.

For Figure 15:
```bash
xdg-open $BASEDIR/tmp/rooflines.pdf
```

For Figure 16:
```bash
xdg-open $BASEDIR/tmp/vgg16_runtime.pdf
```


## Produce Table 3

To reproduce Table 3, run the following commands to print out the numbers in the table:

```bash
bash $BASEDIR/tmp/copy_nodes.sh
bash $BASEDIR/tmp/nodes.sh
```