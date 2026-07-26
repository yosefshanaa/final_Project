"""Command-line entry points: peer | sim | replay | smoke.

stdout carries machine-readable JSON only; human logs go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path

from .domain.rules import POLICE, THIEF


def _err(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def cmd_peer(args: argparse.Namespace) -> int:
    from .infra.mcp_client import McpLink
    from .peer.runtime import PeerRuntime

    config_dir = Path(args.config_dir or f"config/{args.role}")
    runtime = PeerRuntime(args.role, config_dir, out_dir=Path(args.out), seed=args.seed,
                          counted=args.counted, prior_counted_games=args.prior_counted,
                          num_games=args.games)
    runtime.start_server()
    if not runtime.connect(McpLink(runtime.peer.opponent_url)):
        return 2
    result_holder: dict = {}

    def play() -> None:
        result_holder["result"] = runtime.run_series()

    worker = threading.Thread(target=play, name="series", daemon=True)
    worker.start()
    if not args.no_gui:
        try:
            from .gui.live_view import LiveView

            LiveView(runtime.service.status, f"p2p-pursuit - {args.role}").run()
        except Exception as exc:  # noqa: BLE001 - no display etc.
            _err(f"[gui] disabled ({exc}); running headless")
    worker.join()
    result = result_holder.get("result", {})
    transport = _pick_email_transport(runtime.peer.email_mode)
    receipt = runtime.report(result, transport)
    _err(f"[email] {receipt}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _pick_email_transport(mode: str):
    from .infra.email_sender import DryRunTransport

    if mode != "send":
        _err(f"[email] mode={mode!r}: dry-run transport (send-only scope has no drafts)")
    elif Path("token.json").exists():
        try:
            from .infra.email_sender import GmailTransport

            return GmailTransport()
        except Exception as exc:  # noqa: BLE001
            _err(f"[email] Gmail unavailable ({exc}); dry-run transport")
    else:
        _err("[email] no token.json; dry-run transport (report written, not sent)")
    return DryRunTransport()


def cmd_sim(args: argparse.Namespace) -> int:
    from .domain.game_ids import make_game_id, new_game_uid
    from .peer import log_manager
    from .peer.local_match import run_series
    from .report import artifacts, results
    from .shared import sysinfo
    from .shared.config import load_role

    shared, police_cfg = load_role(Path("config/police"))
    _, thief_cfg = load_role(Path("config/thief"))
    game_uid, game_id = new_game_uid(), make_game_id("police-sim", "thief-sim")
    out = Path(args.out) / f"sim-{game_id}"
    rows: list[dict] = []

    def per_sub_game(police, thief, outcome) -> None:
        audit = {"mine_of_them": outcome.audit_of_thief,
                 "theirs_of_us": outcome.audit_of_police}
        log = log_manager.build_log(police, thief.my_records, game_uid=game_uid,
                                    game_id=game_id, audit=audit)
        log_manager.write_log(log, out)
        artifacts.write_config_copy(out, game_id, outcome.index, shared.raw, game_uid)
        rows.append(results.sub_game_row(
            index=outcome.index, ending=outcome.ending, winner=outcome.winner,
            cause=outcome.cause, police_score=outcome.police_score,
            thief_score=outcome.thief_score, moves_played=outcome.thief_steps,
            github_commit=sysinfo.git_commit(),
            audit_verdict=outcome.audit_of_thief["verdict"]))
        _err(f"[sim] g{outcome.index}: {outcome.ending} winner={outcome.winner} "
             f"({outcome.cause})")

    series = run_series(shared, police_cfg, thief_cfg, num_games=args.games,
                        seed=args.seed, on_sub_game=per_sub_game)
    result = results.build_result(
        game_uid=game_uid, game_id=game_id,
        my_group={"group_id": police_cfg.group_id, "members": police_cfg.members,
                  "repos": police_cfg.repos},
        opp_group={"group_id": thief_cfg.group_id}, sub_games=rows,
        police_total=series.police_total, thief_total=series.thief_total,
        tie_score=shared.scoring.get("tie_score", 2), tokens_used=series.tokens_used,
        github_commit=sysinfo.git_commit(), my_role=POLICE, mutual_agreement=True)
    artifacts.write_result(out, game_id, result)
    _err(f"[sim] totals police={series.police_total} thief={series.thief_total} "
         f"winner={series.series_winner}; artifacts in {out}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from .gui.replay_data import load_log, timeline, verdict_of

    path = Path(args.log)
    log = load_log(path)
    verdict, mine, theirs = verdict_of(log)
    if args.no_gui:
        for item in timeline(log):
            stamp = "Verified OK" if item["verified"] else "TAMPERED"
            barrier = f" barrier={item['barrier']}" if item["barrier"] else ""
            _err(f"{item['role']:6s} step {item['step']:2d} -> {item['pos_after']}"
                 f"{barrier}  [{stamp}]  {item['hint'][:44]}")
        print(json.dumps({"log": str(path), "verdict": verdict,
                          "records_checked": len(mine) + len(theirs)}))
        return 0 if verdict == "Verified OK" else 3
    from .gui.replay_view import ReplayView

    ReplayView(path).run()
    return 0


def cmd_authorize(args: argparse.Namespace) -> int:
    from .infra.email_sender import run_authorization

    _err(run_authorization(Path(args.credentials), Path(args.token)))
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    from .infra.mcp_client import McpLink

    link = McpLink(args.url)
    health = link.health(timeout=10)
    print(json.dumps({"url": args.url, "health": health}))
    return 0 if health.get("ok") else 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="p2p-pursuit")
    sub = parser.add_subparsers(dest="command", required=True)

    peer = sub.add_parser("peer", help="run one autonomous peer over the network")
    peer.add_argument("--role", choices=[POLICE, THIEF], required=True)
    peer.add_argument("--config-dir", default=None)
    peer.add_argument("--no-gui", action="store_true")
    peer.add_argument("--seed", type=int, default=None)
    peer.add_argument("--out", default="results")
    peer.add_argument("--counted", action="store_true",
                      help="a counted league match (enforces 6 sub-games)")
    peer.add_argument("--prior-counted", type=int, default=0,
                      help="truthful count of prior counted games (rule #37)")
    peer.add_argument("--games", type=int, default=None)
    peer.set_defaults(fn=cmd_peer)

    sim = sub.add_parser("sim", help="in-process series (tactics lab / demo)")
    sim.add_argument("--games", type=int, default=None)
    sim.add_argument("--seed", type=int, default=None)
    sim.add_argument("--out", default="results")
    sim.set_defaults(fn=cmd_sim)

    replay = sub.add_parser("replay", help="verify + view a sealed sub-game log")
    replay.add_argument("--log", required=True)
    replay.add_argument("--no-gui", action="store_true")
    replay.set_defaults(fn=cmd_replay)

    smoke = sub.add_parser("smoke", help="probe a peer's MCP endpoint")
    smoke.add_argument("url")
    smoke.set_defaults(fn=cmd_smoke)

    auth = sub.add_parser("authorize", help="one-time Gmail OAuth consent (writes token.json)")
    auth.add_argument("--credentials", default="credentials.json")
    auth.add_argument("--token", default="token.json")
    auth.set_defaults(fn=cmd_authorize)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
