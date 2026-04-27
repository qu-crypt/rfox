"""Sweep a frequency range, sample RSSI per channel, print or CSV-dump."""
import csv
import sys
import time
from . import _common

HELP = "RSSI sweep across a frequency range"


def add_args(p):
    _common.add_dongle_args(p)
    p.add_argument("--start", type=float, default=433.0e6, help="start freq Hz")
    p.add_argument("--stop", type=float, default=434.0e6, help="stop freq Hz")
    p.add_argument("--step", type=float, default=50e3, help="step Hz")
    p.add_argument("--dwell-ms", type=int, default=20,
                   help="ms to dwell on each step")
    p.add_argument("-n", "--passes", type=int, default=1,
                   help="number of full sweeps (0 = forever)")
    p.add_argument("--csv", help="write CSV (freq,rssi_dbm,timestamp) to file")
    p.add_argument("--bw", type=float, default=200e3, help="channel BW Hz")
    p.add_argument("--ascii-bar", action="store_true",
                   help="print an ASCII bar per step")


def prompt(args):
    args.start = float(input(f"start Hz [{args.start}]: ") or args.start)
    args.stop = float(input(f"stop Hz [{args.stop}]: ") or args.stop)
    args.step = float(input(f"step Hz [{args.step}]: ") or args.step)
    n = input(f"passes [{args.passes}]: ").strip()
    if n:
        args.passes = int(n)


def _bar(rssi, lo=-120, hi=-20, width=40):
    if rssi <= lo:
        return ""
    if rssi >= hi:
        return "#" * width
    pct = (rssi - lo) / (hi - lo)
    return "#" * int(pct * width)


def run(args):
    from .. import dongle
    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    d.setMdmModulation(_safe_mod(d))  # 2FSK, narrow, just to get RSSI
    d.setMdmChanBW(args.bw)
    d.setModeRX()

    csv_writer = None
    csv_fp = None
    if args.csv:
        csv_fp = open(args.csv, "a", newline="")
        csv_writer = csv.writer(csv_fp)
        if csv_fp.tell() == 0:
            csv_writer.writerow(["timestamp", "freq_hz", "rssi_dbm"])

    sweep_count = 0
    print(f"# sweep {args.start/1e6:.3f} -> {args.stop/1e6:.3f} MHz "
          f"step {args.step/1e3:.1f} kHz")
    try:
        while args.passes == 0 or sweep_count < args.passes:
            sweep_count += 1
            f = args.start
            while f <= args.stop:
                d.setFreq(f)
                time.sleep(args.dwell_ms / 1000.0)
                rssi = _read_rssi(d)
                ts = time.time()
                if args.ascii_bar:
                    print(f"{f/1e6:9.4f} MHz  {rssi:6.1f} dBm  {_bar(rssi)}")
                else:
                    print(f"{f/1e6:9.4f} MHz  {rssi:6.1f} dBm")
                if csv_writer:
                    csv_writer.writerow([f"{ts:.3f}", int(f), f"{rssi:.1f}"])
                f += args.step
            if args.passes != 1:
                print(f"# pass {sweep_count} done")
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        if csv_fp:
            csv_fp.close()
        try:
            d.setModeIDLE()
        except Exception:
            pass
    return 0


def _safe_mod(d):
    import rflib
    return rflib.MOD_2FSK


def _read_rssi(d):
    raw = d.getRSSI()
    if isinstance(raw, (bytes, bytearray)):
        raw = raw[0]
    raw = int(raw)
    # CC1111 RSSI: signed, divide by 2 then offset -74 (rough rule of thumb)
    if raw >= 128:
        raw -= 256
    return raw / 2.0 - 74.0
