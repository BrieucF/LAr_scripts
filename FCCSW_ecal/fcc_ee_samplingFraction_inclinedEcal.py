from Configurables import ApplicationMgr
from Configurables import PodioOutput
from Configurables import AuditorSvc, ChronoAuditor
from Configurables import SamplingFractionInLayers
from Configurables import SimG4PrimariesFromEdmTool
from Configurables import SimG4Alg, SimG4SaveCalHits
from Configurables import SimG4Svc
from Configurables import GeoSvc
from Configurables import HepMCToEDMConverter
from Configurables import GenAlg
from Configurables import MomentumRangeParticleGun
from Configurables import FCCDataSvc
from Configurables import THistSvc
from Gaudi.Configuration import INFO

from GaudiKernel.SystemOfUnits import GeV
from GaudiKernel.PhysicalConstants import pi

import os

# Electron momentum in GeV
momentum = 10
# Theta min and max in degrees
thetaMin = 90.
thetaMax = 90.

# Data service
podioevent = FCCDataSvc("EventDataSvc")

# Particle gun setup
pgun = MomentumRangeParticleGun("ParticleGun_Photon")
pgun.PdgCodes = [11]
pgun.MomentumMin = momentum * GeV
pgun.MomentumMax = momentum * GeV
pgun.PhiMin = 0
pgun.PhiMax = 2 * pi
# theta = 90 degrees (eta = 0)
pgun.ThetaMin = thetaMin * pi / 180.
pgun.ThetaMax = thetaMax * pi / 180.

genalg_pgun = GenAlg()
genalg_pgun.SignalProvider = pgun
genalg_pgun.hepmc.Path = "hepmc"

hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
genParticlesOutputName = "genParticles"
hepmc_converter.GenParticles.Path = genParticlesOutputName
hepmc_converter.hepmcStatusList = []

# DD4hep geometry service
geoservice = GeoSvc("GeoSvc",
                    OutputLevel=INFO)

path_to_detector = os.environ.get("K4GEO", "")
detectors_to_use = [
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/DectEmptyMaster.xml',
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ECalBarrel_thetamodulemerged_calibration.xml'
]
geoservice.detectors = [os.path.join(
    path_to_detector, _det) for _det in detectors_to_use]

# Geant4 service
# Configures the Geant simulation: geometry, physics list and user actions
geantservice = SimG4Svc("SimG4Svc", detector='SimG4DD4hepDetector',
                        physicslist="SimG4FtfpBert", actions="SimG4FullSimActions")
geantservice.g4PostInitCommands += ["/run/setCut 0.1 mm"]
geantservice.randomNumbersFromGaudi = False
geantservice.seedValue = 4242

# Geant4 algorithm
# Translates EDM to G4Event, passes the event to G4, writes out outputs via tools
# and a tool that saves the calorimeter hits
ecalBarrelHitsName = "ECalBarrelPositionedHits"
saveECalBarrelTool = SimG4SaveCalHits("saveECalBarrelHits",
                                      readoutName="ECalBarrelModuleThetaMerged"
                                      )
saveECalBarrelTool.CaloHits.Path = ecalBarrelHitsName

particle_converter = SimG4PrimariesFromEdmTool("EdmConverter")
particle_converter.GenParticles.Path = genParticlesOutputName

# next, create the G4 algorithm, giving the list of names of tools ("XX/YY")
geantsim = SimG4Alg("SimG4Alg",
                    outputs=[saveECalBarrelTool],
                    eventProvider=particle_converter,
                    OutputLevel=INFO)

hist = SamplingFractionInLayers("hists",
                                energyAxis=momentum,
                                readoutName="ECalBarrelModuleThetaMerged",
                                layerFieldName="layer",
                                activeFieldName="type",
                                activeFieldValue=0,
                                numLayers=11,
                                OutputLevel=INFO)
hist.deposits.Path = ecalBarrelHitsName

THistSvc().Output = [
    "rec DATAFILE='histSF_fccee_inclined.root' TYP='ROOT' OPT='RECREATE'"]
THistSvc().PrintAll = True
THistSvc().AutoSave = True
THistSvc().AutoFlush = False
THistSvc().OutputLevel = INFO

# CPU information
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
geantsim.AuditExecute = True
hist.AuditExecute = True

# PODIO algorithm
out = PodioOutput("out", OutputLevel=INFO)
out.outputCommands = ["drop *"]
out.filename = "fccee_samplingFraction_inclinedEcal.root"

# ApplicationMgr
ApplicationMgr(TopAlg=[genalg_pgun, hepmc_converter, geantsim, hist, out],
               EvtSel='NONE',
               EvtMax=100,
               # order is important, as GeoSvc is needed by G4SimSvc
               ExtSvc=[geoservice, podioevent, geantservice, audsvc],
               OutputLevel=INFO,
               StopOnSignal=True
               )
