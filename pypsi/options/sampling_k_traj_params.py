import json
import typing

import numpy as np
import pandas as pd
import logging
import pathlib as plib
import dataclasses as dc

log_module = logging.getLogger(__name__)


@dc.dataclass
class SamplingKTrajectoryParameters:
    k_trajectories: pd.DataFrame = pd.DataFrame(
        columns=["acquisition", "adc_sampling_num", "k_traj_position"]
    )
    sampling_pattern: pd.DataFrame = pd.DataFrame(
        columns=["scan_num", "slice_num", "pe_num", "acq_type",
                 "echo_num", "echo_type", "echo_type_num",
                 "nav_acq", "nav_dir"]
    )

    def save_json(self, f_name: typing.Union[str, plib.Path], indent: int):
        self.save(f_name=f_name, indent=indent)

    def save(self, f_name: typing.Union[str, plib.Path], indent: int):
        # ensure path
        f_name = plib.Path(f_name).absolute()
        # check if exists or make
        if not f_name.suffixes:
            f_name = f_name.with_name("sampling_k_traj_file").with_suffix(".json")
            log_module.info(f"no suffix detected: changing filename to {f_name}")
        if ".json" not in f_name.suffixes:
            f_name = f_name.with_suffix(".json")
            log_module.info(f"ensuring to save as .json, changing suffix")
        f_name.parent.mkdir(parents=True, exist_ok=True)
        # transform dfs to dicts
        sampling_pattern = self.sampling_pattern.to_dict()
        k_traj = self.k_trajectories.to_dict()
        # save dict
        save_dict = {
            "sampling_pattern": sampling_pattern,
            "k_trajectories": k_traj
        }
        with open(f_name, "w") as j_file:
            json.dump(save_dict, j_file, indent=indent)

    @classmethod
    def load(cls, f_name: typing.Union[str, plib.Path]):
        # ensure path
        f_name = plib.Path(f_name).absolute()
        if not f_name.is_file():
            err = f"no valid file found ({f_name.as_posix()})"
            raise FileNotFoundError(err)
        if ".json" not in f_name.suffixes:
            err = f"file ({f_name.as_posix()}) not given as .json"
            log_module.error(err)
            raise AttributeError(err)
        # load dict
        with open(f_name, "r") as j_file:
            ld = json.load(j_file)

        # convert from dict
        inst = cls()
        inst.sampling_pattern = pd.DataFrame.from_dict(ld["sampling_pattern"])
        inst.k_trajectories = pd.DataFrame.from_dict(ld["k_trajectories"])
        return inst

    def register_trajectory(self, trajectory: np.ndarray, identifier: str):
        if trajectory.shape.__len__() > 1:
            adc_samples = trajectory[:, 0]
            k_read_pos = trajectory[:, 1]
        else:
            adc_samples = np.arange(trajectory.shape[0])
            k_read_pos = trajectory
        acquisition = [identifier] * trajectory.shape[0]

        df = pd.DataFrame({
            "acquisition": acquisition, "adc_sampling_num": adc_samples, "k_traj_position": k_read_pos
        })
        self.k_trajectories = pd.concat((self.k_trajectories, df)).reset_index(drop=True)

    def write_sampling_pattern_entry(
            self, scan_num: int, slice_num: int, pe_num, echo_num: int,
            acq_type: str = "", echo_type: str = "", echo_type_num: int = -1,
            nav_acq: bool = False, nav_dir: int = 0):
        # check if entry exists already
        if scan_num in self.sampling_pattern["scan_num"]:
            err = f"scan number to register in sampling pattern ({scan_num}) exists already!"
            log_module.error(err)
            raise ValueError(err)
        # build entry
        new_row = pd.Series({
            "scan_num": scan_num, "slice_num": slice_num, "pe_num": pe_num, "acq_type": acq_type,
            "echo_num": echo_num, "echo_type": echo_type, "echo_type_num": echo_type_num,
            "nav_acq": nav_acq, "nav_dir": nav_dir
        })
        # add entry
        self.sampling_pattern = pd.concat((self.sampling_pattern, new_row.to_frame().T))

    def sampling_pattern_from_list(self, sp_list: list):
        self.sampling_pattern = pd.DataFrame(sp_list).set_index("scan_num")

    # def build_save_k_traj(self, k_trajs: list, labels: list, n_samples_ref: int) -> pd.DataFrame:
    #     # sanity check
    #     if len(k_trajs) != len(labels):
    #         err = "provide same number of labels as trajectories"
    #         log_module.error(err)
    #         raise AttributeError(err)
    #     # build k_traj df
    #     # add fully sampled reference
    #     k_labels = ["fs_ref"] * n_samples_ref
    #     traj_data: list = np.linspace(-0.5, 0.5, n_samples_ref).tolist()
    #     traj_pts: list = np.arange(n_samples_ref).tolist()
    #     for traj_idx in range(len(k_trajs)):
    #         k_labels.extend([labels[traj_idx]] * k_trajs[traj_idx].shape[0])
    #         traj_data.extend(k_trajs[traj_idx].tolist())
    #         traj_pts.extend(np.arange(k_trajs[traj_idx].shape[0]).tolist())
    #
    #     k_traj_df = pd.DataFrame({
    #         "acquisition": k_labels, "k_read_position": traj_data, "adc_sampling_num": traj_pts
    #     })
    #     # self.write_k_traj(k_traj_df)
    #     return k_traj_df
