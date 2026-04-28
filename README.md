# rfox

> Unified [rfcat-py3](https://github.com/qu-crypt/rfcat) helper for sub-GHz RF
> capture and analysis. One CLI, one interactive menu, one capture format. Built
> on top of rfcat / rflib so it works with any YARDStickOne, RfCat-compatible
> CC1111 dongle, or DonsDongle.

```bash
./rfox                                      # interactive menu
./rfox decode --hex aabbccdd -m manchester  # direct CLI
```

---

## Why rfox

rfcat ships a powerful Python library (`rflib`) and an interactive shell,
but day-to-day RF work tends to be the same handful of recipes — capture a
signal, sweep a band, decode some Manchester, identify a CRC, find a sync
word — repeated with slightly different parameters. The community
[RfCatHelpers](https://github.com/AndrewMohawk/RfCatHelpers) project showed
how useful those recipes are as standalone scripts, but each one
re-implements the same dongle init, defines its own incompatible CLI, and
uses its own ad-hoc capture format.

rfox consolidates that workflow into:

- **one tool** with consistent flags everywhere (`-f` is always Hz,
  `-r` is always bps, `-m` is always one of `OOK / 2FSK / GFSK / MSK / 4FSK`);
- **an interactive menu** for when you don't remember the flags — it walks
  you through every option with the default shown;
- **one capture file format** (libpcap, DLT_USER0, RFCT pseudo-header) so
  anything you capture in one mode can be replayed, decoded, diffed, or
  CRC-checked by any other command;
- **named profiles** (`~/.rfcat/profiles.json`) and **built-in presets**
  for common protocols, so you stop re-typing six flags for every command.

The interactive menu and the CLI share a single dispatcher, so they can
never drift apart — adding a new command exposes it in both modes
automatically.

---

## Installation

rfox is a standalone tool that depends on [rfcat-py3](https://github.com/qu-crypt/rfcat) for the underlying `rflib` library.

```bash
pip install rfox
```

Optional dependencies:

```bash
pip install 'rfox[specan]'      # enables `rfox specan` (PySide6)
```

For development:

```bash
git clone https://github.com/qu-crypt/rfox.git
cd rfox
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

System libraries:

- **libusb-1.0** (Linux: `apt install libusb-1.0-0`, macOS: `brew install
libusb`, Windows: see the rfcat README)
- non-root USB access on Linux requires the udev rules from the [rfcat-py3](https://github.com/qu-crypt/rfcat) repo's `etc/udev/`

Verify:

```bash
./rfox --help
./rfox devices         # lists attached dongles
```

---

## Quick start

Five things you'll almost certainly want to do:

```bash
# 1. Sweep a band looking for activity
./rfox sweep --start 433e6 --stop 434e6 --step 50e3 --ascii-bar

# 2. Capture five presses of a 433 MHz remote into a pcap
./rfox replay capture --preset ev1527 -n 5 -o /tmp/garage.pcap

# 3. Replay them
./rfox replay replay --input /tmp/garage.pcap --use-capture-cfg

# 4. Find the rolling-counter byte (or rule it out)
./rfox diff --input /tmp/garage.pcap

# 5. Identify the protocol's checksum
./rfox crc --input /tmp/garage.pcap
```

No dongle? The analysis subcommands work entirely on captures or hex
strings:

```bash
./rfox decode --hex aabbccdd -m auto
./rfox find-sync --hex aaaaaad391deadbeef
./rfox crc --hex 12345612fd
./rfox diff --hex aabbcc00 --hex aabbcc01 --hex aabbcc02
```

---

## Command reference

| group              | command                           | what it does                                      | needs hw |
| ------------------ | --------------------------------- | ------------------------------------------------- | :------: |
| **dongle**         | `devices`                         | list connected RfCat dongles                      |    ✓     |
|                    | `specan`                          | open the PySide6 spectrum analyser                |    ✓     |
| **RX**             | `scan`                            | RX loop, hex-print frames, optional pcap log      |    ✓     |
|                    | `sweep`                           | RSSI sweep across `--start..--stop`, optional CSV |    ✓     |
|                    | `logger`                          | headless RX → append every frame to a pcap        |    ✓     |
| **TX**             | `transmit`                        | binary string → OOK (raw or PWM-encoded)          |    ✓     |
|                    | `tx-hex`                          | raw bytes given as hex on the CLI                 |    ✓     |
|                    | `brute`                           | iterate a key space and transmit each value       |    ✓     |
|                    | `fuzz`                            | bit/byte-mutate a seed frame, retransmit          |    ✓     |
| **capture/replay** | `replay capture`                  | record N frames to a pcap                         |    ✓     |
|                    | `replay replay`                   | replay a pcap                                     |    ✓     |
| **analysis**       | `decode`                          | manchester/diff-manchester/PWM/raw decoders       |          |
|                    | `find-sync`                       | candidate sync words in a capture                 |          |
|                    | `find-repeats`                    | repeating bit patterns                            |          |
|                    | `crc`                             | try CRC-8/CRC-16 polynomials over capture tails   |          |
|                    | `diff`                            | bit-by-bit diff (find rolling-counter fields)     |          |
|                    | `decode-wav`                      | OOK decoder for WAV recordings                    |          |
| **workflow**       | `profile {save,show,list,delete}` | named radio configs                               |          |
|                    | `preset {list,show}`              | built-in protocol presets                         |          |

Each command also has full `--help`:

```bash
./rfox replay capture --help
./rfox find-sync --help
```

---

## Capture file format

Every capture/replay command shares one libpcap file
(magic `0xa1b2c3d4`, link type `DLT_USER0` = 147). Each packet payload
starts with a 24-byte `RFCT` pseudo-header recording the radio
configuration at capture time, followed by the raw on-air bytes:

```
struct rfct_pseudo_hdr {        // little-endian
    uint8_t  magic[4];          // "RFCT"
    uint8_t  version;           // 1
    uint8_t  modulation;        // 0=OOK 1=2FSK 2=GFSK 3=MSK 4=4FSK
    uint32_t freq_hz;
    uint32_t drate_bps;
    uint32_t chanbw_hz;
    int16_t  rssi_dbm10;        // dBm * 10, signed
    uint16_t sync_word;         // 0 if none
    uint8_t  payload[];
};
```

Read with the dataclass-based reader:

```python
from rflib.rfox import pcap

for frame in pcap.read("garage.pcap"):
    print(frame.ts, frame.cfg.summary(), frame.payload.hex())
```

Or open it in Wireshark / tshark — frames will appear as `data` under
`USER0`. A future Lua dissector could decode the pseudo-header field by
field, but the raw bytes are usable today with any pcap parser.

---

## Profiles & presets

Save a configuration once, reuse it forever:

```bash
./rfox profile save mygate -f 433.92e6 -r 2400 -m OOK --chanbw 325000
./rfox replay replay --input cap.pcap --profile mygate
```

Or jump straight to a built-in:

```bash
./rfox preset list
./rfox scan --preset ev1527
./rfox tx-hex --preset keyfob315 --hex aabbcc
```

CLI flags override the profile/preset, so `--preset ev1527 --freq 433.95e6`
works.

Built-in presets:

| name        | freq       | drate  | mod  | typical use                 |
| ----------- | ---------- | ------ | ---- | --------------------------- |
| `ev1527`    | 433.92 MHz | 2400   | OOK  | generic 433 MHz remotes     |
| `pt2262`    | 433.92 MHz | 1200   | OOK  | older garage / gate openers |
| `keeloq`    | 433.92 MHz | 2000   | OOK  | rolling-code keyfobs        |
| `keyfob315` | 315 MHz    | 2400   | OOK  | US automotive key fobs      |
| `srd868`    | 868.35 MHz | 4800   | 2FSK | EU short-range devices      |
| `ism915`    | 915 MHz    | 38 400 | 2FSK | US ISM band                 |
| `tpms433`   | 433.92 MHz | 19 200 | 2FSK | tyre-pressure sensors       |

---

## Adding a new command

Drop a module under `rflib/rfox/commands/`, expose three functions:

```python
HELP = "one-line description shown in --help and the menu"

def add_args(parser):
    """Attach argparse args. Use _common.add_radio_args / add_dongle_args."""

def prompt(args):                # optional
    """Walk the user through args interactively."""

def run(args):
    """Do the work. Return an exit code."""
```

Register it in `rflib/rfox/commands/__init__.py`. The CLI dispatcher and
the interactive menu both pick it up automatically.

Use `_common.cfg_from_args(args)` to honour `--preset` / `--profile`
before merging in CLI overrides — that's how every existing command keeps
its behaviour consistent.

---

## Tests

```bash
python -m unittest tests.test_rfox
```

The pcap roundtrip, presets, profiles, and analysis subcommands
(`decode`, `find-sync`, `find-repeats`, `crc`, `diff`, `decode-wav`) are
covered without hardware. The hardware-using TX commands are smoke-tested
by patching `open_dongle` to return `FakeRfCat`.

---

## Versioning & stability

rfox is versioned independently of rfcat. Anything in
`rflib.rfox.commands` is part of the public CLI; flag names and the
pcap pseudo-header layout are stable within a major version. Anything
under `rflib.rfox` (other than the public command modules) is internal
and may change without notice.

---

## Contributing

Pull requests welcome. Please:

1. Open an issue first for non-trivial changes.
2. Add a test under `tests/test_rfox.py` that exercises your code
   without hardware (use `FakeRfCat` for TX commands).
3. Match the existing argparse flag style (`-f`/`--freq` is Hz,
   `-r`/`--drate` is bps, etc.).
4. Don't add commands whose primary purpose is signal interference or
   disruption.

By contributing, you agree your contribution is licensed under the MIT
License (see [`LICENSE`](LICENSE)).

---

## License

rfox's own source — the entry script, the `rflib/rfox/` package,
and `tests/test_rfox.py` — is released under the **MIT License**. See
[`LICENSE`](LICENSE).

It builds on top of [rfcat-py3](https://github.com/qu-crypt/rfcat),
which is distributed under the MIT License.

---

## Acknowledgements

- [@atlas0fd00m](https://github.com/atlas0fd00m) for the original rfcat and rflib.
- [@qu-crypt](https://github.com/qu-crypt) for the Python 3 port ([rfcat-py3](https://github.com/qu-crypt/rfcat)) and dongle firmware.
- [@AndrewMohawk](https://github.com/AndrewMohawk) — the original
  RfCatHelpers project that mapped out the most useful day-to-day
  recipes and motivated this tool.
- The Ubertooth, GNU Radio, and HackRF communities for decades of
  prior art in sub-GHz tooling.
