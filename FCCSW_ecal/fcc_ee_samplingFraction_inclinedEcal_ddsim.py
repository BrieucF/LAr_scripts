from Configurables import ApplicationMgr
from Configurables import EventCounter
from Configurables import k4DataSvc, PodioInput
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

# Loading the output of the SIM step
evtsvc = k4DataSvc('EventDataSvc')
evtsvc.input = "./ALLEGRO_calibration_sim.root"

input_reader = PodioInput('InputReader')

podioevent = k4DataSvc("EventDataSvc")

# DD4hep geometry service
geoservice = GeoSvc("GeoSvc",
                    OutputLevel=INFO)

# old
# path_to_detector = os.environ.get("FCCDETECTORS", "")
# detectors_to_use = [
#    'Detector/DetFCCeeIDEA-LAr/compact/FCCee_DectEmptyMaster.xml',
#    'Detector/DetFCCeeECalInclined/compact/FCCee_ECalBarrel_thetamodulemerged_calibration.xml',
#    ]
path_to_detector = os.environ.get("K4GEO", "")
detectors_to_use = [
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/DectEmptyMaster.xml',
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ECalBarrel_thetamodulemerged_calibration.xml'
]
geoservice.detectors = [os.path.join(
    path_to_detector, _det) for _det in detectors_to_use]


# Geant4 algorithm
# Translates EDM to G4Event, passes the event to G4, writes out outputs via tools
# and a tool that saves the calorimeter hits
ecalBarrelHitsName = "ECalBarrelPositionedHits"
saveECalBarrelTool = SimG4SaveCalHits("saveECalBarrelHits",
                                      readoutName="ECalBarrelModuleThetaMerged"
                                      )
saveECalBarrelTool.CaloHits.Path = ecalBarrelHitsName

hist = SamplingFractionInLayers("hists",
                                energyAxis=10,
                                readoutName="ECalBarrelModuleThetaMerged",
                                layerFieldName="layer",
                                activeFieldName="type",
                                activeFieldValue=0,
                                numLayers=12,
                                OutputLevel=INFO)
hist.deposits.Path = "ECalBarrelModuleThetaMerged"

THistSvc().Output = [
    "rec DATAFILE='calibration_output_pdgID_11_pMin_10000_pMax_10000_thetaMin_55_thetaMax_125_ddsim.root' TYP='ROOT' OPT='RECREATE'"]
THistSvc().PrintAll = True
THistSvc().AutoSave = True
THistSvc().AutoFlush = False
THistSvc().OutputLevel = INFO

# CPU information
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
hist.AuditExecute = True

# PODIO algorithm
out = PodioOutput("out", OutputLevel=INFO)
out.outputCommands = ["drop *"]
out.filename = "fccee_samplingFraction_inclinedEcal.root"

event_counter = EventCounter('event_counter')
event_counter.Frequency = 10

# ApplicationMgr
ApplicationMgr(TopAlg=[event_counter, input_reader, hist, out],
               EvtSel='NONE',
               EvtMax=-1,
               # order is important, as GeoSvc is needed by G4SimSvc
               ExtSvc=[geoservice, podioevent, audsvc],
               OutputLevel=INFO,
               StopOnSignal=True
               )
