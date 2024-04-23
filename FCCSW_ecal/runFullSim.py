import os

from GaudiKernel.SystemOfUnits import MeV, GeV, tesla

use_pythia = False
addNoise = False

# Input for simulations (momentum is expected in GeV!)
# Parameters for the particle gun simulations, dummy if use_pythia is set to True
# theta from 80 to 100 degrees corresponds to -0.17 < eta < 0.17 
momentum = 5 # in GeV
#thetaMin = 90.25 # degrees
#thetaMax = 90.25 # degrees
thetaMin = 20 # degrees
thetaMax = 130 # degrees
pdgCode = 211 # 11 electron, 13 muon, 22 photon, 111 pi0, 211 pi+
magneticField = False

from Gaudi.Configuration import *

from Configurables import FCCDataSvc
podioevent  = FCCDataSvc("EventDataSvc")

################## Particle gun setup
_pi = 3.14159

from Configurables import GenAlg
genAlg = GenAlg()
if use_pythia:
    from Configurables import PythiaInterface
    pythia8gentool = PythiaInterface()
    pythia8gentool.pythiacard = os.path.join(os.environ.get('PWD', ''), "MCGeneration/ee_Zgamma_inclusive.cmd")
    #pythia8gentool.pythiacard = "MCGeneration/ee_Z_ee.cmd"
    pythia8gentool.printPythiaStatistics = False
    pythia8gentool.pythiaExtraSettings = [""]
    genAlg.SignalProvider = pythia8gentool
    # to smear the primary vertex position:
    #from Configurables import GaussSmearVertex
    #smeartool = GaussSmearVertex()
    #smeartool.xVertexSigma =   0.5*units.mm
    #smeartool.yVertexSigma =   0.5*units.mm
    #smeartool.zVertexSigma =  40.0*units.mm
    #smeartool.tVertexSigma = 180.0*units.picosecond
    #genAlg.VertexSmearingTool = smeartool
else:
    from Configurables import  MomentumRangeParticleGun
    pgun = MomentumRangeParticleGun("ParticleGun_Electron")
    pgun.PdgCodes = [pdgCode]
    pgun.MomentumMin = momentum * GeV
    pgun.MomentumMax = momentum * GeV
    pgun.PhiMin = 0
    #pgun.PhiMax = 0
    pgun.PhiMax = 2 * _pi
    pgun.ThetaMin = thetaMin * _pi / 180.
    pgun.ThetaMax = thetaMax * _pi / 180.
    genAlg.SignalProvider = pgun

genAlg.hepmc.Path = "hepmc"

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path="hepmc"
genParticlesOutputName = "genParticles"
hepmc_converter.GenParticles.Path = genParticlesOutputName
hepmc_converter.hepmcStatusList = []

################## Simulation setup
# Detector geometry
from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc")
# if FCC_DETECTORS is empty, this should use relative path to working directory
path_to_detector = os.environ.get("FCCDETECTORS", "")
print(path_to_detector)
detectors_to_use=[
                    'Detector/DetFCCeeIDEA-LAr/compact/FCCee_DectMaster.xml',
                  ]
# prefix all xmls with path_to_detector
geoservice.detectors = [os.path.join(path_to_detector, _det) for _det in detectors_to_use]
geoservice.OutputLevel = INFO

# Geant4 service
# Configures the Geant simulation: geometry, physics list and user actions

from Configurables import SimG4FullSimActions, SimG4Alg, SimG4PrimariesFromEdmTool, SimG4SaveParticleHistory
actions = SimG4FullSimActions()
# Uncomment if history from Geant4 decays is needed (e.g. to get the photons from pi0) and set actions=actions in SimG4Svc + uncomment saveHistTool in SimG4Alg
#actions.enableHistory=True
#actions.energyCut = 0.2 * GeV
#saveHistTool = SimG4SaveParticleHistory("saveHistory")

# Magnetic field
from Configurables import SimG4ConstantMagneticFieldTool
if magneticField == 1:
    field = SimG4ConstantMagneticFieldTool("SimG4ConstantMagneticFieldTool", FieldComponentZ = -2 * tesla, FieldOn = True, IntegratorStepper = "ClassicalRK4")
else:
    field = SimG4ConstantMagneticFieldTool("SimG4ConstantMagneticFieldTool", FieldOn = False)

from Configurables import SimG4Svc
geantservice = SimG4Svc("SimG4Svc", detector = 'SimG4DD4hepDetector', physicslist = "SimG4FtfpBert", actions = actions, magneticField = field)

