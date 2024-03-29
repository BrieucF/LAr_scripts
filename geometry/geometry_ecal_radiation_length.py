from math import *

# Compute calo depth to reach 22 X0 and count number of cells w.r.t component thickness and calo radius, all computations done in the inner radius
#FIXME refine the projection on circle

# X0 units are in cm from PDG, I use 1/X0 for calculus convenience
# (units 1/cm)
lar_x0 = 1/14.0
lead_x0 = 1/0.5612
W_x0 = 1/0.3504
absorber_x0 = lead_x0
#absorber_x0 = W_x0
glue_x0 = 1/20.209 #LArCaloGlue from geant4 xml dd4hep
steel_x0 = 1/1.775 # lArCaloSteel from geant4 xml dd4hep
cryostat_x0 = 1/8.897 # Aluminiium 
pcb_x0 = 1/15.92 # FR4 (61% glass fiber and 39% resin) 
g10_x0 = 1/19.4 # for the presampler 'absorber'


lar_thickness = 1.2 # mm
pcb_thickness = 1.2 # mm
# absorbers
glue_thickness = 0.2 # mm consider immediately the two sides
steel_thickness = 0.4 # mm consider immediately the two sides
absorber_thickness = 1.4 # mm there is only one (sandwiched)
cell_size = (lar_thickness * 2 + absorber_thickness + glue_thickness + steel_thickness + pcb_thickness) # mm 

pre_sampler_radial_length = 15.0 # mm
normal_cells_radial_length = 35.0 # mm

cryostat_thickness_in = 50 # mm
cryostat_thickness_out = 100 # mm

inner_margin_for_services = 10 # mm
outer_margin_for_services = 50 # mm

inclination = 50 #degrees w.r.t. the radial direction
#inclination = 80 #degrees w.r.t. the radial direction
factor_thicknessPerpendicularPcb_to_radialLength = 1 / cos(radians(90 - inclination))
factor_thicknessPerpendicularPcb_to_imprintOnCircle = 1 / cos(radians(inclination))
factor_radialLength_to_lengthAlongPcb = 1 / cos(radians(inclination))
factor_lengthParallelPcb_to_imprintOnCircle = cos(radians(90 - inclination))

print("Gap thickness: %f mm, absorber thickness %f mm, pcb thickness %f mm"%(lar_thickness, glue_thickness + steel_thickness + absorber_thickness, pcb_thickness))

# Compute the total number of layers in phi
cryostat_starting_radius = 2100 # mm
#cryostat_starting_radius = 1870 # mm

cells_starting_radius = cryostat_starting_radius + cryostat_thickness_in + inner_margin_for_services
print("Readout cells start at %f mm"%cells_starting_radius)
circumferance = 2 * pi * cells_starting_radius
cellSize_circle_projected = cell_size * factor_thicknessPerpendicularPcb_to_imprintOnCircle

n_cells = circumferance / cellSize_circle_projected

print("Need %f cells to cover the 2*pi*r in phi"%n_cells)
print("Phi granularity if we read two cells together: %f"%(2*pi/(n_cells/2)))

n_cells_per_module = 64.0
n_contrcution_modules = 16.0
n_module = n_cells/n_cells_per_module
n_module_rounded = round(n_module)
print("If we want %f cell per module, we would have %f modules... Choosing the closest rounding (%d) and rederivinbg everything:"%(n_cells_per_module, n_module, n_module_rounded))
total_number_of_cell = n_cells_per_module * n_module_rounded
print("New number of cells: %f"%total_number_of_cell)
new_gap_size_inner = (((circumferance/(total_number_of_cell * factor_thicknessPerpendicularPcb_to_imprintOnCircle)) - absorber_thickness - pcb_thickness - glue_thickness - steel_thickness))/2.0 #divided by 2 because two gaps
print("New gap size at inner radius after having rounded the number of cells is %f mm"%new_gap_size_inner)
lar_traversed_straight_particle = new_gap_size_inner * factor_thicknessPerpendicularPcb_to_radialLength
print("Straight particle traverse %f mm of LAr"%lar_traversed_straight_particle)
lar_thickness = new_gap_size_inner

cell_size = (lar_thickness * 2 + absorber_thickness + glue_thickness + steel_thickness + pcb_thickness) # mm 
cellSize_circle_projected = cell_size * factor_thicknessPerpendicularPcb_to_imprintOnCircle

print("------------------------")

x0_toReach = 22
x0 = 0


