"""
We want a class structure that provides all of the necessary information for:
- info of scanner specs
- details used for sequence creation
- details needed for raw data processing
- details needed for sequence simulation via EMC
- info needed to calculate and / or store k-space trajectories -> gridding via kbnufft
- saving and loading sampling patterns
- interfacing pulse files - store and plot pulses used or feed in pulse shapes
"""

import logging
import typing
import pathlib as plib
import simple_parsing as sp
import dataclasses as dc
import options as opts
log_module = logging.getLogger(__name__)


@dc.dataclass
class Config(sp.Serializable):
    config_file: str = sp.field(default="", alias=["-c"])
    pypulseq_config_file: str = sp.field(default="", alias="-ppf")
    pulse_file: str = sp.field(default="", alias="-pf")
    sampling_k_traj_file: str = sp.field(default="", alias="-skf")
    emc_info_file: str = sp.field(default="", alias="-emcf")
    raw_data_details_file: str = sp.field(default="", alias="-rddf")
    scanner_specs_file: str = sp.field(default="", alias="-ssf")
    output_path: str = sp.field(default="./test/", alias=["-o"])
    visualize: bool = sp.field(default=True, alias=["-v"])


class Params:
    def __init__(
            self,
            config: Config = Config(),
            emc: opts.EmcParameters = opts.EmcParameters(),
            pypulseq: opts.PypulseqParameters = opts.PypulseqParameters(),
            pulse: opts.RFParameters = opts.RFParameters(),
            sampling_k_traj: opts.SamplingKTrajectoryParameters = opts.SamplingKTrajectoryParameters(),
            recon: opts.ReconParameters = opts.ReconParameters(),
            specs: opts.ScannerParameters = opts.ScannerParameters()
    ):
        self.config: Config = config
        self.emc: opts.EmcParameters = emc
        self.pypulseq: opts.PypulseqParameters = pypulseq
        self.pulse: opts.RFParameters = pulse
        self.sampling_k_traj: opts.SamplingKTrajectoryParameters = sampling_k_traj
        self.recon: opts.ReconParameters = recon
        self.specs: opts.ScannerParameters = specs

        self._d_to_set = {
            "config_file": "config",
            "pypulseq_config_file": "pypulseq",
            "pulse_file": "pulse",
            "sampling_k_traj_file": "sampling_k_traj",
            "emc_info_file": "emc",
            "raw_data_details_file": "recon",
            "scanner_specs_file": "specs",
        }

    @classmethod
    def load(cls, path: typing.Union[str, plib.Path]):
        # convert to plib Path ifn
        path = plib.Path(path).absolute()
        # load all filenames into config obj
        if not path.is_file():
            err = f"{path} is not a file. exiting..."
            log_module.error(err)
            raise FileNotFoundError(err)
        instance = cls(config=Config.load(path))

        # load individual parts
        for mem, f_name in instance.config.__dict__.items():
            if mem != "visualize":
                # get member name of Config class and set file name value
                # convert to plib Path
                path = plib.Path(f_name)
                if path.is_file():
                    log_module.info(f"load file: {path.as_posix()}")
                    # get corresponding member
                    mem_name = instance._d_to_set.get(mem)
                    if mem_name is not None:
                        mem = instance.__getattribute__(mem_name)
                        mem.load(path)
                        instance.__setattr__(mem_name, mem)
                elif not path.is_file() and mem != "output_path":
                    err = f"{path} is not a file. exiting..."
                    log_module.error(err)
                    raise FileNotFoundError(err)
        return instance

    def save(self, path: typing.Union[str, plib.Path]):
        path = plib.Path(path).absolute()
        # check if dir or filename given
        if path.suffixes:
            # in case of filename use parent dir
            path = path.parent
        # check dir exist or make
        path.mkdir(parents=True, exist_ok=True)
        # set as config output path
        self.config.output_path = plib.Path(path)
        # save all files relative to that path
        for key, val in self._d_to_set.items():
            if val == "pulse":
                f_name = path.joinpath(val).with_suffix(".pkl")
                self.__getattribute__(val).save(f_name)
            else:
                f_name = path.joinpath(val).with_suffix(".json")
                self.__getattribute__(val).save_json(f_name, indent=2)
            log_module.info(f"writing file: {f_name.as_posix()}")
            self.config.__setattr__(key, f_name.as_posix())
        # save config again after all fields filled
        f_name = path.joinpath("config.json")
        self.config.config_file = f_name.as_posix()
        self.config.save_json(f_name, indent=2)


def create_cli() -> (sp.ArgumentParser, sp.ArgumentParser.parse_args):
    parser = sp.ArgumentParser(prog="pypsi")
    parser.add_arguments(Config, dest="config")
    args = parser.parse_args()
    return parser, args


if __name__ == '__main__':
    params = Params()
    params.save("pypsi/options/defaults")

    params = Params.load("pypsi/options/defaults/config.json")
    log_module.info("success")