# Fixed seed to have reproducible results, change it for each job if you split one production into several jobs
# Mind that if you leave Gaudi handle random seed and some job start within the same second (very likely) you will have duplicates
geantservice.randomNumbersFromGaudi = False
geantservice.seedValue = 4242

# Range cut
geantservice.g4PreInitCommands += ["/run/setCut 0.1 mm"]


# Geant4 algorithm
# Translates EDM to G4Event, passes the event to G4, writes out outputs via tools
# and a tool that saves the calorimeter hits

# Detector readouts
# ECAL
ecalBarrelReadoutName = "ECalBarrelEta"
ecalBarrelReadoutNamePhiEta = "ECalBarrelPhiEta"
ecalEndcapReadoutName = "ECalEndcapPhiEta"

# HCAL
hcalBarrelReadoutName = "HCalBarrelReadout"
hcalEndcapReadoutName = "HCalEndcapReadout"

# Configure saving of calorimeter hits
ecalBarrelHitsName = "ECalBarrelPositionedHits"
from Configurables import SimG4SaveCalHits
saveECalBarrelTool = SimG4SaveCalHits("saveECalBarrelHits", readoutNames = [ecalBarrelReadoutName])
saveECalBarrelTool.CaloHits.Path = ecalBarrelHitsName

hcalBarrelHitsName = "HCalBarrelPositionedHits"
saveHCalTool = SimG4SaveCalHits("saveHCalBarrelHits", readoutNames = [hcalBarrelReadoutName])
saveHCalTool.CaloHits.Path = hcalBarrelHitsName

ecalEndcapHitsName = "ECalEndcapPositionedHits"
saveECalEndcapTool = SimG4SaveCalHits("saveECalEndcapHits", readoutNames = [ecalEndcapReadoutName])
saveECalEndcapTool.CaloHits.Path = ecalEndcapHitsName

hcalEndcapHitsName = "HCalEndcapPositionedHits"
saveHCalEndcapTool = SimG4SaveCalHits("saveHCalEndcapHits", readoutNames = [hcalEndcapReadoutName])
saveHCalEndcapTool.CaloHits.Path = hcalEndcapHitsName

# next, create the G4 algorithm, giving the list of names of tools ("XX/YY")
from Configurables import SimG4PrimariesFromEdmTool
particle_converter = SimG4PrimariesFromEdmTool("EdmConverter")
particle_converter.GenParticles.Path = genParticlesOutputName

from Configurables import SimG4Alg
geantsim = SimG4Alg("SimG4Alg",
                       outputs= [saveECalBarrelTool,
                                 saveHCalTool,
                                 saveECalEndcapTool,
                                 saveHCalEndcapTool,
                                 #saveHistTool
                       ],
                       eventProvider=particle_converter,
                       OutputLevel=INFO)

############## Digitization (Merging hits into cells, EM scale calibration)
# EM scale calibration (sampling fraction)
from Configurables import CalibrateInLayersTool
calibEcalBarrel = CalibrateInLayersTool("CalibrateECalBarrel",
                                   samplingFraction = [0.3632447480841956] * 1 + [0.13187261040190248] * 1 + [0.14349714292943705] * 1 + [0.150266118277841] * 1 + [0.15502683375826457] * 1 + [0.15954408786354762] * 1 + [0.16375302347299436] * 1 + [0.16840384714588075] * 1 + [0.17219540619311383] * 1 + [0.1755068643940401] * 1 + [0.17816980262822366] * 1 + [0.18131266048670405] * 1,
                                   readoutName = ecalBarrelReadoutName,
                                   layerFieldName = "layer")

from Configurables import CalibrateCaloHitsTool
calibHcells = CalibrateCaloHitsTool("CalibrateHCal", invSamplingFraction="41.66")
calibEcalEndcap = CalibrateCaloHitsTool("CalibrateECalEndcap", invSamplingFraction="4.27")
calibHcalEndcap = CalibrateCaloHitsTool("CalibrateHCalEndcap", invSamplingFraction="31.7")

