from abc import abstractmethod, ABC
from collections import defaultdict
from typing import overload, Self, override, Any

from utils import Writable, Writer, SFZFile


class SFZElement(Writable, ABC):
    @abstractmethod
    def hgroup(self) -> SFZGroup: ...
    @abstractmethod
    def hregion(self) -> SFZRegion: ...


class SFZ(SFZElement):
    def __init__(self):
        self.headers: list[SFZElement] = []

    @override
    def get_writer(self):
        return SFZWriter(self)

    @override
    def hgroup(self):
        header = SFZGroup(self)
        self.headers.append(header)
        return header

    @override
    def hregion(self):
        header = SFZRegion(self)
        self.headers.append(header)
        return header


class SFZBodyHeader(SFZElement, ABC):
    def __init__(self):
        self.ops = dict()

    def sample(self, sample: str):
        self.ops['sample'] = sample
        return self

    def pitch_keycenter(self, center: int | None):
        self.ops['pitch_keycenter'] = center
        return self

    def hikey(self, val: int):
        self.ops['hikey'] = val
        return self

    def lokey(self, val: int):
        self.ops['lokey'] = val
        return self

    @overload
    def key(self, lo: int, hi: int, center: int) -> Self: ...
    @overload
    def key(self, lo: int, hi: int) -> Self: ...
    @overload
    def key(self, val: int) -> Self: ...

    def key(self, lo: int, hi: int | None = None, center: int | None = None):
        if hi is None:
            self.ops['key'] = lo
        else:
            self.lokey(lo).hikey(hi)

        if center is not None:
            return self.pitch_keycenter(center)
        return self

    def hivel(self, val: int):
        self.ops['hivel'] = val
        return self

    def lovel(self, val: int):
        self.ops['lovel'] = val
        return self

    def vel(self, lo: int, hi: int):
        return self.lovel(lo).hivel(hi)


class SFZGroup(SFZBodyHeader):
    def __init__(self, sfz: SFZ):
        super().__init__()
        self._sfz = sfz
        self.regions: list[SFZRegion] = []

    @override
    def hgroup(self):
        return self._sfz.hgroup()

    @override
    def hregion(self):
        region = SFZRegion(self)
        self.regions.append(region)
        return region

    @override
    def get_writer(self) -> Writer:
        return SFZGroupWriter(self)


class SFZRegion(SFZBodyHeader):
    def __init__(self, outer: SFZ | SFZGroup):
        super().__init__()
        self.outer = outer

    @override
    def hgroup(self):
        return self.outer.hgroup()

    @override
    def hregion(self):
        return self.outer.hregion()

    @override
    def get_writer(self) -> Writer:
        return SFZRegionWriter(self)


class SFZWriter(Writer):
    def __init__(self, sfz: SFZ):
        self._sfz = sfz

    @override
    def write(self, file: SFZFile, cfg: dict[str, Any] | None = None):
        for header in self._sfz.headers:
            header.get_writer().write(file, cfg)


class SFZGroupWriter(Writer):
    def __init__(self, group: SFZGroup):
        self.group = group

    @override
    def write(self, file: SFZFile, cfg: dict[str, Any] | None = None):
        if cfg is None:
            cfg = defaultdict(None)

        prefix = cfg['prefix'] if cfg['prefix'] is not None else ''
        key_style = cfg['key_style'] if cfg['key_style'] is not None else 'line'
        params = [f'{op}={v}' for op, v in self.group.ops.items()]
        key_sep = '\n' + prefix if key_style == 'column' else ' '
        keys_prefix = '\n' + prefix if key_style == 'column' else ''

        file.write('<group>' + keys_prefix + key_sep.join(params) + '\n')

        for region in self.group.regions:
            region.get_writer().write(file, cfg)


class SFZRegionWriter(Writer):
    def __init__(self, region: SFZRegion):
        self.region = region

    @override
    def write(self, file: SFZFile, cfg: dict[str, Any] | None = None):
        if cfg is None:
            cfg = defaultdict(None)

        key_style = cfg['key_style'] if cfg['key_style'] is not None else 'line'
        prefix = cfg['prefix'] if cfg['prefix'] is not None else ''
        params = [f'{op}={v}' for op, v in self.region.ops.items()]
        key_sep = '\n' + prefix * 2 if key_style == 'column' else ' '
        keys_prefix = '\n' + prefix * 2 if key_style == 'column' else ' '

        file.write(prefix + '<region>' + keys_prefix + key_sep.join(params) + '\n')
