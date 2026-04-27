"""Two-dongle scan + jam (DualRF clone).

ETHICS / LEGAL: RF jamming is illegal in most jurisdictions. Use this only
on equipment you own, in a shielded enclosure, or under written authorisation.
See RFOX.md for the full disclaimer.
"""
import time
from . import _common

HELP = "Two dongles: one scans, the other jams on detect"


def add_args(p):
    p.add_argument("--scanner-index", type=int, default=0)
    p.add_argument("--jammer-index", type=int, default=1)
    p.add_argument("-f", "--freq", type=float, default=433.92e6,
                   help="centre / jam freq Hz")
    p.add_argument("--start", type=float, default=None,
                   help="if set, scan over [start, stop] instead of one freq")
    p.add_argument("--stop", type=float, default=None)
    p.add_argument("--step", type=float, default=50e3)
    p.add_argument("--min-rssi", type=float, default=-50.0,
                   help="dBm threshold to trigger a jam")
    p.add_argument("--jam-seconds", type=float, default=2.0)
    p.add_argument("--bw", type=float, default=200e3)


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq}]: ") or args.freq)
    args.min_rssi = float(input(f"min rssi dBm [{args.min_rssi}]: ") or args.min_rssi)
    args.jam_seconds = float(input(f"jam s [{args.jam_seconds}]: ") or args.jam_seconds)


def run(args):
    from .. import dongle
    scanner = dongle.open_dongle(idx=args.scanner_index)
    jammer = dongle.open_dongle(idx=args.jammer_index)

    scanner.setMdmChanBW(args.bw)
    scanner.setModeRX()

    payload = b"\xff" * 240

    def jam_for(seconds, freq):
        jammer.setFreq(freq)
        deadline = time.time() + seconds
        while time.time() < deadline:
            jammer.RFxmit(payload)
        jammer.setModeIDLE()

    sweep = args.start is not None and args.stop is not None
    print("# scanjam running. ctrl-c to stop.")
    try:
        if sweep:
            f = args.start
            while True:
                scanner.setFreq(f)
                time.sleep(0.005)
                rssi = _read_rssi(scanner)
                if rssi >= args.min_rssi:
                    print(f"!! {f/1e6:.4f} MHz {rssi:.1f} dBm — jamming")
                    jam_for(args.jam_seconds, f)
                f += args.step
                if f > args.stop:
                    f = args.start
        else:
            scanner.setFreq(args.freq)
            jammer.setFreq(args.freq)
            while True:
                rssi = _read_rssi(scanner)
                if rssi >= args.min_rssi:
                    print(f"!! {args.freq/1e6:.4f} MHz {rssi:.1f} dBm — jamming")
                    jam_for(args.jam_seconds, args.freq)
                else:
                    time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        try: scanner.setModeIDLE()
        except Exception: pass
        try: jammer.setModeIDLE()
        except Exception: pass
    return 0


def _read_rssi(d):
    raw = d.getRSSI()
    if isinstance(raw, (bytes, bytearray)):
        raw = raw[0]
    raw = int(raw)
    if raw >= 128:
        raw -= 256
    return raw / 2.0 - 74.0
