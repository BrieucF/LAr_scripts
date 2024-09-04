# LAr_scripts

Various scripts used for LAr studies

## How to get started for newcomers

### Setup FCC release
Go to work directory

```
export FCCBASEDIR=$PWD
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
```

### Getting LAr_scripts package and the required data files
```
git clone git@github.com:BrieucF/LAr_scripts.git
# if outside CERN
scp yourlogin@lxplus.cern.ch:/eos/user/b/brfranco/rootfile_storage/neighbours_map_barrel.root LAr_scripts/data/
scp yourlogin@lxplus.cern.ch:/eos/user/b/brfranco/rootfile_storage/cellNoise_map_electronicsNoiseLevel.root LAr_scripts/data/
scp yourlogin@lxplus.cern.ch:/eos/user/g/gmarchio/rootfile_storage/neighbours_map_barrel_thetamodulemerged.root LAr_scripts/data/
scp yourlogin@lxplus.cern.ch:/eos/user/g/gmarchio/rootfile_storage/cellNoise_map_electronicsNoiseLevel_thetamodulemerged.root LAr_scripts/data/
# if at CERN
cp /eos/user/b/brfranco/rootfile_storage/neighbours_map_barrel.root LAr_scripts/data/
cp /eos/user/b/brfranco/rootfile_storage/cellNoise_map_electronicsNoiseLevel.root LAr_scripts/data/
cp /eos/user/g/gmarchio/rootfile_storage/neighbours_map_barrel_thetamodulemerged.root LAr_scripts/data/
cp /eos/user/g/gmarchio/rootfile_storage/cellNoise_map_electronicsNoiseLevel_thetamodulemerged.root LAr_scripts/data/
```

### Getting additional packages
These packages are optional: basically only when one needs to modify them
and recompile

#### FCCAnalyses
Package also used for FCC physics analyses. Contains useful routines to create ntuples
with calo information from FCC EDM files: `CaloNtupleizer` class.

```
git clone git@github.com:HEP-FCC/FCCAnalyses.git
```

Some setup needed:
```
cd FCCAnalyses
export PYTHONPATH=$PWD:$PYTHONPATH
export LD_LIBRARY_PATH=$PWD/install/lib:$LD_LIBRARY_PATH
export ROOT_INCLUDE_PATH=$PWD/install/include:$ROOT_INCLUDE_PATH
export LD_LIBRARY_PATH=`python -m awkward.config --libdir`:$LD_LIBRARY_PATH
cd ..
```

Compiling:
```
cd FCCAnalyses
mkdir build
cd build
cmake ../ -DCMAKE_INSTALL_PREFIX=../install -DWITH_DD4HEP=ON
make -j32 install
cd ../../
```

#### Setup for the other packages
```
export FCCDETECTORS=$PWD/FCCDetectors/
export K4FWCORE=$PWD/k4FWCore/install/share/k4FWCore
export K4GEO=$PWD/k4geo/install/share/k4geo
export K4RECCALORIMETER=$PWD/k4RecCalorimeter/install/share/k4RecCalorimeter
export PATH=$PWD/k4RecCalorimeter/install/bin/:$PWD/k4geo/install/bin/:$PWD/k4FWCore/install/bin/:$PATH
export CMAKE_PREFIX_PATH=$PWD/k4RecCalorimeter/install:$PWD/k4geo/install/:$PWD/k4FWCore/install/:$PWD/FCCDetectors/install/:$CMAKE_PREFIX_PATH
export LD_LIBRARY_PATH=$PWD/k4RecCalorimeter/install/lib:$PWD/k4RecCalorimeter/install/lib64:$PWD/k4geo/install/lib:$PWD/k4geo/install/lib64:$PWD/k4FWCore/install/lib:$PWD/FCCDetectors/install/lib:$PWD/FCCDetectors/install/lib64:$LD_LIBRARY_PATH
export PYTHONPATH=$PWD/k4RecCalorimeter/install/python:$PWD/k4FWCore/install/python:$PYTHONPATH
```

#### FCCDetectors
This package contains all the detector descriptions as xml files, and the detailed
geometry is implemented in cpp files.

