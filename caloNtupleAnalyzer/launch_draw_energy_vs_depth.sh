#folder=plots_averaged_showerShape_210218/
folder=plots_averaged_showerShape_210219/
#folder=plots_averaged_showerShape_55degrees_210223
#python draw_energy_vs_depth.py -inputFiles $folder/averaged_shower_shape_1dot0.root $folder/averaged_shower_shape_10dot0.root $folder/averaged_shower_shape_45dot0.root $folder/averaged_shower_shape_200dot0.root -outputPostfix 55degrees
python draw_energy_vs_depth.py -inputFiles $folder/averaged_shower_shape_10dot0.root $folder/averaged_shower_shape_200dot0.root
