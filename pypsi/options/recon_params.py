import simple_parsing as sp
import dataclasses as dc
import logging

log_module = logging.getLogger(__name__)


@dc.dataclass
class ReconParameters(sp.helpers.Serializable):
    pass
