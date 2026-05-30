"""
gog -- one CLI entrypoint for Google services, sharing the tools/auth.py token.

    python tools/gog.py <service> <command> [args]
    gog <service> <command> [args]          # if gog.cmd is on PATH

Services:
    gmail   list/read/send/label/draft/trash
    cal     agenda/list/create/edit/delete/quickadd   (module: gcal.cli)
    tasks   lists/list/add/complete/delete

Each service module exposes main(argv); the dispatcher forwards everything after
the service name to it. Mutating commands accept --dry-run.
"""

import importlib
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent

# service name -> (module, one-line command summary)
SERVICES = {
    "gmail": ("gmail.cli", "list/read/send/label/draft/trash"),
    "cal": ("gcal.cli", "agenda/list/create/edit/delete/quickadd"),
    "tasks": ("tasks.cli", "lists/list/add/complete/delete"),
}


def usage():
    print("gog -- CLI for Google services (shares tools/auth.py OAuth token)\n")
    print("Usage: gog <service> <command> [args]   (or: python tools/gog.py ...)\n")
    print("Services:")
    for name, (_mod, cmds) in SERVICES.items():
        print(f"  {name:7}{cmds}")
    print("\nExamples:")
    print("  gog gmail list --max 5")
    print("  gog cal agenda --days 7")
    print("  gog tasks lists")
    print("\nMutating commands accept --dry-run.")


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        usage()
        sys.exit(0)
    svc = argv[0]
    if svc not in SERVICES:
        print(f"error: unknown service '{svc}'. Known: {', '.join(SERVICES)}", file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, str(TOOLS_DIR))
    module = importlib.import_module(SERVICES[svc][0])
    module.main(argv[1:])


if __name__ == "__main__":
    main()
