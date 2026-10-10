"""Turn benchmark/results/results.jsonl into numbers, Markdown tables and charts.

    python -m benchmark.summarize

Writes benchmark/results/summary.json, benchmark/results/summary.md and PNG charts in docs/images/.
Energy figures use metrics.py (cited cloud baseline, device watts x measured local time).
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import metrics  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
IMAGES = os.path.join(HERE, "..", "..", "docs", "images")

# Reference palette, first three categorical slots (validated all-pairs for colour-vision deficiency).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def pct(n, d):
    return round(100 * n / d, 1) if d else None


def p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(0.9 * (len(xs) - 1)))] if xs else None


def footprint(rows, watts, retries=False):
    """Total estimated footprint of a set of routed prompts at a given device power."""
    tot = {"wh": 0.0, "gco2e": 0.0, "water_ml": 0.0}
    old = config.DEVICE_ACTIVE_WATTS
    config.DEVICE_ACTIVE_WATTS = watts
    try:
        for r in rows:
            parts = [metrics.local_footprint(r["local_s"]) if r["decision"] == "local" else metrics.cloud_footprint()]
            if retries and r["decision"] == "local" and r.get("local_acceptable") is False:
                parts.append(metrics.cloud_footprint())  # user re-asks in the cloud
            for p in parts:
                for k in tot:
                    tot[k] += p[k]
    finally:
        config.DEVICE_ACTIVE_WATTS = old
    return tot


def summarize(rows):
    n = len(rows)
    hit = [r for r in rows if r["decision"] == r["expected"]]
    conf = {f"{e}->{d}": sum(1 for r in rows if r["expected"] == e and r["decision"] == d)
            for e in ("local", "cloud") for d in ("local", "cloud")}
    judged = [r for r in rows if "local_acceptable" in r]
    rl = [r for r in judged if r["decision"] == "local"]
    rc = [r for r in judged if r["decision"] == "cloud"]
    acc = lambda rs: pct(sum(r["local_acceptable"] for r in rs), len(rs))
    mean_score = lambda rs: round(statistics.mean(r["judge_score"] for r in rs), 2) if rs else None

    local_rows = [r for r in rows if r["decision"] == "local"]
    lat_local = [r["local_s"] for r in local_rows]
    lat_cloud_same = [r["cloud_s"] for r in local_rows if "cloud_s" in r]
    tps = [r["local_out_tokens"] / r["local_s"] for r in rows if r["local_s"] > 0 and r["local_out_tokens"]]

    base = {k: v * n for k, v in metrics.cloud_footprint().items()}
    gr = footprint(rows, config.DEVICE_ACTIVE_WATTS)
    gr_retry = footprint(rows, config.DEVICE_ACTIVE_WATTS, retries=True)
    saving = lambda t: {k: pct(base[k] - t[k], base[k]) for k in base}

    # Device power at which routing locally stops saving energy on this prompt mix
    local_secs = sum(lat_local)
    breakeven_w = round(metrics.CLOUD_WH_PER_PROMPT * len(local_rows) * 3600 / local_secs) if local_secs else None
    sens = {w: pct(base["wh"] - footprint(rows, w)["wh"], base["wh"]) for w in (10, 25, 60, 150)}

    return {
        "n": n, "local_model": rows[0].get("local_model", config.LOCAL_MODEL),
        "cloud_model": rows[0].get("cloud_model", config.CLOUD_MODEL), "judge_model": rows[0].get("judge_model"),
        "assumptions": {"device_active_watts": config.DEVICE_ACTIVE_WATTS, "grid_gco2_per_kwh": config.GRID_GCO2_PER_KWH,
                        "cloud_per_prompt": metrics.cloud_footprint()},
        "routing": {"accuracy_pct": pct(len(hit), n), "correct": len(hit), "confusion": conf,
                    "local_share_pct": pct(len(local_rows), n),
                    "misses": [{"prompt": r["prompt"][:90], "expected": r["expected"], "decision": r["decision"],
                                "task": r["task"], "complexity": r["complexity"]} for r in rows if r not in hit]},
        "quality": {"judged": len(judged),
                    "routed_local": {"n": len(rl), "acceptable_pct": acc(rl), "mean_score": mean_score(rl)},
                    "routed_cloud": {"n": len(rc), "local_acceptable_pct": acc(rc), "mean_score": mean_score(rc)},
                    "all_local_acceptable_pct": acc(judged),
                    "weak_local_answers": [{"prompt": r["prompt"][:90], "score": r["judge_score"], "why": r["judge_reason"]}
                                           for r in rl if not r["local_acceptable"]]},
        "latency_s": {"local_median_routed_local": round(statistics.median(lat_local), 2) if lat_local else None,
                      "local_p90_routed_local": p90(lat_local),
                      "cloud_median_same_prompts": round(statistics.median(lat_cloud_same), 2) if lat_cloud_same else None,
                      "local_tokens_per_s_median": round(statistics.median(tps), 1) if tps else None},
        "energy": {"all_cloud": {k: round(v, 3) for k, v in base.items()},
                   "greenroute": {k: round(v, 3) for k, v in gr.items()},
                   "greenroute_with_retries": {k: round(v, 3) for k, v in gr_retry.items()},
                   "saving_pct": saving(gr), "saving_with_retries_pct": saving(gr_retry),
                   "breakeven_device_watts": breakeven_w, "energy_saving_pct_by_watts": sens},
    }


def markdown(s):
    e, q, r, l = s["energy"], s["quality"], s["routing"], s["latency_s"]
    lines = [
        f"# Benchmark summary ({s['n']} prompts, local `{s['local_model']}`, cloud `{s['cloud_model']}`, "
        f"judge `{s['judge_model']}`)", "",
        "## Routing", "",
        "| Metric | Value |", "|---|---|",
        f"| Agreement with hand labels | {r['correct']}/{s['n']} ({r['accuracy_pct']}%) |",
        f"| Routed on-device | {r['local_share_pct']}% |",
        f"| Labelled local, routed cloud | {r['confusion']['local->cloud']} |",
        f"| Labelled cloud, routed local | {r['confusion']['cloud->local']} |", "",
        "## Quality of the local model's answers (judged against the cloud answer)", "",
        "| Group | Prompts | Local answer acceptable | Mean score (1-5) |", "|---|---|---|---|",
        f"| Router sent on-device | {q['routed_local']['n']} | {q['routed_local']['acceptable_pct']}% | {q['routed_local']['mean_score']} |",
        f"| Router sent to cloud (local answer generated anyway) | {q['routed_cloud']['n']} | "
        f"{q['routed_cloud']['local_acceptable_pct']}% | {q['routed_cloud']['mean_score']} |", "",
        "## Latency on this laptop", "",
        "| Metric | Seconds |", "|---|---|",
        f"| Local, median (prompts routed on-device) | {l['local_median_routed_local']} |",
        f"| Local, 90th percentile | {l['local_p90_routed_local']} |",
        f"| Cloud, median (same prompts) | {l['cloud_median_same_prompts']} |",
        f"| Local generation speed, median | {l['local_tokens_per_s_median']} tokens/s |", "",
        f"## Estimated footprint ({s['assumptions']['device_active_watts']:g} W device, "
        f"{s['assumptions']['grid_gco2_per_kwh']:g} gCO2e/kWh grid)", "",
        "| Scenario | Energy (Wh) | Water (mL) | CO2e (g) |", "|---|---|---|---|",
    ]
    for name, key in [("All cloud", "all_cloud"), ("GreenRoute", "greenroute"),
                      ("GreenRoute + re-asking weak local answers in the cloud", "greenroute_with_retries")]:
        t = e[key]
        lines.append(f"| {name} | {t['wh']} | {t['water_ml']} | {t['gco2e']} |")
    lines += ["", f"Saving vs all-cloud: energy {e['saving_pct']['wh']}%, water {e['saving_pct']['water_ml']}%, "
                  f"CO2e {e['saving_pct']['gco2e']}% (with retries: {e['saving_with_retries_pct']['wh']}% / "
                  f"{e['saving_with_retries_pct']['water_ml']}% / {e['saving_with_retries_pct']['gco2e']}%).", "",
              f"Break-even device power: routing locally saves energy below ~{e['breakeven_device_watts']} W "
              "of extra draw while generating, on this prompt mix.", "",
              "| Device power while generating | Energy saving vs all-cloud |", "|---|---|"]
    lines += [f"| {w} W | {v}% |" for w, v in e["energy_saving_pct_by_watts"].items()]
    lines += ["", "## Routing misses", ""] + [f"- expected {m['expected']}, routed {m['decision']} "
                                              f"({m['task']}, {m['complexity']}): {m['prompt']}" for m in r["misses"]]
    lines += ["", "## Weak local answers the router let through", ""] + [
        f"- score {w['score']}: {w['prompt']} - {w['why']}" for w in q["weak_local_answers"]]
    return "\n".join(lines) + "\n"


def charts(rows, s):
    import logging
    import matplotlib
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11,
                         "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                         "text.color": INK, "axes.spines.top": False, "axes.spines.right": False})
    os.makedirs(IMAGES, exist_ok=True)

    # 1. Footprint: small multiples (one measure per panel, each with its own axis)
    e = s["energy"]
    names = ["All cloud", "GreenRoute", "GreenRoute +\nre-asks"]
    keys = ["all_cloud", "greenroute", "greenroute_with_retries"]
    colors = [BLUE, AQUA, ORANGE]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), dpi=200)
    for ax, (k, title, unit, fmt) in zip(axes, [("wh", "Energy", "Wh", "{:.1f}"),
                                                ("water_ml", "Water", "mL", "{:.1f}"),
                                                ("gco2e", "CO₂e", "g", "{:.2f}")]):
        vals = [e[x][k] for x in keys]
        ax.barh(names, vals, color=colors, height=0.55, edgecolor="white", linewidth=2)
        ax.invert_yaxis()
        ax.set_title(f"{title} ({unit})", loc="left", fontsize=12, fontweight="bold", color=INK)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.02, i, fmt.format(v), va="center", fontsize=10, color=INK)
        ax.set_xlim(0, max(vals) * 1.25)
        if ax is not axes[0]:
            ax.set_yticklabels([])
    fig.suptitle(f"Estimated footprint of {s['n']} prompts", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, -0.04, f"Cloud: Google's median Gemini prompt (0.24 Wh, 0.26 mL, 0.03 g). Local: "
             f"{s['assumptions']['device_active_watts']:g} W × measured time, {s['assumptions']['grid_gco2_per_kwh']:g} gCO₂e/kWh. "
             "'Re-asks' adds a cloud call for every weak local answer.", fontsize=8.5, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES, "footprint.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # 2. Where the line sits: complexity vs judged quality of the local answer
    judged = [r for r in rows if "judge_score" in r]
    cap = 0.35
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=200)
    for decision, color, label in [("local", AQUA, "Router: on-device"), ("cloud", BLUE, "Router: cloud")]:
        pts = [r for r in judged if r["decision"] == decision]
        jit = [((r["id"] * 37) % 11 - 5) * 0.03 for r in pts]  # deterministic jitter
        ax.scatter([r["complexity"] for r in pts], [r["judge_score"] + j for r, j in zip(pts, jit)],
                   s=70, color=color, edgecolor="white", linewidth=1.5, label=label, zorder=3)
    ax.axvline(cap, color=INK2, linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(cap + 0.01, 0.62, f"llama3.2:1b limit ({cap})", color=INK2, fontsize=9)
    ax.axhspan(0.4, 2.5, color="#f0efec", zorder=0)
    ax.text(0.99, 0.62, "not acceptable (score < 3)", ha="right", color=INK2, fontsize=9)
    ax.set_xlim(0, 1.03); ax.set_ylim(0.4, 5.6)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Prompt complexity (router's score)")
    ax.set_ylabel("Local answer quality (judge, 1–5)")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.set_title("The local model's answers get worse as complexity rises", loc="left", fontsize=13,
                 fontweight="bold", pad=30)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=10, borderaxespad=0.2,
              handletextpad=0.3, columnspacing=1.5)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES, "quality_vs_complexity.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    path = os.path.join(RESULTS, "results.jsonl")
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    s = summarize(rows)
    with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    md = markdown(s)
    with open(os.path.join(RESULTS, "summary.md"), "w", encoding="utf-8") as f:
        f.write(md)
    charts(rows, s)
    print(md)


if __name__ == "__main__":
    main()
