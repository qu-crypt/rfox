"""Wrap rflib's spectrum analyzer GUI."""
from . import _common

HELP = "Open the rflib spectrum analyzer GUI (requires PySide6)"


def add_args(p):
    _common.add_dongle_args(p)
    p.add_argument("-f", "--centfreq", type=float, default=915e6,
                   help="centre frequency Hz (default: 915e6)")
    p.add_argument("-c", "--inc", type=float, default=250e3,
                   help="channel spacing Hz")
    p.add_argument("-n", "--specchans", type=int, default=104,
                   help="number of channels")


def prompt(args):
    args.centfreq = float(input(f"centre freq Hz [{args.centfreq}]: ") or args.centfreq)


def run(args):
    import rflib
    d = rflib.RfCat(idx=args.index)
    d.specan(args.centfreq, args.inc, args.specchans)
    return 0
