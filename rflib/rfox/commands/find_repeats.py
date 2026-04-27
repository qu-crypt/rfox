"""Wrap rflib.bits.detectRepeatPatterns over a capture."""
from . import _common

HELP = "Find repeating bit patterns in a capture"


def add_args(p):
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--hex", type=_common.hex_arg)
    src.add_argument("--input", help="pcap path")
    p.add_argument("--frame-index", type=int, default=0)
    p.add_argument("--size", type=int, default=64,
                   help="pattern size in bits (default: 64)")
    p.add_argument("--min-entropy", type=float, default=0.07)


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
        data = frames[args.frame_index].payload
    else:
        print("provide --hex or --input")
        return 2

    out = rfbits.detectRepeatPatterns(data, size=args.size,
                                       minEntropy=args.min_entropy)
    if not out:
        print("no repeating patterns found.")
        return 1
    print(f"# {len(out)} pattern(s):")
    for s1, s2, length, val in out:
        print(f"  bits[{s1}:{s1+length}] == bits[{s2}:{s2+length}]  "
              f"(len={length})  val={val:#x}")
    return 0