```
git clone git@github.com:HEP-FCC/FCCDetectors.git
```

Compiling:
```
cd FCCDetectors
mkdir build
cd build
cmake ../ -DCMAKE_INSTALL_PREFIX=../install 
make -j32 install
cd ../../
```

#### k4RecCalorimeter
This package contains all the reconstruction algorithms, i.e
digitization, clustering.

```
git clone git@github.com:HEP-FCC/k4RecCalorimeter.git
```

Compiling:
```
cd k4RecCalorimeter
mkdir build
cd build
cmake ../ -DCMAKE_INSTALL_PREFIX=../install 
make -j32 install
cd ../../
```

#### k4SimGeant4
This package contains some stuff related to full simulation.
In particular for us, in `Detector/DetStudies`, the algorithms
and scripts to compute the sampling fraction and the upstream/downstream
energy corrections

```
git clone git@github.com:HEP-FCC/k4SimGeant4.git
```

Compiling:
```
cd k4SimGeant4
mkdir build
cd build
cmake ../ -DCMAKE_INSTALL_PREFIX=../install 
make -j32 install
cd ../../
```

### Change the geometry and recompute resolutions from scratch
#### Geometry
Main xml file with the calo geometry:
`FCCDetectors/Detector/DetFCCeeECalInclined/compact/FCCee_ECalBarrel.xml`

This ECal xml file is called from the main FCCeeIDEA-LAr xml description:
`FCCDetectors/Detector/DetFCCeeIDEA-LAr/compact/FCCee_DectMaster.xml`

In `FCCee_ECalBarrel.xml`:
* one can change lengths of various items in the calo: cryo, LAr dead bath,
absorber plates, LAr gaps...
* one can change material of active liquid or absorber or cryo: LAr->LKr, ...
* one can change the dimensions of the readout layers

You should regenerate the other xml files used for sampling fraction calculation
or for upstream/downstream energy corrections calculations:
```
cd LAr_scripts/FCCSW_ecal
python write_calibration_xml.py ../../FCCDetectors/Detector/DetFCCeeECalInclined/compact/FCCee_ECalBarrel.xml
```

The X0 plot can be produced to check the amount of material:
```
cd ../geometry
fccrun material_scan.py
python material_plot.py
```

Results are in `x0pos.png`, `lambdapos.png`, ...

#### Computing sampling fraction
JobOption to run:
`fccrun fcc_ee_samplingFraction_inclinedEcal.py`

Outputs `fccee_samplingFraction_inclinedEcal.root` and `histSF_fccee_inclined.root`. Second file (hist)
is where the useful histograms are.

Post-processing:
`FCC_calo_analysis_cpp/plot_samplingFraction.py`
creates plots of sampling fractions, possibly json file with values (`--json`), and can replace the sampling
fraction values in other jobOption files (`--sed`).


#### Computing upstream and downstream corrections
jobOption to run:
`fcc_ee_upstream_inclinedEcal.py`

Computes the energy per layer in the LAr/Pb calo (applying sampling fraction), and
stores the truth energy deposited at the front or at the back.
Outputs:
ROOT file in FCC EDM. Contains info on simulated particle, and `energyInLayer` and `energyInCryo`.

Post-processing:

For each input energy, find relation between eneryg in layer 0 and energy in front ; find
relation between energy in last layer and energy in back:
`k4SimGeant4/Detector/DetStudies/scripts/cec_process_events`

Then interpolate between energies to find estimates of upstream/downstream corrections
as function of calo energy, energy in 1st layer and energy in last layer
`k4SimGeant4/Detector/DetStudies/scripts/cec_derive1`

#### Running reconstruction algorithms
Pre-processing step: `sed` the upstream and downstream corrections in the jobOption file, 
using the `read_upstream_json.py` script

jobOption to run:
`runTopoAndSlidingWindowAndCaloSim.py`

Generate single electrons. Create calorimeter cells. Add noise if needed. Create calo towers.
Create fixed size clusters. Correct the clusters. Create the topo clusters. Correct the topo
clusters. (correction means applying upstream and downstream corrections)

