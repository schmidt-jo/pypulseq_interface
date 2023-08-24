import typing

import numpy as np
import simple_parsing as sp
import dataclasses as dc
import logging

log_module = logging.getLogger(__name__)


@dc.dataclass
class ImageAcqParameters(sp.Serializable):
    # define all recon parameters we ship in interface
    n_read: int = NotImplemented
    n_phase: int = NotImplemented
    n_slice: int = NotImplemented

    resolution_read: float = NotImplemented
    resolution_phase: float = NotImplemented
    resolution_slice: float = NotImplemented

    read_dir: str = NotImplemented
    os_factor: int = NotImplemented
    acc_read: bool = NotImplemented
    acc_factor_phase: float = NotImplemented

    etl: int = NotImplemented
    te: list = NotImplemented


@dc.dataclass
class NavigatorAcqParameters(ImageAcqParameters):
    lines_per_nav: int = NotImplemented
    num_of_nav: int = NotImplemented
    nav_acc_factor: int = NotImplemented
    nav_resolution_scaling: float = NotImplemented


@dc.dataclass
class ReconParameters(sp.Serializable):
    multi_echo_img: ImageAcqParameters = ImageAcqParameters()
    navigator_img: NavigatorAcqParameters = NotImplemented

    def set_recon_params(
            self, img_n_read: int, img_n_phase: int, img_n_slice: int, img_resolution_read: float,
            img_resolution_phase: float, img_resolution_slice: float, read_dir: str, os_factor: int,
            acc_read: bool, acc_factor_phase: int, etl: int, te: typing.Union[list, np.ndarray]
    ):
        if isinstance(te, np.ndarray):
            te = te.tolist()
        self.multi_echo_img = ImageAcqParameters(
            n_read=img_n_read, n_phase=img_n_phase, n_slice=img_n_slice,
            resolution_read=img_resolution_read, resolution_phase=img_resolution_phase,
            resolution_slice=img_resolution_slice, read_dir=read_dir,
            acc_read=acc_read, acc_factor_phase=acc_factor_phase,
            etl=etl, te=te, os_factor=os_factor
        )

    def set_navigator_params(
            self, lines_per_nav: int, num_of_nav: int, nav_acc_factor: int, nav_resolution_scaling: float
    ):
        nav_n_read = int(self.multi_echo_img.n_read * nav_resolution_scaling)
        nav_n_phase = int(self.multi_echo_img.n_phase * nav_resolution_scaling)
        nav_n_slice = int(self.multi_echo_img.n_slice * nav_resolution_scaling)
        nav_res_read = self.multi_echo_img.n_read / nav_resolution_scaling
        nav_res_phase = self.multi_echo_img.n_phase / nav_resolution_scaling
        nav_res_slice = self.multi_echo_img.n_slice / nav_resolution_scaling
        read_dir = self.multi_echo_img.read_dir
        acc_read = False
        acc_factor_phase = nav_acc_factor
        self.navigator_img = NavigatorAcqParameters(
            n_read=nav_n_read, n_phase=nav_n_phase, n_slice=nav_n_slice,
            resolution_read=nav_res_read, resolution_phase=nav_res_phase,
            resolution_slice=nav_res_slice, read_dir=read_dir,
            acc_read=acc_read, acc_factor_phase=acc_factor_phase,
            lines_per_nav=lines_per_nav, num_of_nav=num_of_nav, nav_acc_factor=nav_acc_factor,
            nav_resolution_scaling=nav_resolution_scaling
        )

