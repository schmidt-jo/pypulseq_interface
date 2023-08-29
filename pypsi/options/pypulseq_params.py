import simple_parsing as sp
import dataclasses as dc
import typing
import numpy as np
import logging

log_module = logging.getLogger(__name__)


@dc.dataclass
class PypulseqParameters(sp.helpers.Serializable):
    """
    Holding all Sequence Parameters
    """
    name: str = "jstmc"
    version: str = "xx"
    report: bool = sp.field(default=False, alias="-r")
    visualize: bool = sp.field(default=True, alias="-v")

    resolutionFovRead: float = 100  # [mm]
    resolutionFovPhase: float = 100.0  # [%]
    resolutionBase: int = 100
    resolutionSliceThickness: float = 1.0  # [mm]
    resolutionNumSlices: int = 10
    resolutionSliceGap: int = 20  # %

    numberOfCentralLines: int = 40
    accelerationFactor: float = 2.0

    excitationFA: float = 90.0
    excitationRfPhase: float = 90.0  # °
    excitationDuration: int = 2500  # [us]
    excitationTimeBwProd: float = 2.0
    excitationPreMoment: float = 1000.0  # Hz/m
    excitationRephaseFactor: float = 1.04  # Correction factor for insufficient rephasing

    refocusingFA: typing.List = dc.field(default_factory=lambda: [140.0])
    refocusingRfPhase: typing.List = dc.field(default_factory=lambda: [0.0])  # °
    refocusingDuration: int = 3000  # [us]
    refocusingTimeBwProd: float = 2.0
    refocusingScaleSliceGrad: float = 1.5  # adjust slice selective gradient sice of refocusing -
    # caution: this broadens the slice profile of the pulse, the further away from 180 fa
    # we possibly get saturation outside the slice
    readSpoilingFactor: float = 0.5
    sliceSpoilingMoment: float = 2500.0  # [Hz/m]
    sliceEndSpoilingMoment: float = 2500  # [Hz/m]
    interleavedAcquisition: bool = True
    # interfacing with rfpf
    extRfExc: str = ""
    extRfRef: str = ""

    ESP: float = 7.6  # [ms] echo spacing
    ETL: int = 8  # echo train length
    TR: float = 4500.0  # [ms]

    bandwidth: float = 250.0  # [Hz / px]
    oversampling: int = 2  # oversampling factor
    sampleWeighting: float = 0.0  # factor to weight random sampling towards central k-space ->
    # towards 1 we get densely sampled center

    phaseDir: str = "PA"

    def __post_init__(self):
        # resolution
        self.resolutionNRead = self.resolutionBase  # number of freq encodes
        self.resolutionNPhase = int(self.resolutionBase * self.resolutionFovPhase / 100)  # number of phase encodes
        self.resolutionVoxelSizeRead = self.resolutionFovRead / self.resolutionBase  # [mm]
        self.resolutionVoxelSizePhase = self.resolutionFovRead / self.resolutionBase  # [mm]
        self.deltaK_read = 1e3 / self.resolutionFovRead  # cast to m
        self.deltaK_phase = 1e3 / (self.resolutionFovRead * self.resolutionFovPhase / 100.0)  # cast to m
        self.TE = np.arange(1, self.ETL + 1) * self.ESP  # [ms] echo times
        # there is one gap less than number of slices,
        self.z_extend = self.resolutionSliceThickness * (
                self.resolutionNumSlices + self.resolutionSliceGap / 100.0 * (self.resolutionNumSlices - 1))  # in mm
        # acc
        self.numberOfOuterLines = round((self.resolutionNPhase - self.numberOfCentralLines) / self.accelerationFactor)
        # sequence
        self.acquisitionTime = 1 / self.bandwidth
        # dwell needs to be on adc raster time, acquisition time is flexible -> leads to small deviations in bandwidth
        # adc raster here hardcoded
        adc_raster = 1e-7
        s_dwell = self.acquisitionTime / self.resolutionNRead / self.oversampling  # oversampling
        adcr_dwell = int(1 / adc_raster * s_dwell)
        self.dwell = adc_raster * adcr_dwell
        if np.abs(s_dwell - self.dwell > 1e-9):
            log_module.info(f"setting dwell time on adc raster -> small bw adoptions (set bw: {self.bandwidth:.1f})")
        # update acquisition time and bandwidth
        self.acquisitionTime = self.dwell * self.resolutionNRead * self.oversampling
        self.bandwidth = 1 / self.acquisitionTime
        log_module.info(f"Bandwidth: {self.bandwidth:.1f} Hz/px;"
                        f"Readout time: {self.acquisitionTime * 1e3:.1f} ms;"
                        f"DwellTime: {self.dwell * 1e6:.1f} us;"
                        f"Number of Freq Encodes: {self.resolutionNRead}")
        # ref list
        if self.refocusingFA.__len__() != self.refocusingRfPhase.__len__():
            err = f"provide same amount of refocusing pulse angle ({self.refocusingFA.__len__()}) " \
                  f"and phases ({self.refocusingRfPhase.__len__()})"
            log_module.error(err)
            raise AttributeError(err)
        # check for phase values
        for l_idx in range(self.refocusingRfPhase.__len__()):
            while np.abs(self.refocusingRfPhase[l_idx]) > 180.0:
                self.refocusingRfPhase[l_idx] = self.refocusingRfPhase[l_idx] - \
                                                np.sign(self.refocusingRfPhase[l_idx]) * 180.0
            while np.abs(self.refocusingFA[l_idx]) > 180.0:
                self.refocusingFA[l_idx] = self.refocusingFA[l_idx] - np.sign(self.refocusingFA[l_idx]) * 180.0
        while self.refocusingFA.__len__() < self.ETL:
            # fill up list with last value
            self.refocusingFA.append(self.refocusingFA[-1])
            self.refocusingRfPhase.append(self.refocusingRfPhase[-1])
        # while self.sliceSpoilingMoment.__len__() < self.ETL:
        #     self.sliceSpoilingMoment.append(self.sliceSpoilingMoment[-1])

        # casting
        self.excitationRadFA = self.excitationFA / 180.0 * np.pi
        self.excitationRadRfPhase = self.excitationRfPhase / 180.0 * np.pi
        self.refocusingRadFA = np.array(self.refocusingFA) / 180.0 * np.pi
        self.refocusingRadRfPhase = np.array(self.refocusingRfPhase) / 180.0 * np.pi
        self.get_voxel_size()
        if self.phaseDir == "PA":
            self.read_dir = 'x'
            self.phase_dir = 'y'
        elif self.phaseDir == "RL":
            self.phase_dir = 'x'
            self.read_dir = 'y'
        else:
            err = 'Unknown Phase direction: chose either PA or RL'
            log_module.error(err)
            raise AttributeError(err)

        # error catches
        if np.any(np.array(self.sliceSpoilingMoment) < 1e-7):
            err = f"this implementation needs a spoiling moment supplied: provide spoiling Moment > 0"
            log_module.error(err)
            raise ValueError(err)

    def get_voxel_size(self):
        log_module.info(
            f"Voxel Size [read, phase, slice] in mm: "
            f"{[self.resolutionVoxelSizeRead, self.resolutionVoxelSizePhase, self.resolutionSliceThickness]}")
        return self.resolutionVoxelSizeRead, self.resolutionVoxelSizePhase, self.resolutionSliceThickness

    def get_fov(self):
        fov_read = 1e-3 * self.resolutionFovRead
        fov_phase = 1e-3 * self.resolutionFovRead * self.resolutionFovPhase / 100
        fov_slice = self.z_extend * 1e-3
        if self.read_dir == 'x':
            log_module.info(
                f"FOV (xyz) Size [read, phase, slice] in mm: "
                f"[{1e3 * fov_read:.1f}, {1e3 * fov_phase:.1f}, {1e3 * fov_slice:.1f}]")
            return fov_read, fov_phase, fov_slice
        else:
            log_module.info(
                f"FOV (xyz) Size [phase, read, slice] in mm: "
                f"[{1e3 * fov_phase:.1f}, {1e3 * fov_read:.1f}, {1e3 * fov_slice:.1f}]")
            return fov_phase, fov_read, fov_slice
