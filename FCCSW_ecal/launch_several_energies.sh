python condor_submit_fccsw.py -outputFolder /eos/user/b/brfranco/rootfile_storage/ -campaignName $(date +"%y%m%d")_energies_10kevt_topoAndSW_noNoise \
 -gaudiConfig $PWD/run_thetamodulemerged.py -jobType caloReco \
 -energies 300 650 1000 2000 5000 10000 20000 30000 45000 100000 150000 200000 -polarAngles 90 -energiesForDifferentPolarAngles 10000 \
 -nEvt 10000 -originalNjobs 2 -condorQueue microcentury --submit
