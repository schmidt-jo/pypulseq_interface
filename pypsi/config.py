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
import json
import pickle as pkl
import logging
import pathlib as plib
import typing

import simple_parsing as sp
import dataclasses as dc
from pypsi import parameters as iparams

log_module = logging.getLogger(__name__)


@dc.dataclass
class Config(sp.Serializable):
    config_file: str = sp.field(default="", alias=["-c"])
    output_path: str = sp.field(default="./test/", alias=["-o"])
    visualize: bool = sp.field(default=True, alias=["-v"])


@dc.dataclass
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
    config: Config = Config()
    emc: iparams.EmcParameters = iparams.EmcParameters()
    pypulseq: iparams.PypulseqParameters = iparams.PypulseqParameters()
    pulse: iparams.RFParameters = iparams.RFParameters()
    sampling_k_traj: iparams.SamplingKTrajectoryParameters = iparams.SamplingKTrajectoryParameters()
    recon: iparams.ReconParameters = iparams.ReconParameters()
    specs: iparams.ScannerParameters = iparams.ScannerParameters()

    def __post_init__(self):
        self._d_to_set: dict = {
            "pypulseq_config_file": "pypulseq",
            "pulse_file": "pulse",
            "sampling_k_traj_file": "sampling_k_traj",
            "emc_info_file": "emc",
            "raw_data_details_file": "recon",
            "scanner_specs_file": "specs",
        }

    # @classmethod
    # def load(cls, f_name: typing.Union[str, plib.Path]):
    #     # ensure path
    #     f_name = plib.Path(f_name).absolute()
    #     # check if exists
    #     if f_name.is_file():
    #         if ".json" in f_name.suffixes:
    #             with open(f_name, "r") as j_file:
    #                 # returns json contents as dict
    #                 contents = json.load(j_file)
    #                 inst = cls()
    #                 for key, val in contents.items():
    #                     inst.__setattr__(key, val)
    #         if ".pkl" in f_name.suffixes:
    #             with open(f_name, "rb") as p_file:
    #                 inst = pkl.load(p_file)
    #         else:
    #             err = f"no valid suffix ({f_name.suffixes}), input needs to be .pkl or .json"
    #             log_module.error(err)
    #             raise AttributeError(err)
    #     else:
    #         err = f"no valid file: {f_name.as_posix()}"
    #         log_module.error(err)
    #         raise FileNotFoundError(err)
    #     return inst
    #
    # def save(self, f_name: typing.Union[str, plib.Path]):
    #     # ensure path
    #     f_name = plib.Path(f_name).absolute()
    #     # check if exists or make
    #     if not f_name.suffixes:
    #         err = f"no valid filename: {f_name.as_posix()}"
    #         log_module.error(err)
    #         raise AttributeError(err)
    #     f_name.parent.mkdir(parents=True, exist_ok=True)
    #     # save
    #     if ".pkl" not in f_name.suffixes:
    #         log_module.info(f"changing suffix to .pkl")
    #         f_name = f_name.with_suffix(".pkl")
    #     log_module.info(f"writing file: {f_name.as_posix()}")
    #     with open(f_name, "wb") as p_file:
    #         pkl.dump(self, p_file)

    def save_as_subclasses(self, path: typing.Union[str, plib.Path]):
        # ensure path
        path = plib.Path(path).absolute()
        # check if exists or make
        if path.suffixes:
            path = path.parent
        path.mkdir(parents=True, exist_ok=True)
        # save
        for f_name, att_name in self._d_to_set.items():
            suffix = ".json"
            if att_name == "pulse":
                suffix = ".pkl"
            save_file = path.joinpath(f_name).with_suffix(suffix)
            log_module.info(f"write file: {save_file.as_posix()}")
            subclass = self.__getattribute__(att_name)
            if suffix == ".pkl":
                subclass.save(save_file)
            else:
                subclass.save_json(save_file, indent=2)

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

    def visualize(self):
        self.sampling_k_traj.plot_sampling_pattern(output_path=self.config.output_path)
        self.sampling_k_traj.plot_k_space_trajectories(output_path=self.config.output_path)
        self.pulse.plot(output_path=self.config.output_path)

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
                    mem_name = self._d_to_set.get(mem)
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
    s_file = plib.Path("./default_config/pypsi.pkl").absolute()
    s_file.parent.mkdir(parents=True, exist_ok=True)
    params.save(s_file.as_posix())

    params.save_as_subclasses(s_file.parent.as_posix())

    params = Params.load(s_file.as_posix())
    log_module.info("success")
