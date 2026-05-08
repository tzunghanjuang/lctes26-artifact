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
ssh -A -J your-username@jump.cs.mcgill.ca your-username@solaire.cs.mcgill.ca
```
Once connected, you will have access to Intel Arria 10 PAC connected via PCI-Express on the server.

### 3. Acceess the Artifact
The artifact can be downloaded from Zenodo ``zenodo.org/records/20046007`` with the following command.
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

Please make sure to set current folder as the `BASEDIR`.
``` bash
export BASEDIR="$(pwd)"
```

### 4. Folder Structure
After unzipping the files in the previous sectiond the folder structure is as follows:
```
99
├── driver                 # FPGA driver
├── scores                 # Shell scripts to print the results for Table 2
├── src                    # Main Python scripts
├── tests                  # Main experiment scripts
├── data                   # Data and weight for accelerators
├── pre_synthesis_cleaned  # FPGA wrappers with pre-synthesizd bitstreams
├── venv                   # Python virtual environment
├── figures.py             # Python script to draw Figure 15 and 6
├── profile                # FPGA tool chain setup script (for the reference server with a Intel PAC card)
└── lctes26-docker.tar     # Docker immage for running the compiler infrastructure
```

The Docker image ``lctes26-docker.zip`` in this artifact reproduces the paper's accelerator HDL files, which are required for Table 2.
Generated VHDL code for all experiments are written to the local `results/` directory for evaluation. The generated VHDL will synthesized into FPGA bitstreams via Intel Quartus tool chain. 

The virtual environment ``venv`` are required to run the pytorch interface to execute the models on generated accelerators.

## Step-By-Step Instructions (Table 2)

The steps below walk you through the complete workflow for evaluating using our Docker image and python virtual evironment.

In this artifact, we sticks to the ``BASEDIR`` in ``99/``. Please run the following command to check if the setup is correct. It will print out a path ending with ``99``.
```bash
echo $BASEDIR
```


### 1. Load the Docker image
The docker image can be loaded with the folling command.

```bash
sudo docker load -i ./lctes26-artifact.tar
```

### 2. Run the container with mounted results

Create a local results directory and mount it into the container so that all outputs are available on your host machine. Note that this step only covers the experiements from this paper in Table 2, i.e., experiments with id 3, 4, 6, 8, 9, 10, 11. 

```bash
mkdir -p results
sudo docker run --rm -it \
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
Run the following command to execute the experimental options listed below:

```bash
docker run --rm -it \
  --mount type=bind,src=./results,dst=/workspace/results \
  ghcr.io/jonathanvdc/skeleshare-cgo26-artifact:latest \
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

**Warning:** Because synthesis typically takes **4–8 hours per benchmark** with Intel Quartus tool chain. We provide pre-synthesized designs that correspond exactly to the VHDL generated for each experiment. Please skip section 4.1 if long synthsis time is a concern. 

#### 4.1 Set up Intel Quartus tool chain environment (reference server only)
Please follow the instruction below to set up the the access to Intel Quartus tools and the FPGA driver.
```bash
source profile
```


#### 4.2 Synthsize FPGA Bitstreams (Optional)

After the step 3, the generated VHDL files should be located in the ``results`` folder. The next step is to copy them to the synthesis folder `pre_synthesis_cleaned` with the following commands;
```bash
bash ./scores/copy-<experiment-id>.sh
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
**Warning: the command could take 4-8 hours, please consider using tmux or background execution.**
```bash 
bash ./pre_systhesis_cleaned/<experiment-id>/real.sh
```


#### 4.3 Running Programms on FPGA

If the previous step is skipped or synthesis has done, FPGA bitstreams (.gbs files) should locate at ``./pre_systhesis_cleaned/<experiment-id>/build_synth/``.

Pleas make source running ``source profile`` before the following steps.

The next step is to set up the python virtual environment.
```bash
source ./venv/bin/activate
```

To run an experiment using its synthesized hardware design on the FPGA board, go to the corresponding experiment directory and execute the following commands:
```bash
python ./test/<experiment-id>.py
```

The available options are:
- `expt-3`
- `expt-4`
- `expt-6`
- `expt-8`
- `expt-9`
- `expt-10`
- `expt-11`

<!-- Inside each experiment (folder ``./precomputed/<experiment-id>``), the software runtime for each experiment might also need to be updated due to different compiling environment.
```bash
cd ./sw
cmake .
make clean
make
cd ..
```

To run an experiment using its pre-synthesized hardware design on the FPGA board, go to the corresponding experiment directory and execute the following commands:

```bash
./real_start.sh
./real_sw.sh
``` -->

### 5. Results

Finally, run the following script to summarize the logic, RAM, and DSP utilization, along with the GOPS measurements collected in the previous step.

```bash
bash $SCRIPTDIR/scores/<experiment-id>.sh
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
