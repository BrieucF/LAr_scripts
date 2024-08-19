from Configurables import GeoSvc
from Configurables import ApplicationMgr
from Configurables import CreateFCCeeCaloNeighbours
import os
from Gaudi.Configuration import INFO, DEBUG

# produce neighbour map also for HCal
doHCal = False

# only relevant if doHCal is True, set to True
# for combined ECal+HCal topoclusters
linkECalHCalBarrels = True

# Detector geometry
geoservice = GeoSvc("GeoSvc")
# if K4GEO is empty, this should use relative path to working directory
path_to_detector = os.environ.get("K4GEO", "")
print(path_to_detector)
detectors_to_use = [
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml'
]

# prefix all xmls with path_to_detector
geoservice.detectors = [os.path.join(
    path_to_detector, _det) for _det in detectors_to_use]
geoservice.OutputLevel = INFO

if doHCal:
    # create the neighbour file for ECAL+HCAL barrel cells
    neighbours = CreateFCCeeCaloNeighbours("neighbours",
                                           outputFileName="neighbours_map_ecalB_thetamodulemerged_hcalB_thetaphi.root",
                                           readoutNames=[
                                               "ECalBarrelModuleThetaMerged", "BarHCal_Readout_phitheta"],
                                           systemNames=["system", "system"],
                                           systemValues=[4, 8],
                                           activeFieldNames=["layer", "layer"],
                                           activeVolumesNumbers=[11, 13],
                                           activeVolumesTheta=[
                                               [],
                                               [
                                                   0.788969, 0.797785, 0.806444, 0.814950, 0.823304,
                                                   0.839573, 0.855273, 0.870425, 0.885051, 0.899172,
                                                   0.912809, 0.938708, 0.962896
                                               ]
                                           ],
                                           includeDiagonalCells=False,
                                           connectBarrels=linkECalHCalBarrels,
                                           OutputLevel=DEBUG)
else:
    # create the neighbour file for ECAL barrel cells
    neighbours = CreateFCCeeCaloNeighbours("neighbours",
                                           outputFileName="neighbours_map_ecalB_thetamodulemerged.root",
                                           readoutNames=[
                                               "ECalBarrelModuleThetaMerged"],
                                           systemNames=["system"],
                                           systemValues=[4],
                                           activeFieldNames=["layer"],
                                           activeVolumesNumbers=[11],
                                           includeDiagonalCells=False,
                                           connectBarrels=False,
                                           OutputLevel=DEBUG)

# ApplicationMgr
ApplicationMgr(TopAlg=[],
               EvtSel='NONE',
               EvtMax=1,
               # order is important, as GeoSvc is needed by G4SimSvc
               ExtSvc=[geoservice, neighbours],
               OutputLevel=INFO
               )
