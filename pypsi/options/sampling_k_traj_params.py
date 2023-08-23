import numpy as np
import pandas as pd
import logging
import simple_parsing as sp
import dataclasses as dc

log_module = logging.getLogger(__name__)


@dc.dataclass
class SamplingKTrajectoryParameters(sp.Serializable):
    lookup_df: pd.DataFrame = pd.DataFrame(columns=["acquisition", "adc_sampling_num", "k_traj_position"])

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
        self.lookup_df = pd.concat((self.lookup_df, df), ignore_index=True).reset_index()
