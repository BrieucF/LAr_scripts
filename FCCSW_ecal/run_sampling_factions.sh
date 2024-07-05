# Careful, you can not provide the rootfile name without '?', it crashes
python FCC_calo_analysis_cpp/plot_samplingFraction.py ./calibration_output_pdgID_11_pMin_?_pMax_?_thetaMin_55_thetaMax_125_ddsim_LAr.root 10 -r 10000 --preview -outputfolder FCC_calo_analysis_cpp/plots_sampling_fraction_$(date +"%y%m%d") --sed

