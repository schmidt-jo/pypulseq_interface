import pandas as pd
import logging
import simple_parsing as sp
import dataclasses as dc

log_module = logging.getLogger(__name__)


@dc.dataclass
class SamplingKTrajectoryParameters(sp.Serializable):
    pass