# Create cells in ECal barrel
# 1. step - merge hits into cells with Eta and module segmentation (phi module is a 'physical' cell i.e. lead + LAr + PCB + LAr +lead)
# 2. step - rewrite the cellId using the Eta-Phi segmentation (merging several modules into one phi readout cell). Add noise at this step if you derived the noise already assuming merged cells
from Configurables import CreateCaloCells
createEcalBarrelCellsStep1 = CreateCaloCells("CreateECalBarrelCellsStep1",
                               doCellCalibration=True,
                               calibTool = calibEcalBarrel,
                               addCellNoise=False, filterCellNoise=False,
                               addPosition=True,
                               OutputLevel=INFO,
                               hits=ecalBarrelHitsName,
                               cells="ECalBarrelCellsStep1")

## Use Phi-Theta segmentation in ECal barrel
from Configurables import RedoSegmentation
resegmentEcalBarrel = RedoSegmentation("ReSegmentationEcal",
                             # old bitfield (readout)
                             oldReadoutName = ecalBarrelReadoutName,
                             # specify which fields are going to be altered (deleted/rewritten)
                             oldSegmentationIds = ["module"],
                             # new bitfield (readout), with new segmentation
                             newReadoutName = ecalBarrelReadoutNamePhiEta,
                             OutputLevel = INFO,
                             inhits = "ECalBarrelCellsStep1",
                             outhits = "ECalBarrelCellsStep2")

# cells without noise
EcalBarrelCellsName = "ECalBarrelCells"
createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCells",
                               doCellCalibration=False,
                               addCellNoise=False, filterCellNoise=False,
                               OutputLevel=INFO,
                               hits="ECalBarrelCellsStep2",
                               cells=EcalBarrelCellsName)
cell_creator_to_use = createEcalBarrelCells

# generate noise for each cell
if addNoise:
    ecalBarrelNoisePath = os.environ['FCCBASEDIR']+"/LAr_scripts/data/elecNoise_ecalBarrelFCCee.root"
    ecalBarrelNoiseHistName = "h_elecNoise_fcc_"
    from Configurables import NoiseCaloCellsFromFileTool
    noiseBarrel = NoiseCaloCellsFromFileTool("NoiseBarrel",
                                             readoutName = ecalBarrelReadoutNamePhiEta,
                                             noiseFileName = ecalBarrelNoisePath,
                                             elecNoiseHistoName = ecalBarrelNoiseHistName,
                                             activeFieldName = "layer",
                                             addPileup = False,
                                             filterNoiseThreshold = 2,
                                             scaleFactor = 1/1000.,
                                             numRadialLayers = 12)

    from Configurables import TubeLayerPhiEtaCaloTool
    barrelGeometry = TubeLayerPhiEtaCaloTool("EcalBarrelGeo",
                                             readoutName = ecalBarrelReadoutNamePhiEta,
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [4])
                                             #activeVolumesNumber = 12)
    # cells with noise not filtered
    createEcalBarrelCellsNoise = CreateCaloCells("CreateECalBarrelCellsNoise",
                                   doCellCalibration=False,
                                   addCellNoise=True, filterCellNoise=False,
                                   OutputLevel=INFO,
                                   hits="ECalBarrelCellsStep2",
                                   noiseTool = noiseBarrel,
                                   geometryTool = barrelGeometry,
                                   cells=EcalBarrelCellsName)

    # cells with noise filtered
    #createEcalBarrelCellsNoise = CreateCaloCells("CreateECalBarrelCellsNoise_filtered",
    #                               doCellCalibration=False,
    #                               addCellNoise=True, filterCellNoise=True,
    #                               OutputLevel=INFO,
    #                               hits="ECalBarrelCellsStep2",
    #                               noiseTool = noiseBarrel,
    #                               geometryTool = barrelGeometry,
    #                               cells=EcalBarrelCellsName)

    cell_creator_to_use = createEcalBarrelCellsNoise


# Ecal barrel cell positions (good for physics, all coordinates set properly)
from Configurables import CellPositionsECalBarrelTool
cellPositionEcalBarrelTool = CellPositionsECalBarrelTool("CellPositionsECalBarrel", readoutName = ecalBarrelReadoutNamePhiEta, OutputLevel = INFO)

from Configurables import CreateCaloCellPositionsFCCee
createEcalBarrelPositionedCells = CreateCaloCellPositionsFCCee("ECalBarrelPositionedCells", OutputLevel = INFO)
createEcalBarrelPositionedCells.positionsTool = cellPositionEcalBarrelTool
createEcalBarrelPositionedCells.hits.Path = EcalBarrelCellsName
createEcalBarrelPositionedCells.positionedHits.Path = "ECalBarrelPositionedCells"


