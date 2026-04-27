"""Port of the original decodeOOK.py: peak-spacing decode of an OOK WAV."""
import wave
import struct
from . import _common

HELP = "Decode an OOK signal from a WAV file (peak spacing analysis)"


def add_args(p):
    p.add_argument("--input", required=False, help="WAV file path")
    p.add_argument("--threshold-bias", type=float, default=0.0,
                   help="bias added to mean amplitude (default: 0)")
    p.add_argument("--top", type=int, default=10,
                   help="show this many top-ranked candidates")


def prompt(args):
    args.input = input("WAV path: ").strip()


def _samples(path):
    with wave.open(path, "rb") as w:
        nch = w.getnchannels()
        sw = w.getsampwidth()
        nframes = w.getnframes()
        raw = w.readframes(nframes)
    fmt = {1: "b", 2: "h", 4: "i"}.get(sw)
    if fmt is None:
        raise ValueError(f"unsupported sample width {sw}")
    samples = struct.unpack("<%d%s" % (len(raw) // sw, fmt), raw)
    if nch > 1:
        samples = samples[::nch]  # left channel
    return list(samples)


def run(args):
    if not args.input:
        print("provide --input PATH")
        return 2
    samples = _samples(args.input)
    if not samples:
        print("empty WAV.")
        return 1

    mean = sum(abs(s) for s in samples) / len(samples)
    threshold = mean + args.threshold_bias
    # find rising edges over threshold
    peaks = []
    above = False
    for i, s in enumerate(samples):
        if abs(s) > threshold and not above:
            peaks.append(i)
            above = True
        elif abs(s) <= threshold * 0.5:
            above = False

    if len(peaks) < 4:
        print(f"only {len(peaks)} peaks found (mean={mean:.0f}, threshold={threshold:.0f})")
        return 1

    # measure peak spacings, classify short vs long
    spacings = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]
    if not spacings:
        return 1
    avg = sum(spacings) / len(spacings)
    bits = "".join("1" if s < avg else "0" for s in spacings)

    # split on long gaps (> 2 * avg)
    groups = []
    cur = []
    for i, s in enumerate(spacings):
        if s > 2 * avg and cur:
            groups.append(cur)
            cur = []
        else:
            cur.append("1" if s < avg else "0")
    if cur:
        groups.append(cur)

    # rank groups by frequency
    counts = {}
    for g in groups:
        if len(g) < 8:
            continue
        bs = "".join(g)
        counts[bs] = counts.get(bs, 0) + 1

    print(f"# {len(samples)} samples, mean={mean:.0f}, threshold={threshold:.0f}")
    print(f"# {len(peaks)} peaks, {len(groups)} groups, {len(counts)} unique sequences")
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    for bs, n in ranked[:args.top]:
        # right-pad to byte boundary for the hex view
        pad = (8 - len(bs) % 8) % 8
        bytestr = bs + "0" * pad
        as_hex = bytes(int(bytestr[i:i+8], 2) for i in range(0, len(bytestr), 8)).hex()
        print(f"  count={n:3d}  bits={bs}  hex={as_hex}")
    return 0
