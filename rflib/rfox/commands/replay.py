"""Capture frames to pcap and/or replay them."""
import time
from . import _common

HELP = "Capture frames to a pcap or replay frames from a pcap"


def add_args(p):
    sub = p.add_subparsers(dest="action", required=True)

    p_cap = sub.add_parser("capture", help="record N frames to a pcap")
    _common.add_dongle_args(p_cap)
    _common.add_profile_preset(p_cap)
    _common.add_radio_args(p_cap, sync=True, deviation=True, pktlen=True,
                           preamble=True, fixed=True)
    p_cap.add_argument("-n", "--count", type=int, default=3)
    p_cap.add_argument("-o", "--output", required=True, help="pcap path")
    p_cap.add_argument("--min-rssi", type=float, default=None)
    p_cap.add_argument("--timeout-ms", type=int, default=1000)

    p_rep = sub.add_parser("replay", help="replay all frames from a pcap")
    _common.add_dongle_args(p_rep)
    _common.add_profile_preset(p_rep)
    _common.add_radio_args(p_rep, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    p_rep.add_argument("--input", required=True, help="pcap to replay")
    p_rep.add_argument("-t", "--repeat", type=int, default=1,
                       help="repeat each frame N times")
    p_rep.add_argument("--use-capture-cfg", action="store_true",
                       help="use the cfg saved per-frame instead of CLI args")
    p_rep.add_argument("--gap-ms", type=int, default=200,
                       help="ms between frames")
    p_rep.add_argument("--wait-key", action="store_true",
                       help="wait for Enter before each frame")


def prompt(args):
    if not getattr(args, "action", None):
        args.action = (input("action [capture/replay]: ").strip() or "capture").lower()
    if args.action == "capture":
        args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
        args.drate = float(input(f"drate bps [{args.drate or 4800}]: ") or (args.drate or 4800))
        args.modulation = input(f"modulation [{args.modulation or 'OOK'}]: ").strip() or (args.modulation or "OOK")
        args.count = int(input(f"count [{args.count}]: ") or args.count)
        args.output = input("output pcap: ").strip()
    else:
        args.input = input("input pcap: ").strip()
        n = input(f"repeat [{args.repeat}]: ").strip()
        if n:
            args.repeat = int(n)


def run(args):
    if args.action == "capture":
        return _capture(args)
    return _replay(args)


def _capture(args):
    from .. import dongle, pcap
    cfg = _common.cfg_from_args(args)
    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    d.setModeRX()

    print(f"# capture {args.count} frames to {args.output}: {cfg.summary()}")
    seen = 0
    with pcap.PcapWriter(args.output) as w:
        while seen < args.count:
            try:
                payload, ts = d.RFrecv(args.timeout_ms)
            except Exception as e:
                if "Timeout" in repr(e):
                    continue
                raise
            try:
                raw = d.getRSSI()
                raw = raw[0] if isinstance(raw, (bytes, bytearray)) else int(raw)
                if raw >= 128:
                    raw -= 256
                rssi = raw / 2.0 - 74.0
            except Exception:
                rssi = 0.0
            if args.min_rssi is not None and rssi < args.min_rssi:
                continue
            print(f"[{seen+1}/{args.count}] {rssi:6.1f} dBm  "
                  f"{len(payload)}B  {payload[:32].hex()}")
            w.write(pcap.CapturedFrame(ts=time.time(), cfg=cfg,
                                        rssi=rssi, payload=payload))
            seen += 1
    d.setModeIDLE()
    print(f"# saved {seen} frames -> {args.output}")
    return 0


def _replay(args):
    from .. import dongle, pcap
    frames = list(pcap.read(args.input))
    if not frames:
        print("no frames in capture file.")
        return 1

    print(f"# replay {len(frames)} frames from {args.input} x{args.repeat}")
    d = dongle.open_dongle(idx=args.index, debug=args.debug)

    if args.use_capture_cfg:
        last_sig = None
    else:
        cfg = _common.cfg_from_args(args, base=frames[0].cfg)
        dongle.apply_config(d, cfg)

    for n, frame in enumerate(frames, 1):
        if args.use_capture_cfg:
            sig = (frame.cfg.freq, frame.cfg.drate, frame.cfg.modulation,
                   frame.cfg.chanbw)
            if sig != last_sig:
                dongle.apply_config(d, frame.cfg)
                last_sig = sig
        if args.wait_key:
            input(f"  frame {n}/{len(frames)} - press Enter to send...")
        for _ in range(args.repeat):
            d.RFxmit(frame.payload)
            time.sleep(args.gap_ms / 1000.0)
        print(f"  sent frame {n}/{len(frames)} ({len(frame.payload)}B)")
    d.setModeIDLE()
    return 0
