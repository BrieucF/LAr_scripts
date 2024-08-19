from Configurables import GeoSvc
from Configurables import ApplicationMgr
from Configurables import CreateFCCeeCaloNoiseLevelMap
#from Configurables import ReadNoiseVsThetaFromFileTool
from Configurables import NoiseCaloCellsVsThetaFromFileTool
from Configurables import ConstNoiseTool
from Configurables import CellPositionsECalBarrelModuleThetaSegTool
import os
from Gaudi.Configuration import INFO, DEBUG

doHCal = True

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

# readout names for ECAL and HCAL (latter is ignored if doHCal is False)
ecalBarrelReadoutName = "ECalBarrelModuleThetaMerged"
hcalBarrelReadoutName = "BarHCal_Readout_phitheta"
# names of file and histograms with noise per layer vs theta for barrel ECAL
BarrelNoisePath = os.environ['FCCBASEDIR'] + \
    "/LAr_scripts/data/elecNoise_ecalBarrelFCCee_theta.root"
ecalBarrelNoiseRMSHistName = "h_elecNoise_fcc_"

# cell positioning and noise tool for the ecal barrel
ECalBcells = CellPositionsECalBarrelModuleThetaSegTool("CellPositionsECalBarrel",
                                                       readoutName=ecalBarrelReadoutName)

#ECalNoiseTool = ReadNoiseVsThetaFromFileTool("ReadNoiseFromFileToolECal",
#                                             useSegmentation=False,
#                                             cellPositionsTool=ECalBcells,
#                                             readoutName=ecalBarrelReadoutName,
#                                             noiseFileName=BarrelNoisePath,
#                                             elecNoiseHistoName=ecalBarrelNoiseHistName,
#                                             setNoiseOffset=False,
#                                             activeFieldName="layer",
#                                             addPileup=False,
#                                             numRadialLayers=11,
#                                             scaleFactor=1 / 1000.,  # MeV to GeV
#                                             OutputLevel=INFO)

ECalNoiseTool = NoiseCaloCellsVsThetaFromFileTool("NoiseCaloCellsVsThetaFromFileTool",
                                                  cellPositionsTool=ECalBcells,
                                                  readoutName=ecalBarrelReadoutName,
                                                  noiseFileName=BarrelNoisePath,
                                                  elecNoiseRMSHistoName=ecalBarrelNoiseRMSHistName,
                                                  setNoiseOffset=False,
                                                  activeFieldName="layer",
                                                  addPileup=False,
                                                  numRadialLayers=11,
                                                  scaleFactor=1 / 1000.,  # MeV to GeV
                                                  OutputLevel=DEBUG)


if doHCal:
    # noise tool for the HCAL barrel
    # HCAL noise file has yet to be created/implemented
    # HCalNoiseTool = ReadNoiseFromFileTool("ReadNoiseFromFileToolHCal",
    #                                       readoutName = hcalBarrelReadoutName,
    #                                       noiseFileName = BarrelNoisePath,
    #                                       elecNoiseHistoName = ecalBarrelNoiseHistName,
    #                                       setNoiseOffset = False,
    #                                       activeFieldName = "layer",
    #                                       addPileup = False,
    #                                       numRadialLayers = 12,
    #                                       scaleFactor = 1/1000., #MeV to GeV
    #                                       OutputLevel = INFO)
    # ConstNoiseTool provides constant noise for all calo subsystems
    # here we are going to use it only for hcal barrel
    HCalNoiseTool = ConstNoiseTool("ConstNoiseTool",
                                   detectors = [ "HCAL_Barrel"],
                                   detectorsNoiseRMS = [0.0115/4],
                                   OutputLevel = DEBUG)
    #HCalNoiseTool = ConstNoiseTool("ConstNoiseTool",
    #                               detectors = ["ECAL_Barrel", "ECAL_Endcap", "HCAL_Barrel", "HCAL_Endcap"],
    #                               detectorsNoiseRMS = [0.0075/4, 0.0075/4, 0.0115/4, 0.0115/4],
    #                               OutputLevel = DEBUG)

    # create the noise file for ECAL+HCAL barrel cells
    # the tool wants the system IDs, maybe we could have passed the names instead
    noisePerCell = CreateFCCeeCaloNoiseLevelMap("noisePerCell",
                                                ECalBarrelNoiseTool=ECalNoiseTool,
                                                ecalBarrelSysId=4,
                                                HCalBarrelNoiseTool=HCalNoiseTool,
                                                hcalBarrelSysId=8,
                                                readoutNames=[
                                                    ecalBarrelReadoutName, hcalBarrelReadoutName],
                                                systemNames=[
                                                    "system", "system"],
                                                systemValues=[4, 8],
                                                activeFieldNames=[
                                                    "layer", "layer"],
                                                activeVolumesNumbers=[11, 13],
                                                activeVolumesTheta=[
                                                    [],
                                                    [
                                                        0.788969, 0.797785, 0.806444, 0.81495, 0.823304,
                                                        0.839573, 0.855273, 0.870425, 0.885051, 0.899172,
                                                        0.912809, 0.938708, 0.962896
                                                    ]
                                                ],
                                                outputFileName="cellNoise_map_electronicsNoiseLevel_ecalB_thetamodulemerged_hcalB_thetaphi.root",
                                                OutputLevel=DEBUG)
else:
    # create the noise file for ECAL barrel cells
    noisePerCell = CreateFCCeeCaloNoiseLevelMap("noisePerCell",
                                                ECalBarrelNoiseTool=ECalNoiseTool,
                                                ecalBarrelSysId=4,
                                                HCalBarrelNoiseTool=None,
                                                hcalBarrelSysId=8,
                                                readoutNames=[ecalBarrelReadoutName],
                                                systemNames=["system"],
                                                systemValues=[4],
                                                activeFieldNames=["layer"],
                                                activeVolumesNumbers=[11],
                                                activeVolumesTheta=[[]],
                                                outputFileName="cellNoise_map_electronicsNoiseLevel_ecalB_thetamodulemerged.root",
                                                OutputLevel=DEBUG)


# ApplicationMgr
ApplicationMgr(TopAlg=[],
               EvtSel='NONE',
               EvtMax=1,
               # order is important, as GeoSvc is needed by G4SimSvc
               ExtSvc=[geoservice, noisePerCell],
               OutputLevel=INFO
               )