# Create cells in HCal
# 1. step - merge hits into cells with the default readout
HcalBarrelCellsName = "HCalBarrelCells"
createHcalBarrelCells = CreateCaloCells("CreateHCaloCells",
                               doCellCalibration=True,
                               calibTool=calibHcells,
                               addCellNoise = False,
                               filterCellNoise = False,
                               addPosition=True,
                               OutputLevel = INFO,
                               hits=hcalBarrelHitsName,
                               cells=HcalBarrelCellsName)

HcalEndcapCellsName = "HCalEndcapCells"
createHcalEndcapCells = CreateCaloCells("CreateHcalEndcapCaloCells",
                                    doCellCalibration=True,
                                    calibTool=calibHcalEndcap,
                                    addCellNoise=False, 
                                    filterCellNoise=False,
                                    OutputLevel=INFO,
                                    hits=hcalEndcapHitsName,
                                    cells=HcalEndcapCellsName)

"""
from Configurables import CellPositionsHCalBarrelTool
cellPositionHcalBarrelTool = CellPositionsHCalBarrelTool("CellPositionsHCalBarrel", readoutName = hcalBarrelReadoutName, OutputLevel = INFO)
createHcalBarrelPositionedCells = CreateCaloCellPositionsFCCee("HCalBarrelPositionedCells", OutputLevel = INFO)
createHcalBarrelPositionedCells.positionsHCalBarrelTool = cellPositionHcalBarrelTool
createHcalBarrelPositionedCells.hits.Path = HcalBarrelCellsName
HCalBarrelPositionedCellsName = "HCalBarrelPositionedCellsName"
createHcalBarrelPositionedCells.positionedHits.Path = "HCalBarrelPositionedCells"
"""
EcalEndcapCellsName = "ECalEndcapCells"
createEcalEndcapCells = CreateCaloCells("CreateEcalEndcapCaloCells",
                                    doCellCalibration=True,
                                    calibTool=calibEcalEndcap,
                                    addCellNoise=False, 
                                    filterCellNoise=False,
                                    addPosition=True,
                                    OutputLevel = INFO,
                                    hits=ecalEndcapHitsName,
                                    cells=EcalEndcapCellsName)

#Empty cells for parts of calorimeter not implemented yet
from Configurables import CreateEmptyCaloCellsCollection
createemptycells = CreateEmptyCaloCellsCollection("CreateEmptyCaloCells")
createemptycells.cells.Path = "emptyCaloCells"

from Configurables import CaloTowerTool
towers = CaloTowerTool("towers",
                               deltaEtaTower = 0.01, deltaPhiTower = 2*_pi/768.,
                               radiusForPosition = 2160 + 40 / 2.0,
                               ecalBarrelReadoutName = ecalBarrelReadoutNamePhiEta,
                               ecalEndcapReadoutName = ecalEndcapReadoutName,
                               ecalFwdReadoutName = "",
                               hcalBarrelReadoutName = hcalBarrelReadoutName,
                               hcalExtBarrelReadoutName = "",
                               hcalEndcapReadoutName = "",
                               hcalFwdReadoutName = "",
                               OutputLevel = INFO)
towers.ecalBarrelCells.Path = EcalBarrelCellsName
towers.ecalEndcapCells.Path = EcalEndcapCellsName
towers.ecalFwdCells.Path = "emptyCaloCells"
towers.hcalBarrelCells.Path = HcalBarrelCellsName
towers.hcalExtBarrelCells.Path = "emptyCaloCells"
towers.hcalEndcapCells.Path = "emptyCaloCells"
towers.hcalFwdCells.Path = "emptyCaloCells"

# Cluster variables
windE = 9
windP = 17
posE = 5
posP = 11
dupE = 7
dupP = 13
finE = 9
finP = 17
# Minimal energy to create a cluster in GeV (FCC-ee detectors have to reconstruct low energy particles)
threshold = 0.05

from Configurables import CreateCaloClustersSlidingWindow
createClusters = CreateCaloClustersSlidingWindow("CreateClusters",
                                                 towerTool = towers,
                                                 nEtaWindow = windE, nPhiWindow = windP,
                                                 nEtaPosition = posE, nPhiPosition = posP,
                                                 nEtaDuplicates = dupE, nPhiDuplicates = dupP,
                                                 nEtaFinal = finE, nPhiFinal = finP,
                                                 energyThreshold = threshold,
                                                 energySharingCorrection = True,
                                                 attachCells = True,
                                                 OutputLevel = INFO
                                                 )
