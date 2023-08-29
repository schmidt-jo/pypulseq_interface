import typing

import numpy as np
import simple_parsing as sp
import dataclasses as dc
import logging

log_module = logging.getLogger(__name__)


@dc.dataclass
class ImageAcqParameters(sp.Serializable):
    # define all recon parameters we ship in interface
    n_read: int = None
    n_phase: int = None
    n_slice: int = None

    resolution_read: float = None
    resolution_phase: float = None
    resolution_slice: float = None

    read_dir: str = None
    os_factor: int = None
    acc_read: bool = None
    acc_factor_phase: float = None

    etl: int = None
    te: list = None


@dc.dataclass
class NavigatorAcqParameters(ImageAcqParameters):
    lines_per_nav: int = None
    num_of_nav: int = None
    nav_acc_factor: int = None
    nav_resolution_scaling: float = None


@dc.dataclass
class ReconParameters(sp.Serializable):
    multi_echo_img: ImageAcqParameters = ImageAcqParameters()
    navigator_img: NavigatorAcqParameters = NavigatorAcqParameters()

    def set_recon_params(
            self, img_n_read: int, img_n_phase: int, img_n_slice: int, img_resolution_read: float,
            img_resolution_phase: float, img_resolution_slice: float, read_dir: str, os_factor: int,
            acc_read: bool, acc_factor_phase: float, etl: int, te: typing.Union[list, np.ndarray]
    ):
        if isinstance(te, np.ndarray):
            te = te.tolist()
        self.multi_echo_img.n_read = img_n_read
        self.multi_echo_img.n_phase = img_n_phase
        self.multi_echo_img.n_slice = img_n_slice
        self.multi_echo_img.resolution_read = img_resolution_read
        self.multi_echo_img.resolution_phase = img_resolution_phase
        self.multi_echo_img.resolution_slice = img_resolution_slice
        self.multi_echo_img.read_dir = read_dir
        self.multi_echo_img.acc_read = acc_read
        self.multi_echo_img.acc_factor_phase = acc_factor_phase
        self.multi_echo_img.etl = etl
        self.multi_echo_img.te = te
        self.multi_echo_img.os_factor = os_factor

    def set_navigator_params(
            self, lines_per_nav: int, num_of_nav: int, nav_acc_factor: int, nav_resolution_scaling: float
    ):
        self.navigator_img.n_read = int(self.multi_echo_img.n_read * nav_resolution_scaling)
        self.navigator_img.n_phase = int(self.multi_echo_img.n_phase * nav_resolution_scaling)
        self.navigator_img.n_slice = int(self.multi_echo_img.n_slice * nav_resolution_scaling)
        self.navigator_img.resolution_read = self.multi_echo_img.n_read / nav_resolution_scaling
        self.navigator_img.resolution_phase = self.multi_echo_img.n_phase / nav_resolution_scaling
        self.navigator_img.resolution_slice = self.multi_echo_img.n_slice / nav_resolution_scaling
        self.navigator_img.read_dir = self.multi_echo_img.read_dir
        self.navigator_img.acc_read = False
        self.navigator_img.acc_factor_phase = nav_acc_factor
        self.navigator_img.lines_per_nav = lines_per_nav
        self.navigator_img.num_of_nav = num_of_nav
        self.navigator_img.nav_acc_factor = nav_acc_factor,
        self.navigator_img.nav_resolution_scaling = nav_resolution_scaling
