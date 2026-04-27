"""Bit-by-bit diff of frames in a capture - find rolling counters."""
from . import _common

HELP = "Compare frames bit-by-bit; highlight always-same vs ever-changing bits"


def add_args(p):
    p.add_argument("--input", required=False, help="pcap to diff")
    p.add_argument("--hex", action="append", default=[],
                   help="hex frame (repeat for multiple)")
    p.add_argument("--show-frames", action="store_true",
                   help="also print each frame as binary")


def prompt(args):
    args.input = input("pcap path: ").strip()


def _to_bits(b):
    return "".join(format(c, "08b") for c in b)


def run(args):
    from .. import pcap
    payloads = []
    if args.input:
        payloads = [f.payload for f in pcap.read(args.input)]
    if args.hex:
        for h in args.hex:
            payloads.append(_common.hex_arg(h))

    if len(payloads) < 2:
        print("need at least 2 frames to diff")
        return 2

    n = min(len(p) for p in payloads)
    bits = [_to_bits(p[:n]) for p in payloads]
    width = n * 8

    counts = [0] * width  # how many frames had a 1 at this bit
    for b in bits:
        for i, c in enumerate(b):
            if c == "1":
                counts[i] += 1

    same_zero = [i for i, c in enumerate(counts) if c == 0]
    same_one = [i for i, c in enumerate(counts) if c == len(bits)]
    differ = [i for i in range(width) if i not in same_zero and i not in same_one]

    print(f"# {len(payloads)} frames, {n} bytes ({width} bits) compared")
    print(f"  always 0 : {len(same_zero)} bits")
    print(f"  always 1 : {len(same_one)} bits")
    print(f"  changing : {len(differ)} bits")

    if differ:
        # group consecutive changing bits into ranges
        ranges = []
        s = differ[0]
        prev = differ[0]
        for i in differ[1:]:
            if i == prev + 1:
                prev = i
            else:
                ranges.append((s, prev))
                s = prev = i
        ranges.append((s, prev))
        print("  changing ranges (bit indices):")
        for a, b in ranges:
            print(f"    [{a:4d}..{b:4d}]  ({b - a + 1} bits)  byte[{a // 8}].bit{a % 8}..byte[{b // 8}].bit{b % 8}")

    if args.show_frames:
        for i, b in enumerate(bits):
            print(f"  frame {i}: {b}")
    return 0