WARNING: edit this file and check that the ROOT files related to noise are accessible for you
(there are several options whether you are at CERN or elsewhere)

Output:
File in FCC EDM format with collections for each type of cluster, for simulated particles and
for ECal cells.

#### Training the MVA calibration
The MVA calibration relies on XGBoost. It has been available in FCC software since October 1, 2022.

Training on CaloClusters:
`python training.py CaloClusters -i production/ --json upstream/corr_params_1d.json -o training_calo.json`
Training on CaloTopoClusters:
`python training.py CaloTopoClusters -i production/ --json upstream/corr_params_1d.json -o training_topo.json`

#### Computing and plotting energy resolutions and other quantities
First step: apply MVA calibration if needed, then compute energy resolutions for a given geometry
`python compute_resolutions.py --inputDir $runname/clusters --outFile $runname/results.csv --clusters
CaloClusters CorrectedCaloClusters CaloTopoClusters CorrectedCaloTopoClusters --MVAcalibCalo
$runname/training_calo.json --MVAcalibTopo $runname/training_topo.json`

Second step: produce nice plots
* Produce plots for each type of cluster:
`python plot_resolutions.py --outDir $runname --doFits plot $runname/results.csv --all`

* Compare several types of clusters for a given geometry:
`python plot_resolutions.py --outDir $runname --doFits compare clusters CaloClusters CorrectedCaloClusters
CalibratedCaloClusters CalibratedCaloTopoClusters $runname/results.csv --distributions E_resol E_response`

* Compare several geometries for a given cluster type:
`python plot_resolutions.py --outDir comp --doFits compare files baseline_LAr_noNoise_1/results.csv
baseline_LKr_noNoise_1/results.csv constantDepth_LKr_noNoise_1/results.csv
constantDepth_LKr_W_noNoise_1/results.csv constantDepth_LKr_W_optim_noNoise_1/results.csv -d "1.8mm Pb,
LAr" "1.8mm Pb, LKr" "1.35mm Pb, LKr" "1.35mm W, LKr" "1.0mm W, LKr" --clusters CorrectedCaloClusters
CorrectedCaloTopoClusters --distributions E_resol E_response`

#### High-level automation of all previous steps
##### `runParallel.py`:
For each major step (sampling, up/downstream, cluster production) it allows to perform
pre-processing, processing "on batch" i.e on multicore, hadd the results, then post-processing steps.

Examples:

* Computation of sampling fraction:
`python runParallel.py --outDir $runname/sampling --nEvt 1000 --energies 20000 --sampling`

* Upstream/downstream corrections:
`python runParallel.py --outDir $runname/upstream --nEvt 1000 --energies 1000 5000 10000 15000 20000 30000
50000 75000 100000 --upstream --SF $runname/sampling/SF.json`

* Large number of clusters for MVA training:
`python runParallel.py --outDir $runname/production --nEvt 300000 --production --SF
$runname/sampling/SF.json --corrections $runname/upstream/corr_params_1d.json`

* Clusters for energy resolutions:
`python runParallel.py --outDir $runname/clusters --nEvt 1000 --energies 500 1000 5000 10000 15000 20000
30000 50000 75000 100000 --clusters --SF $runname/sampling/SF.json --corrections
$runname/upstream/corr_params_1d.json`

##### `run_all_chain.sh`
Basically runs all the steps in one go. Comment/uncomment lines as needed.

* Propagate the geometry changes, and computes the X0. Archives the files.
* Calls the `runParallel` scripts for the various steps.
* Train the MVA calib (on CaloClusters and CaloTopoClusters)
* Then compute the resolutions and responses, and make plots.

#### Producing neighbours of crosstalk
jobOption to run:
`xtalk_neighbours_theta.py`

For each cell, generate a list of crosstalk neighbours and their corresponding crosstalk coefficients with respect to the cell under study. The Layer/Module/Theta indices can be added for debug purpose.

Output:
`xtalk_neighbours_map_ecalB_thetamodulemerged.root`
A list of crosstalk neighbours and corresponding crosstalk coefficients for each cell.
