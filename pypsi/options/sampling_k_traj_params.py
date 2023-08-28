import numpy as np
import pandas as pd
import logging
import simple_parsing as sp
import dataclasses as dc

log_module = logging.getLogger(__name__)


@dc.dataclass
class SamplingKTrajectoryParameters(sp.Serializable):
    k_trajectories: pd.DataFrame = pd.DataFrame(
        columns=["acquisition", "adc_sampling_num", "k_traj_position"]
    )
    sampling_pattern: pd.DataFrame = pd.DataFrame(
        columns=["scan_num", "slice_num", "pe_num", "acq_type",
                 "echo_num", "echo_type", "echo_type_num",
                 "nav_acq", "nav_dir"]
    )

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
        self.k_trajectories = pd.concat((self.k_trajectories, df), ignore_index=True).reset_index()

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
