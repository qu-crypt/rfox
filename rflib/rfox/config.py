"""Shared radio configuration used by every rfox subcommand."""
from dataclasses import dataclass, field, asdict
from typing import Optional


MOD_NAMES = ("OOK", "2FSK", "GFSK", "MSK", "4FSK")
SYNC_MODES = ("NONE", "15/16", "16/16", "CS", "CS15/16", "CS16/16", "CS30/32")


@dataclass
class RFConfig:
    """Parameters every command needs to talk to a dongle."""
    freq: float = 433.92e6          # Hz
    drate: float = 4800.0           # bps
    modulation: str = "OOK"         # one of MOD_NAMES
    sync_mode: str = "NONE"         # one of SYNC_MODES
    sync_word: int = 0              # 16-bit
    chanbw: float = 60_000.0        # Hz
    deviation: float = 20_000.0     # Hz, only used for FSK family
    channel: int = 0
    pktlen: int = 250
    power: int = 0xc0               # 0..0xff
    preamble: int = 4               # bytes
    fixed_len: bool = True          # True=Fixed, False=Variable

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        # tolerate extra keys
        valid = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def summary(self):
        return (
            f"{self.freq/1e6:.4f} MHz @ {self.drate:.0f} bps  "
            f"mod={self.modulation} bw={self.chanbw/1e3:.1f} kHz  "
            f"sync={self.sync_mode}/{self.sync_word:#06x} pktlen={self.pktlen}"
        )
