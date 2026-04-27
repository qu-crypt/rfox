"""Wrap rflib.bits.findSyncWord(Doubled) over a capture."""
from . import _common

HELP = "Find candidate sync words in a capture or hex string"


def add_args(p):
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--hex", type=_common.hex_arg)
    src.add_argument("--input", help="pcap path")
    p.add_argument("--frame-index", type=int, default=0)
    p.add_argument("--sensitivity", type=int, default=4)
    p.add_argument("--min-preamble", type=int, default=2)
    p.add_argument("--doubled", action="store_true",
                   help="search for 32-bit doubled sync words")


def prompt(args):
    src = input("source [hex/pcap]: ").strip().lower() or "hex"
    if src == "hex":
        args.hex = _common.hex_arg(input("hex: ").strip())
    else:
        args.input = input("pcap: ").strip()


def run(args):
    from .. import pcap
    from rflib import bits as rfbits

    if args.hex:
        data = args.hex
    elif args.input:
        frames = list(pcap.read(args.input))
        if not frames:
            print("empty pcap.")
            return 1
        # search across all frames concatenated for better odds
        data = b"".join(f.payload for f in frames)
    else:
        print("provide --hex or --input")
        return 2

    if args.doubled:
        out = rfbits.findSyncWordDoubled(data,
                                          sensitivity=args.sensitivity,
                                          minpreamble=args.min_preamble)
    else:
        out = rfbits.findSyncWord(data,
                                   sensitivity=args.sensitivity,
                                   minpreamble=args.min_preamble)
    if not out:
        print("no candidate sync words found.")
        return 1
    print(f"# {len(out)} candidate sync word(s):")
    for w in out:
        if args.doubled:
            print(f"  {w:#010x}")
        else:
            print(f"  {w:#06x}")
    return 0
