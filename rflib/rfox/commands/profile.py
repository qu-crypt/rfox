"""Save/load/list/delete saved RFConfig profiles."""
import sys
from . import _common

HELP = "Manage saved radio profiles in ~/.rfcat/profiles.json"


def add_args(p):
    sub = p.add_subparsers(dest="action", required=True)

    p_list = sub.add_parser("list", help="list saved profiles")

    p_show = sub.add_parser("show", help="print one profile")
    p_show.add_argument("name")

    p_save = sub.add_parser("save", help="save a profile from CLI args")
    p_save.add_argument("name")
    _common.add_radio_args(p_save, sync=True, deviation=True, channel=True,
                           pktlen=True, power=True, preamble=True, fixed=True)

    p_del = sub.add_parser("delete", help="delete a profile")
    p_del.add_argument("name")


def prompt(args):
    if not getattr(args, "action", None):
        print("\n[a]ction = list, show, save, delete")
        args.action = (input("action [list]: ").strip() or "list").lower()
    if args.action in ("show", "delete"):
        args.name = input("name: ").strip()
    if args.action == "save":
        args.name = input("name: ").strip()
        # let user fill in the radio fields with defaults
        from ..config import RFConfig
        cfg = RFConfig()
        for field in ("freq", "drate", "modulation", "chanbw", "deviation",
                      "channel", "pktlen", "power", "preamble"):
            cur = getattr(cfg, field)
            v = input(f"  {field} [{cur}]: ").strip()
            if v:
                if field in ("modulation",):
                    setattr(args, field, v)
                elif field in ("channel", "pktlen", "power", "preamble"):
                    setattr(args, field, int(v, 0))
                else:
                    setattr(args, field, float(v))


def run(args):
    from .. import profiles

    if args.action == "list":
        names = profiles.list_profiles()
        if not names:
            print("no profiles saved. use 'profile save NAME' to create one.")
            return 0
        for name, cfg in sorted(names.items()):
            print(f"{name:<20} {cfg.summary()}")
        return 0

    if args.action == "show":
        try:
            cfg = profiles.load(args.name)
        except KeyError as e:
            print(e, file=sys.stderr)
            return 1
        for k, v in cfg.to_dict().items():
            print(f"  {k}: {v}")
        return 0

    if args.action == "save":
        cfg = _common.cfg_from_args(args)
        profiles.save(args.name, cfg)
        print(f"saved {args.name!r}: {cfg.summary()}")
        return 0

    if args.action == "delete":
        try:
            profiles.delete(args.name)
            print(f"deleted {args.name!r}")
        except KeyError as e:
            print(e, file=sys.stderr)
            return 1
        return 0

    print(f"unknown action: {args.action}", file=sys.stderr)
    return 1
