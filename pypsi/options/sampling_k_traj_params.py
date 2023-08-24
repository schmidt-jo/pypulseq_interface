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

    def register_trajectory(self, trajectory: np.ndarray, id: str):
        if trajectory.shape.__len__() > 1:
            adc_samples = trajectory[:, 0]
            k_read_pos = trajectory[:, 1]
        else:
            adc_samples = np.arange(trajectory.shape[0])
            k_read_pos = trajectory
        acquisition = [id] * trajectory.shape[0]

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
        new_row = {
            "scan_num": scan_num, "slice_num": slice_num, "pe_num": pe_num, "acq_type": acq_type,
            "echo_num": echo_num, "echo_type": echo_type, "echo_type_num": echo_type_num,
            "nav_acq": nav_acq, "nav_dir": nav_dir
        }
        # add entry
        self.sampling_pattern.append(new_row, ignore_index=True)

