"""Pcap capture file format for rfox.

We use DLT_USER0 (147), reserved by libpcap for private link types.
Each "packet" payload starts with a fixed RFCT pseudo-header that records
the radio config used at capture time, followed by the raw on-air bytes.

Per-packet pseudo-header (little-endian, 24 bytes):
    magic       4s  b"RFCT"
    version     B   1
    modulation  B   index into config.MOD_NAMES
    freq_hz     I   tuning frequency
    drate_bps   I   modem data rate
    chanbw_hz   I   channel bandwidth
    rssi_dbm10  h   RSSI * 10 (signed, so -42.5 dBm = -425)
    sync_word   H   16-bit sync word, 0 if none

Wireshark won't dissect this without a custom Lua plugin, but the raw
.pcap is still a valid file and any pcap reader (scapy, pyshark, raw)
can pull the packets out.
"""
from __future__ import annotations
import os
import struct
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from .config import RFConfig, MOD_NAMES


PCAP_MAGIC_USEC = 0xa1b2c3d4
PCAP_VERSION = (2, 4)
DLT_USER0 = 147
SNAPLEN = 65535

GLOBAL_HDR = struct.Struct("<IHHiIII")    # 24 bytes
PKT_HDR = struct.Struct("<IIII")           # 16 bytes
PSEUDO_HDR = struct.Struct("<4sBBIIIhH")   # 24 bytes
PSEUDO_MAGIC = b"RFCT"
PSEUDO_VERSION = 1


@dataclass
class CapturedFrame:
    ts: float
    cfg: RFConfig
    rssi: float
    payload: bytes


def _mod_to_idx(name: str) -> int:
    try:
        return MOD_NAMES.index(name)
    except ValueError:
        return 0


def _mod_from_idx(idx: int) -> str:
    if 0 <= idx < len(MOD_NAMES):
        return MOD_NAMES[idx]
    return MOD_NAMES[0]


class PcapWriter:
    """Append-only pcap writer. Use as a context manager."""

    def __init__(self, path: str):
        self.path = path
        self._fp = None

    def __enter__(self):
        new = not os.path.exists(self.path) or os.path.getsize(self.path) == 0
        self._fp = open(self.path, "ab")
        if new:
            self._fp.write(GLOBAL_HDR.pack(
                PCAP_MAGIC_USEC, PCAP_VERSION[0], PCAP_VERSION[1],
                0, 0, SNAPLEN, DLT_USER0,
            ))
            self._fp.flush()
        return self

    def __exit__(self, *exc):
        if self._fp:
            self._fp.close()
            self._fp = None

    def write(self, frame: CapturedFrame):
        cfg = frame.cfg
        pseudo = PSEUDO_HDR.pack(
            PSEUDO_MAGIC, PSEUDO_VERSION,
            _mod_to_idx(cfg.modulation),
            int(cfg.freq), int(cfg.drate), int(cfg.chanbw),
            int(round(frame.rssi * 10)), cfg.sync_word & 0xffff,
        )
        payload = pseudo + frame.payload
        ts_sec = int(frame.ts)
        ts_usec = int((frame.ts - ts_sec) * 1_000_000)
        self._fp.write(PKT_HDR.pack(ts_sec, ts_usec, len(payload), len(payload)))
        self._fp.write(payload)
        self._fp.flush()


def read(path: str) -> Iterator[CapturedFrame]:
    """Iterate frames from a pcap file written by PcapWriter."""
    with open(path, "rb") as fp:
        ghdr = fp.read(GLOBAL_HDR.size)
        if len(ghdr) != GLOBAL_HDR.size:
            raise ValueError(f"{path}: truncated pcap global header")
        magic, vmaj, vmin, _tz, _sf, _snap, dlt = GLOBAL_HDR.unpack(ghdr)
        if magic != PCAP_MAGIC_USEC:
            raise ValueError(f"{path}: not a usec-pcap (magic={magic:#x})")
        if dlt != DLT_USER0:
            # not fatal - still read it, but warn
            pass

        while True:
            phdr = fp.read(PKT_HDR.size)
            if not phdr:
                return
            if len(phdr) != PKT_HDR.size:
                raise ValueError(f"{path}: truncated packet header")
            ts_sec, ts_usec, incl_len, _orig_len = PKT_HDR.unpack(phdr)
            data = fp.read(incl_len)
            if len(data) != incl_len:
                raise ValueError(f"{path}: truncated packet body")
            if len(data) < PSEUDO_HDR.size:
                continue
            magic, ver, mod_idx, freq, drate, chanbw, rssi10, syncw = \
                PSEUDO_HDR.unpack(data[:PSEUDO_HDR.size])
            if magic != PSEUDO_MAGIC:
                # foreign frame - skip
                continue
            payload = data[PSEUDO_HDR.size:]
            cfg = RFConfig(
                freq=float(freq),
                drate=float(drate),
                modulation=_mod_from_idx(mod_idx),
                chanbw=float(chanbw),
                sync_word=syncw,
            )
            yield CapturedFrame(
                ts=ts_sec + ts_usec / 1e6,
                cfg=cfg,
                rssi=rssi10 / 10.0,
                payload=payload,
            )


def write_one(path: str, frame: CapturedFrame):
    """Convenience helper for writing a single frame."""
    with PcapWriter(path) as w:
        w.write(frame)
