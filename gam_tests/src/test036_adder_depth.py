#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gam_gate as gam
from scipy.spatial.transform import Rotation
import uproot
import matplotlib.pyplot as plt

paths = gam.get_default_test_paths(__file__, 'gate_test036_adder_depth')

# create the simulation
sim = gam.Simulation()

# main options
ui = sim.user_info
ui.g4_verbose = False
ui.visu = False
ui.number_of_threads = 1

# units
m = gam.g4_units('m')
cm = gam.g4_units('cm')
keV = gam.g4_units('keV')
mm = gam.g4_units('mm')
Bq = gam.g4_units('Bq')
kBq = 1000 * Bq

# world size
world = sim.world
world.size = [2 * m, 2 * m, 2 * m]

# material
sim.add_material_database(paths.data / 'GateMaterials.db')

# fake spect head
head = sim.add_volume('Box', 'SPECThead')
head.size = [55 * cm, 42 * cm, 18 * cm]
head.material = 'G4_AIR'

# crystal
crystal = sim.add_volume('Box', 'crystal')
crystal.mother = 'SPECThead'
crystal.size = [55 * cm, 42 * cm, 2 * cm]
crystal.translation = [0, 0, 4 * cm]
crystal.material = 'Plastic'
crystal.color = [1, 0, 0, 1]

# pixel crystal
crystal_pixel = sim.add_volume('Box', 'crystal_pixel')
crystal_pixel.mother = crystal.name
crystal_pixel.size = [0.5 * cm, 0.5 * cm, 2 * cm]
crystal_pixel.material = 'NaITl'
crystal_pixel.color = [1, 1, 0, 1]

# geom = 'repeat'
geom = 'param'
# geom = 'repeat'
size = [100, 80, 1]
tr = [0.5 * cm, 0.5 * cm, 0]

if geom == 'repeat':
    le = gam.repeat_array(crystal_pixel.name, size, tr)
    crystal_pixel.translation = None
    crystal_pixel.rotation = None
    crystal_pixel.repeat = le

if geom == 'param':
    crystal_repeater = gam.build_param_repeater(sim, crystal.name, crystal_pixel.name, size, tr)

# FIXME add a second head
'''head.translation = None
head.rotation = None
le = gam.repeat_array(head.name, [1, 1, 2], [0, 0, 30 * cm])
print(le)
le[1]['rotation'] = Rotation.from_euler('X', 180, degrees=True).as_matrix()
head.repeat = le'''

# physic list
p = sim.get_physics_user_info()
p.physics_list_name = 'G4EmStandardPhysics_option4'
p.enable_decay = False
cuts = p.production_cuts
cuts.world.gamma = 0.01 * mm
cuts.world.electron = 0.01 * mm
cuts.world.positron = 1 * mm
cuts.world.proton = 1 * mm

# default source for tests
activity = 50 * kBq / ui.number_of_threads
source = sim.add_source('Generic', 'Default')
source.particle = 'gamma'
source.energy.mono = 333 * keV
source.position.type = 'sphere'
source.position.radius = 3 * cm
source.position.translation = [0, 0, -15 * cm]
source.direction.type = 'momentum'
source.direction.momentum = [0, 0, 1]
source.activity = activity

# default source for tests
'''source = sim.add_source('Generic', 'Default1')
source.particle = 'gamma'
source.energy.mono = 333 * keV
source.position.type = 'sphere'
source.position.radius = 3 * cm
source.position.translation = [0, 0, -15 * cm]
source.direction.type = 'momentum'
source.direction.momentum = [0, 0, -1]
source.activity = activity'''

# add stat actor
sim.add_actor('SimulationStatisticsActor', 'Stats')

# hits collection
hc = sim.add_actor('HitsCollectionActor', 'Hits')
hc.mother = crystal.name
hc.output = paths.output / 'test036.root'
hc.attributes = ['KineticEnergy', 'PostPosition', 'PrePosition',
                 'TotalEnergyDeposit', 'GlobalTime',
                 'TrackVolumeName', 'TrackID',  # 'Test',
                 'ProcessDefinedStep',
                 'PreStepUniqueVolumeID',
                 'TrackVolumeCopyNo', 'TrackVolumeInstanceID']

# singles collection
sc = sim.add_actor('HitsAdderActor', 'Singles')
sc.mother = crystal.name
sc.input_hits_collection = 'Hits'
sc.policy = 'EnergyWinnerPosition'
# sc.policy = 'EnergyWeightedCentroidPosition'
# same filename, there will be two branches in the file
sc.output = hc.output

sec = gam.g4_units('second')
ui.running_verbose_level = 2
# sim.run_timing_intervals = [[0, 0.33 * sec], [0.33 * sec, 0.66 * sec], [0.66 * sec, 1 * sec]]

# create G4 objects
sim.initialize()

# start simulation
sim.start()

# stat
gam.warning('Compare stats')
stats = sim.get_actor('Stats')
print(stats)
print(f'Number of runs was {stats.counts.run_count}. Set to 1 before comparison')
stats.counts.run_count = 1  # force to 1
stats_ref = gam.read_stat_file(paths.gate_output / 'stats.txt')
is_ok = gam.assert_stats(stats, stats_ref, tolerance=0.07)

# root compare HITS
print()
gam.warning('Compare HITS')
gate_file = paths.gate_output / 'spect.root'
checked_keys = ['posX', 'posY', 'posZ', 'edep', 'time', 'trackId']
# FIXME -> first, remove hit with edep ==0 and compare
gam.compare_root(gate_file, hc.output, "Hits", "Hits", checked_keys, paths.output / 'test036_hits.png')

# Root compare SINGLES
print()
gam.warning('Compare SINGLES')
gate_file = paths.gate_output / 'spect.root'
checked_keys = ['time', 'globalPosX', 'globalPosY', 'globalPosZ', 'energy']
keys1, keys2, scalings, tols = gam.get_keys_correspondence(checked_keys)
tols[4] = 0.01  # energy
gam.compare_root3(gate_file, sc.output, "Singles", "Singles",
                  keys1, keys2, tols, scalings,
                  paths.output / 'test036_singles.png')

# this is the end, my friend
gam.test_ok(is_ok)
