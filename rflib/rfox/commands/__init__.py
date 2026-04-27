"""Subcommand registry."""
from . import (
    devices,
    profile,
    preset,
    scan,
    sweep,
    logger,
    transmit,
    tx_hex,
    jam,
    scanjam,
    replay,
    rolljam,
    decode,
    find_sync,
    find_repeats,
    crc,
    diff,
    decode_wav,
    specan,
    brute,
    fuzz,
)


# (name, module) — order is the menu order
ALL = [
    ("devices", devices),
    ("scan", scan),
    ("sweep", sweep),
    ("logger", logger),
    ("transmit", transmit),
    ("tx-hex", tx_hex),
    ("jam", jam),
    ("scanjam", scanjam),
    ("replay", replay),
    ("rolljam", rolljam),
    ("brute", brute),
    ("fuzz", fuzz),
    ("decode", decode),
    ("find-sync", find_sync),
    ("find-repeats", find_repeats),
    ("crc", crc),
    ("diff", diff),
    ("decode-wav", decode_wav),
    ("specan", specan),
    ("profile", profile),
    ("preset", preset),
]


def get(name):
    for n, mod in ALL:
        if n == name:
            return mod
    raise KeyError(f"unknown command {name!r}")
