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
import pathlib as plib
import simple_parsing as sp
import dataclasses as dc
import options as opts
log_module = logging.getLogger(__name__)


@dc.dataclass
class Config(sp.Serializable):
    config_file: str = sp.field(default="", alias=["-c"])
    output_path: str = sp.field(default="./test/", alias=["-o"])
    visualize: bool = sp.field(default=True, alias=["-v"])


@ dc.dataclass
class XConfig(sp.Serializable):
    # loading extra files
    pypulseq_config_file: str = sp.field(default=None, alias="-ppf")
    pulse_file: str = sp.field(default=None, alias="-pf")
    sampling_k_traj_file: str = sp.field(default=None, alias="-skf")
    emc_info_file: str = sp.field(default=None, alias="-emcf")
    raw_data_details_file: str = sp.field(default=None, alias="-rddf")
    scanner_specs_file: str = sp.field(default=None, alias="-ssf")


@dc.dataclass
class Params(sp.Serializable):
    config: Config = Config(),
    emc: opts.EmcParameters = opts.EmcParameters(),
    pypulseq: opts.PypulseqParameters = opts.PypulseqParameters(),
    pulse: opts.RFParameters = opts.RFParameters(),
    sampling_k_traj: opts.SamplingKTrajectoryParameters = opts.SamplingKTrajectoryParameters(),
    recon: opts.ReconParameters = opts.ReconParameters(),
    specs: opts.ScannerParameters = opts.ScannerParameters()

    @staticmethod
    def _get_d_to_set():
        return {
            "pypulseq_config_file": "pypulseq",
            "pulse_file": "pulse",
            "sampling_k_traj_file": "sampling_k_traj",
            "emc_info_file": "emc",
            "raw_data_details_file": "recon",
            "scanner_specs_file": "specs",
        }

    @classmethod
    def from_cli(cls, args: sp.ArgumentParser.parse_args):
        # create instance, fill config arguments
        instance = cls(config=args.config)
        # check if config file exists and laod
        c_file = plib.Path(args.config.config_file).absolute()
        if c_file.is_file():
            log_module.info(f"loading config file: {c_file.as_posix()}")
            instance = cls.load(c_file)
        # check for extra file input
        instance._load_extra_argfile(extra_files=args.extra_files)
        return instance

    def _load_extra_argfile(self, extra_files: XConfig):
        # check through all arguments
        for mem, f_name in extra_files.__dict__.items():
            # check if provided
            if f_name is not None:
                # get member name of Config class and set file name value
                # convert to plib Path
                path = plib.Path(f_name)
                if path.is_file():
                    log_module.info(f"load file: {path.as_posix()}")
                    # get corresponding member
                    mem_name = self._get_d_to_set().get(mem)
                    if mem_name is not None:
                        mem = extra_files.__getattribute__(mem_name)
                        mem.load(path)
                        self.__setattr__(mem_name, mem)
                elif not path.is_file():
                    err = f"{path} is not a file. exiting..."
                    log_module.error(err)
                    raise FileNotFoundError(err)


def create_cli() -> (sp.ArgumentParser, sp.ArgumentParser.parse_args):
    parser = sp.ArgumentParser(prog="pypsi")
    parser.add_arguments(Config, dest="config")
    parser.add_arguments(XConfig, dest="extra_files")
    args = parser.parse_args()
    return parser, args


if __name__ == '__main__':
    parser, args = create_cli()

    params = Params.from_cli(args=args)
    params.save("pypsi/options/defaults/pypsi.pkl")

    params = Params.load("pypsi/options/defaults/pypsi.pkl")
    log_module.info("success")