createClusters.clusters.Path = "CaloClusters"
createClusters.clusterCells.Path = "CaloClusterCells"

createEcalBarrelPositionedCaloClusterCells = CreateCaloCellPositionsFCCee("ECalBarrelPositionedCaloClusterCells", OutputLevel = INFO)
createEcalBarrelPositionedCaloClusterCells.positionsTool = cellPositionEcalBarrelTool
createEcalBarrelPositionedCaloClusterCells.hits.Path = "CaloClusterCells"
createEcalBarrelPositionedCaloClusterCells.positionedHits.Path = "PositionedCaloClusterCells"

from Configurables import CorrectCaloClusters
correctCaloClusters = CorrectCaloClusters("correctCaloClusters",
                                          inClusters = createClusters.clusters.Path,
                                          outClusters = "Corrected"+createClusters.clusters.Path,
                                          systemIDs=[4],
                                          numLayers = [12],
                                          firstLayerIDs = [0],
                                          lastLayerIDs = [11],
                                          readoutNames = [ecalBarrelReadoutNamePhiEta],
                                          upstreamParameters = [[0.033955208567442975, -3.818122686176795, -146.59497297249345, 0.563447903447204, -3.7906629536351906, -8.569962044554627]],
                                          upstreamFormulas = [['[0]+[1]/(x-[2])', '[0]+[1]/(x-[2])']],
                                          downstreamParameters = [[-0.00357017357914002, 0.006624434345822984, 1.0065650241358008, -1.285181650875406, -0.0707783194915608, 12.907319280196257]],
                                          downstreamFormulas = [['[0]+[1]*x', '[0]+[1]/sqrt(x)', '[0]+[1]/x']],
                                          OutputLevel = INFO
                                          )

################ Output
from Configurables import PodioOutput
out = PodioOutput("out",
                  OutputLevel=INFO)
#out.outputCommands = ["drop *", "keep ECalBarrelPositionedCells", "keep gen*"]
#out.outputCommands = ["keep *", "drop ECalBarrelHits", "drop HCal*", "drop ECalBarrelCellsStep*", "drop ECalBarrelPositionedHits", "drop emptyCaloCells", "drop CaloClusterCells"]
out.outputCommands = ["keep *", "drop ECalBarrelHits", "drop ECalBarrelCellsStep*", "drop emptyCaloCells"]
#out.outputCommands = ["keep *", "drop ECalBarrelHits", "drop HCal*", "drop ECalBarrelCellsStep*", "drop ECalBarrelPositionedHits", "drop emptyCaloCells", "drop CaloClusterCells", "drop %s"%EcalBarrelCellsName, "drop %s"%createEcalBarrelPositionedCells.positionedHits.Path]

import uuid
out.filename = "output_fullCalo_SimAndDigi_withCluster_MagneticField_"+str(magneticField)+"_pMin_"+str(momentum*1000)+"_MeV"+"_ThetaMinMax_"+str(thetaMin)+"_"+str(thetaMax)+"_pdgId_"+str(pdgCode)+"_pythia"+str(use_pythia)+"_Noise"+str(addNoise)+".root"

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
genAlg.AuditExecute = True
hepmc_converter.AuditExecute = True
geantsim.AuditExecute = True
createEcalBarrelCellsStep1.AuditExecute = True
resegmentEcalBarrel.AuditExecute = True
cell_creator_to_use.AuditExecute = True
#createHcalBarrelCells.AuditExecute = True
out.AuditExecute = True

from Configurables import EventCounter
event_counter = EventCounter('event_counter')
event_counter.Frequency = 10

from Configurables import ApplicationMgr
ApplicationMgr(
    TopAlg = [
              event_counter,
              genAlg,
              hepmc_converter,
              geantsim,
              createEcalBarrelCellsStep1,
              resegmentEcalBarrel,
              #createEcalBarrelCells,
              cell_creator_to_use,
              createEcalBarrelPositionedCells,
              createHcalBarrelCells,
              #createHcalBarrelPositionedCells,
              createEcalEndcapCells,
              createHcalEndcapCells,
              #createemptycells,
              #createClusters,
              #createEcalBarrelPositionedCaloClusterCells,
              #correctCaloClusters,
              out
              ],
    EvtSel = 'NONE',
    EvtMax   = 10,
    ExtSvc = [geoservice, podioevent, geantservice, audsvc],
    StopOnSignal = True,
 )
