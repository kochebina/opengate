import gam_g4 as g4
import itk
import numpy as np
import gam
from scipy.spatial.transform import Rotation


class DoseActor(g4.GamDoseActor, gam.ActorBase):
    """
    DoseActor: compute a 3D edep/dose map for deposited
    energy/absorbed dose in the attached volume

    The dose map is parameterized with:
        - dimension (number of voxels)
        - spacing (voxel size)
        - translation (according to the coordinate system of the "attachedTo" volume)
        - no rotation

    Position:
    - by default: centered according to the "attachedTo" volume center
    - if the attachedTo volume is an Image AND the option "img_coord_system" is True:
        the origin of the attachedTo image is used for the output dose.
        Hence, the dose can be superimposed with the attachedTo volume

    Options
        - edep only for the moment
        - later: add dose, uncertainty, squared etc 

    """

    type_name = 'DoseActor'

    def set_default_user_info(user_info):
        gam.ActorBase.set_default_user_info(user_info)
        # required user info, default values
        mm = gam.g4_units('mm')
        user_info.dimension = [10, 10, 10]
        user_info.spacing = [1 * mm, 1 * mm, 1 * mm]
        user_info.save = 'edep.mhd'  # FIXME change to 'output' ?
        user_info.translation = [0, 0, 0]
        user_info.img_coord_system = None
        user_info.uncertainty = True

    def __init__(self, user_info):
        gam.ActorBase.__init__(self, user_info)
        g4.GamDoseActor.__init__(self, user_info.__dict__)
        # default image (py side)
        self.py_edep_image = None
        self.py_temp_image = None
        self.py_square_image = None
        self.py_last_id_image = None
        self.uncertainty_image = None
        self.img_center = None
        self.first_run = None
        self.output_origin = None

    def __str__(self):
        u = self.user_info
        s = f'DoseActor "{u.name}": dim={u.dimension} spacing={u.spacing} {u.save} tr={u.translation}'
        return s

    def initialize(self):
        gam.ActorBase.initialize(self)
        # create itk image (py side)
        size = np.array(self.user_info.dimension)
        spacing = np.array(self.user_info.spacing)
        self.py_edep_image = gam.create_3d_image(size, spacing)
        # compute the center, using translation and half pixel spacing
        self.img_center = -size * spacing / 2.0 + spacing / 2.0 + self.user_info.translation
        # for initialization during the first run
        self.first_run = True

    def StartSimulationAction(self):
        # Compute the transformation from global (world) position
        # to local (attachedTo volume) position and set it to the itk image
        # This will be used by the GamDoseActor (cpp side)
        vol_name = self.user_info.mother
        vol = self.simulation.volume_manager.get_volume(vol_name)
        # get the first volume (if repeater)
        vol = vol.g4_physical_volumes[0].GetName()
        translation, rotation = gam.get_transform_world_to_local(vol)
        t = gam.get_translation_from_rotation_with_center(Rotation.from_matrix(rotation), self.img_center)
        # compute and set the origin: the center of the volume
        # during the run, the origin is set such that dose volume is centered (+translation)
        # according to the attached volume coordinate system
        origin = translation + self.img_center - t
        self.py_edep_image.SetOrigin(origin)
        self.py_edep_image.SetDirection(rotation)

        # FIXME for multiple run and motion
        if not self.first_run:
            gam.warning(f'Not implemented yet: DoseActor with several runs')
        # send itk image to cpp side, copy data only the first run.
        gam.update_image_py_to_cpp(self.py_edep_image, self.cpp_edep_image, self.first_run)

        # for uncertainty ## FIXME add flag
        if self.user_info.uncertainty:
            print('ici')
            self.py_temp_image = gam.create_image_like(self.py_edep_image)
            self.py_square_image = gam.create_image_like(self.py_edep_image)
            self.py_last_id_image = gam.create_image_like(self.py_edep_image)
            print('ok')
            gam.update_image_py_to_cpp(self.py_temp_image, self.cpp_temp_image, self.first_run)
            gam.update_image_py_to_cpp(self.py_square_image, self.cpp_square_image, self.first_run)
            gam.update_image_py_to_cpp(self.py_last_id_image, self.cpp_last_id_image, self.first_run)
            print('la')

        self.first_run = False

        # If attached to a voxelized volume, may use its coord system
        vol_name = self.user_info.mother
        vol_type = self.simulation.get_volume_user_info(vol_name).type_name
        self.output_origin = self.img_center
        if vol_type == 'Image':
            if self.user_info.img_coord_system:
                vol = self.simulation.volume_manager.volumes[vol_name]
                # translate the output dose map so that its center correspond to the image center
                # the origin is thus the center of the first voxel
                img_info = gam.get_image_info(vol.image)
                dose_info = gam.get_image_info(self.py_edep_image)
                img_size = img_info.size * img_info.spacing
                dose_size = dose_info.size * dose_info.spacing
                self.output_origin = (img_size - dose_size) / 2.0
                self.output_origin += img_info.origin - img_info.spacing / 2.0 + dose_info.spacing / 2
                self.output_origin += self.user_info.translation

        else:
            if self.user_info.img_coord_system:
                gam.warning(f'DoseActor "{self.user_info.name}" has '
                            f'the flag img_coord_system set to True, '
                            f'but it is not attached to an Image '
                            f'volume ("{vol_name}", of type "{vol_type}"). '
                            f'So the flag is ignored.')

    def EndSimulationAction(self):
        g4.GamDoseActor.EndSimulationAction(self)
        # Get the itk image from the cpp side
        # Currently a copy. Maybe latter as_pyarray ?
        self.py_edep_image = gam.get_cpp_image(self.cpp_edep_image)
        # set the property of the output image:
        # in the coordinate system of the attached volume
        # FIXME no direction for the moment ?
        self.py_edep_image.SetOrigin(self.output_origin)
        # FIXME: write the image at the end of the run, but
        # uncertainty ? Need to be called before writing edep (to terminate temp events)
        if self.user_info.uncertainty:
            self.compute_uncertainty()
            n = self.user_info.save.replace('.mhd', '_uncertainty.mhd')
            print(n)
            itk.imwrite(self.uncertainty_image, n)
        # maybe different for several runs
        itk.imwrite(self.py_edep_image, self.user_info.save)

    def compute_uncertainty(self):
        self.py_temp_image = gam.get_cpp_image(self.cpp_temp_image)
        self.py_square_image = gam.get_cpp_image(self.cpp_square_image)
        self.py_last_id_image = gam.get_cpp_image(self.cpp_last_id_image)

        self.py_temp_image.SetOrigin(self.output_origin)
        self.py_square_image.SetOrigin(self.output_origin)
        self.py_last_id_image.SetOrigin(self.output_origin)

        # complete edep with temp values
        edep = itk.array_view_from_image(self.py_edep_image)
        tmp = itk.array_view_from_image(self.py_temp_image)
        edep = edep + tmp
        self.py_edep_image = itk.image_from_array(edep)
        self.py_edep_image.CopyInformation(self.py_temp_image)

        # complete square with temp values
        square = itk.array_view_from_image(self.py_square_image)
        square = square + tmp * tmp
        self.py_square_image = itk.image_from_array(square)
        self.py_square_image.CopyInformation(self.py_temp_image)

        # uncertainty image
        self.uncertainty_image = gam.create_image_like(self.py_edep_image)
        unc = itk.array_view_from_image(self.uncertainty_image)
        N = unc.size
        print('N', N)
        unc = np.sqrt(1 / (N - 1) * (square / N - np.power(edep / N, 2)))
        unc = np.divide(unc, edep / N, out=np.ones_like(unc), where=edep != 0)
        self.uncertainty_image = itk.image_from_array(unc)
        self.uncertainty_image.CopyInformation(self.py_temp_image)
        self.uncertainty_image.SetOrigin(self.output_origin)

        # self.py_edep_image.SetSpacing(np.array(self.user_info.spacing))
        itk.imwrite(self.py_square_image, "square.mhd")
        itk.imwrite(self.py_temp_image, "temp.mhd")
        itk.imwrite(self.py_last_id_image, "lastid.mhd")
        itk.imwrite(self.uncertainty_image, "uncer.mhd")