# compute the X0 from services, cryostat etc
x0_services = ((cryostat_thickness_in + cryostat_thickness_out) * cryostat_x0 + (inner_margin_for_services + outer_margin_for_services) * lar_x0) / 10.0
x0 += x0_services

# compute X0 of the presampler
presampler_length = pre_sampler_radial_length * factor_radialLength_to_lengthAlongPcb # mm. without taking into account inclination, number is its bare length, measured parallel to the readout
x0_presampler_cell = (lar_thickness * lar_x0 * 2 + absorber_thickness * g10_x0  + glue_thickness * glue_x0 + steel_thickness * steel_x0 + pcb_thickness * pcb_x0) * factor_thicknessPerpendicularPcb_to_radialLength / 10.0 # / 10 because thickness provided in mm while X0 in 1/cm
number_of_presampler_cells_crossed = pre_sampler_radial_length / (cell_size * factor_thicknessPerpendicularPcb_to_radialLength)
print("One crosses %f presampler cells with pre-sampler length of %f mm (measured parallely to the readout)"%(number_of_presampler_cells_crossed, presampler_length))
x0_presampler = x0_presampler_cell * number_of_presampler_cells_crossed
x0 += x0_presampler


# Compute X0 when crossing one cell(abs gap pcb gap), taking into account the inclination w.r.t. radial angle
x0_per_normal_cell = (lar_thickness * lar_x0 * 2 + absorber_thickness * absorber_x0 + glue_thickness * glue_x0 + steel_thickness * steel_x0 + pcb_thickness * pcb_x0) * factor_thicknessPerpendicularPcb_to_radialLength / 10.0 # / 10 because thickness provided in mm while X0 in 1/cm 
print("X0 per normal cell: ", x0_per_normal_cell)

n_layer = 0
while(x0 < x0_toReach):
   n_layer += 1
   x0 += x0_per_normal_cell

print("After %d layers (excluding presampler), we reach %f X0 (at eta = 0)"%(n_layer, x0))

total_calo_thickness = pre_sampler_radial_length + cell_size * n_layer * factor_thicknessPerpendicularPcb_to_radialLength # mm

print("It corresponds to a sensitive calo thickness of %f cm"%(total_calo_thickness / 10.0))

print("Length of the plate parallel to them: %f cm (rectangular triangle approximation)"%((total_calo_thickness / 10.0)/cos(radians(inclination))))

total_calo_thickness_withServices = total_calo_thickness + inner_margin_for_services + outer_margin_for_services + cryostat_thickness_in + cryostat_thickness_out # mm

print("Including cryostat and services: it corresponds to a calo thickness of %f cm"%(total_calo_thickness_withServices / 10))

# compute gap thickness at the outer radius based on dilution factor from circumference inner, circumference outer
outer_sensitive_radius = cells_starting_radius + total_calo_thickness
print("Outer sensitive radius: %f"%outer_sensitive_radius)
dilution_factor =  outer_sensitive_radius / cells_starting_radius 
gap_size_outer = new_gap_size_inner * dilution_factor
print("Outer gap thicknes: %f mm"%gap_size_outer)
print("Ratio outer/inner gap thickness: %f"%(gap_size_outer/new_gap_size_inner))
print("Smallest phi granularity %f degrees if we read the two gaps from one cell with one trace"%(360/float(total_number_of_cell)))
print("Smallest phi granularity %f miliradians if we read the two gaps from one cell with one trace"%(radians(360/float(total_number_of_cell))*1000))
print("Smallest cell size at inner radius %f mm if we read the two gaps from one cell with one trace"%(circumferance/float(total_number_of_cell)))
print("Even though the inclination of the readout pcb spread the phi information (large circle imprint), e.g. a MIP will hit more than one cell and taking the barycenter should lead to resolution similar to the above granularity")
print("Moliere radius ~4cm [to be computed precisely]")
# checking imprint in phi from pcb segmentation at 90 degrees
readout_cell_length_parallel = normal_cells_radial_length * factor_radialLength_to_lengthAlongPcb
readout_cell_phiImprint_on_circle = readout_cell_length_parallel * factor_lengthParallelPcb_to_imprintOnCircle 
readout_cell_phiAngle = readout_cell_phiImprint_on_circle / (cells_starting_radius + pre_sampler_radial_length)

print("Distance imprint in phi from the readout cell projected on circle: %f mm"%readout_cell_phiImprint_on_circle)
print("Angle imprint in phi from the readout cell projected on circle, for the first normal cell (get smaller towards high R): %f radians"%readout_cell_phiAngle)
