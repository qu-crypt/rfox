"""Built-in protocol presets (read-only)."""
HELP = "List or print built-in radio presets"


def add_args(p):
    sub = p.add_subparsers(dest="action", required=False)
    p_list = sub.add_parser("list", help="list presets")
    p_show = sub.add_parser("show", help="print one preset")
    p_show.add_argument("name")


def prompt(args):
    if not getattr(args, "action", None):
        args.action = (input("action [list]: ").strip() or "list").lower()
    if args.action == "show":
        args.name = input("name: ").strip()


def run(args):
    from .. import presets
    action = getattr(args, "action", None) or "list"

    if action == "list":
        for n in presets.names():
            cfg = presets.get(n)
            print(f"{n:<12} {cfg.summary()}")
        return 0

    if action == "show":
        try:
            cfg = presets.get(args.name)
        except KeyError as e:
            print(e)
            return 1
        for k, v in cfg.to_dict().items():
            print(f"  {k}: {v}")
        return 0

    print(f"unknown action: {action}")
    return 1
