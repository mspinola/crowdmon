"""Build the damage panel and write it to `CROWDMON_STORE`.

    COTDATA_STORE=~/code/cotdata_store CROWDMON_STORE=~/code/crowdmon_store \
        .venv/bin/python bin/publish_damage.py

Normally driven by `bin/publish_damage.sh`, which defaults both env vars because launchd
reads no shell profile. Everything of substance is in `crowdmon.futures.publish`; this file
is argument parsing and a printed summary, deliberately, so that what gets published is
decided by the package and not by a script.

`--dry-run` builds and prints without writing, which is the mode to use when checking a
store you are not sure has finished syncing.
"""
import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None,
                        help="output root; defaults to $CROWDMON_STORE")
    parser.add_argument("--keep", type=int, default=None,
                        help="weeks of history to retain (default 8)")
    parser.add_argument("--no-commonality", action="store_true",
                        help="skip the Amihud panel behind `beta`. Cheap to leave on "
                             "(about 1.3s), and without it README reading instruction 4 "
                             "has no per-row carrier at all, so this is for debugging "
                             "rather than for scheduled runs")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and summarise, write nothing")
    args = parser.parse_args(argv)

    from crowdmon.futures.publish import (
        build_damage_panel,
        panel_manifest,
        publish_panel,
        store_root,
    )

    if not args.dry_run:
        # Resolved BEFORE the expensive build, so an unset store is a message in a second
        # rather than after the whole chain has run.
        store_root(args.out)

    build = build_damage_panel(with_commonality=not args.no_commonality)
    counts = panel_manifest(build)["counts"]
    week = build.report_date.date().isoformat()

    print(f"report week {week}")
    print(f"  markets            {counts['markets']}")
    print(f"  scored sell / buy  {counts['scored_sell']} / {counts['scored_buy']}")
    print(f"  triggers sell/buy  {counts['trigger_sell']} / {counts['trigger_buy']}")
    print(f"  rows (full history){counts['rows']:>7,}")
    print(f"  beta attached      {build.provenance['with_commonality']} "
          f"({build.provenance['n_betas']} markets)")

    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    kwargs = {} if args.keep is None else {"keep_weeks": args.keep}
    written = publish_panel(build, args.out, **kwargs)
    print(f"\nwrote {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
