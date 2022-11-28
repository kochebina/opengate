from .BoxVolume import *
from .SphereVolume import *
from .TrapVolume import *
from .ImageVolume import *
from .TubsVolume import *
from .ConsVolume import *
from .PolyhedraVolume import *
from .TrdVolume import *
from .BooleanVolume import *
from .RepeatParametrisedVolume import *

volume_type_names = {
    BoxVolume,
    SphereVolume,
    TrapVolume,
    ImageVolume,
    TubsVolume,
    PolyhedraVolume,
    ConsVolume,
    TrdVolume,
    BooleanVolume,
    RepeatParametrisedVolume,
}
volume_builders = gate.make_builders(volume_type_names)

# G4Tubs G4CutTubs G4Cons G4Para G4Trd
# G4Torus (G4Orb not needed) G4Tet
# G4EllipticalTube G4Ellipsoid G4EllipticalCone
# G4Paraboloid G4Hype
# specific: G4Polycone G4GenericPolycone Polyhedra
# G4ExtrudedSolid G4TwistedBox G4TwistedTrap G4TwistedTrd G4GenericTrap
# G4TwistedTubs

"""
http://geant4-userdoc.web.cern.ch/geant4-userdoc/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html#constructed-solid-geometry-csg-solids
"""


def box_add_size(box, thickness):
    box.size = [x + thickness for x in box.size]


def cons_add_size(cons, thickness):
    cons.rmax1 += thickness / 2
    cons.rmax2 += thickness / 2
    cons.dz += thickness


def get_volume_bounding_limits(simulation, volume_name):
    """
    Return the min and max 3D points of the bounding box of the given volume
    """
    v = simulation.get_volume_user_info(volume_name)
    s = simulation.get_solid_info(v)
    pMin = s.bounding_limits[0]
    pMax = s.bounding_limits[1]
    return pMin, pMax


def get_volume_bounding_box_size(simulation, volume_name):
    """
    Return the size of the bounding box of the given volume
    """
    pMin, pMax = get_volume_bounding_limits(simulation, volume_name)
    return [pMax[0] - pMin[0], pMax[1] - pMin[1], pMax[2] - pMin[2]]


def translate_point_to_volume(simulation, volume, top, x):
    """

    Consider the point x in the current volume and return the coordinate of x in the top volume
    (that must be an ancestor).
    Translation only, do not consider rotation.
    """
    while volume.name != top:
        x += volume.translation
        volume = simulation.get_volume_user_info(volume.mother)
    return x


# correspondence element names <> symbol
elements_name_symbol = {
    "Hydrogen": "H",
    "Carbon": "C",
    "Nitrogen": "N",
    "Oxygen": "O",
    "Sodium": "Na",
    "Magnesium": "Mg",
    "Phosphor": "P",
    "Sulfur": "S",
    "Chlorine": "Cl",
    "Argon": "Ar",
    "Potassium": "K",
    "Calcium": "Ca",
    "Titanium": "Ti",
    "Copper": "Cu",
    "Zinc": "Zn",
    "Silver": "Ag",
    "Tin": "Sn",
}