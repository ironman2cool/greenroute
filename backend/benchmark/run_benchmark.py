"""Benchmark GreenRoute on 60 labelled prompts with real models.

For every prompt it records:
  - the router's decision (Auto mode) vs the hand label
  - the local model's answer and generation time (Ollama)
  - the cloud model's answer and time (Gemini)
  - a judge's verdict on whether the LOCAL answer is acceptable (Gemini, structured output)

Running the local model on *every* prompt - including the ones the router sends to the cloud -
shows whether the router's line is in the right place.

    python -m benchmark.run_benchmark              # full run (~30 min)
    python -m benchmark.run_benchmark --no-judge   # routing + local latency only, no cloud calls

The cloud reference and the judge default to Gemma 4 26B through the Gemini API: the free tier
allows only 20 requests/day for Gemini 2.5 Flash, while Gemma's free limits cover a full run.
Gemma is also a different model family from the local Llama model, which keeps the judge independent.

Results append to benchmark/results/results.jsonl, so an interrupted run resumes where it stopped.
"""
import argparse
import json
import os
import sys
import time

from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cloud_backend  # noqa: E402
import config  # noqa: E402
import local_backend  # noqa: E402
import router  # noqa: E402
import system_check  # noqa: E402
from app import _prompt_for  # noqa: E402
from benchmark.prompts import PROMPTS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results", "results.jsonl")

JUDGE_SYSTEM = "You are a strict, fair evaluator of AI assistant answers. Judge substance, not style or length."
JUDGE_TEMPLATE = """User request:
<request>
{prompt}
</request>

Reference answer from a large cloud model:
<reference>
{reference}
</reference>

Candidate answer from a small on-device model:
<candidate>
{candidate}
</candidate>

Is the candidate an acceptable answer to the user's request: correct, on-topic and complete enough
that the user would not need to ask again? It does not need to match the reference's length or
wording. Score 1-5 (5 = as good as the reference, 3 = acceptable with minor issues, 2 = noticeably
wrong or incomplete, 1 = wrong or unusable). Set acceptable to true only for scores of 3 or more.

Reply with only a JSON object: {{"score": <1-5>, "acceptable": <true|false>, "reason": "<one sentence>"}}"""


class Verdict(BaseModel):
    score: int
    acceptable: bool
    reason: str


class Throttle:
    """Spaces out Gemini calls to stay under the free tier's requests-per-minute limit."""

    def __init__(self, rpm: float):
        self.gap, self.last = 60 / rpm, 0.0

    def wait(self):
        delay = self.last + self.gap - time.time()
        if delay > 0:
            time.sleep(delay)
        self.last = time.time()


def gemini(throttle: Throttle, fn, *args, **kw):
    """Call the cloud API with throttling. Rate limits wait a minute; transient server errors
    (500/503, common on the free tier) wait 10 s. Up to 5 retries.
    Returns (result, seconds) where seconds times only the successful call, not the waiting."""
    for attempt in range(6):
        throttle.wait()
        try:
            t0 = time.perf_counter()
            return fn(*args, **kw), round(time.perf_counter() - t0, 2)
        except cloud_backend.CloudError as e:
            wait = 65 if "429" in str(e) else 10 if any(c in str(e) for c in ("500", "503")) else None
            if wait is None or attempt == 5:
                raise
            print(f"    {str(e)[:60]} - retrying in {wait} s ({attempt + 1}/5)", flush=True)
            time.sleep(wait)


def load_done() -> dict:
    done = {}
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done[r["id"]] = r
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true", help="skip the cloud answers and quality judging")
    ap.add_argument("--rpm", type=float, default=15, help="max cloud requests per minute")
    ap.add_argument("--cloud-model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--judge-model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--local-max-tokens", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    status = system_check.ollama_status()
    if not status["model_ready"]:
        sys.exit(f"Local model not ready: {status['message']}")
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done()
    throttle = Throttle(args.rpm)

    print(f"Local: {config.LOCAL_MODEL} ({status['model_params_b']}B)  Cloud: {args.cloud_model}  "
          f"Judge: {args.judge_model}  Already done: {len(done)}")
    local_backend.generate("Say OK.", max_tokens=5)  # warm-up so the first timing isn't a cold start

    for i, (category, expected, prompt) in enumerate(PROMPTS[: args.limit]):
        if i in done:
            continue
        status = system_check.ollama_status()
        d = router.decide(prompt, local_status=status, specs=system_check.live_specs())
        c = d.details["classification"]
        row = {"id": i, "category": category, "expected": expected, "prompt": prompt,
               "local_model": config.LOCAL_MODEL, "cloud_model": args.cloud_model, "judge_model": args.judge_model,
               "decision": d.decision, "reason": d.reason, "task": c["task"], "complexity": c["complexity"],
               "input_tokens_est": c["input_tokens"]}

        t0 = time.perf_counter()
        local = local_backend.generate(prompt, max_tokens=args.local_max_tokens)
        row.update(local_s=round(time.perf_counter() - t0, 2), local_answer=local["text"],
                   local_out_tokens=local["output_tokens"])

        if not args.no_judge:
            cloud, cloud_s = gemini(throttle, cloud_backend.generate, _prompt_for(d, prompt), args.cloud_model,
                                    fallback=False)
            row.update(cloud_s=cloud_s, cloud_answer=cloud["text"], cloud_out_tokens=cloud["output_tokens"])
            if category != "image":  # no text answer can satisfy an image request; judged separately
                v, _ = gemini(throttle, cloud_backend.generate,
                           JUDGE_TEMPLATE.format(prompt=prompt, reference=cloud["text"], candidate=local["text"]),
                           args.judge_model, system=JUDGE_SYSTEM, fallback=False,
                           response_mime_type="application/json")
                verdict = Verdict.model_validate_json(v["text"].strip().removeprefix("```json").removesuffix("```"))
                row.update(judge_score=verdict.score, local_acceptable=verdict.acceptable, judge_reason=verdict.reason)

        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        mark = "ok " if d.decision == expected else "MISS"
        q = f"judge {row.get('judge_score', '-')}" if "judge_score" in row else ""
        print(f"[{i + 1:2}/60] {mark} {d.decision:5} (exp {expected:5}) {c['task']:9} {c['complexity']:.2f} "
              f"local {row['local_s']:5.1f}s {q} | {prompt[:50]!r}", flush=True)

    print(f"\nDone. Results: {RESULTS}\nNext: python -m benchmark.summarize")


if __name__ == "__main__":
    main()
