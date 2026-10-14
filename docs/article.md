# Should this prompt leave your laptop?

*Building a local-first AI router, and doing the honest math on what it saves.*

> **AI disclosure:** I built this project with an AI coding assistant (Claude), which also helped draft this article. The benchmark ran on my own laptop, and I have checked every number, source and claim below against the code and the raw results, which are all public.

Every AI feature you use, a chatbot, a writing assistant, a "summarize this" button, sends your request to a data center. Even when the request is "what's the capital of Australia?". Even when a model small enough to run on your laptop would answer it perfectly well.

There's a whole category of tools that route LLM requests: OpenRouter, NotDiamond, Martian and the model routers inside the big cloud platforms. They answer *which* cloud model gives the best quality per dollar. None of them ask the question before that one: **does this request need to leave the device at all?**

I built **GreenRoute** to answer that question for every request, explain its answer, and estimate what it saved. It started as a weekend hackathon prototype; this is the version I rebuilt afterwards, with a real router, real local inference, a benchmark, and numbers I'm willing to defend.

![GreenRoute's chat: a simple question answered on-device, with the reason and the estimated saving](https://raw.githubusercontent.com/ironman2cool/greenroute/main/docs/images/chat.png)

## What it does

GreenRoute is a small Python service (FastAPI) with a web chat in front of it. For every prompt it:

1. **Classifies** the request: what kind of task is it, and how demanding is it?
2. **Checks the device**: how big is the local model, is there memory free, is the battery low?
3. **Routes** it to a local model ([Ollama](https://ollama.com), Llama 3.2 1B on my laptop) or to the cloud (Google Gemini), and **shows why** under the answer.
4. **Estimates the footprint** of that answer against an "everything in the cloud" baseline.

If the local model is missing or crashes halfway through an answer, the request moves to the cloud and the user is told. There is no path that ends in an empty reply.

## The router: boring on purpose

I didn't train a classifier. The router is a set of rules you can read in one sitting, and that was a deliberate choice: every decision has to be explainable in one sentence, and it has to run in well under a millisecond so it never slows the request down.

**Step 1: classify.** Patterns pick a task type (Q&A, summary, rewrite, translation, code, analysis, long-form writing, image generation and a few more). Each type has a base complexity, then the score moves with evidence:

- the input's length (a 3,000-token document is harder than a one-liner),
- the expected output's length ("1500 words", "5 paragraphs", "in one sentence"),
- cues like "detailed", "step by step" or "briefly".

Two lessons from building this. First, keywords should only count in the *instruction*, not in the material you pasted: in `Make this more polite: "Send me the report now."`, the word "report" shouldn't turn the request into report-writing. My first version got exactly that wrong. Second, when several rules fire, the most demanding task wins, so mistakes lean toward the cloud: the expensive direction rather than the wrong-answer direction.

**Step 2: seven checks, in order.** The first one that fails sends the request to the cloud and becomes the reason the user sees:

| Check | Goes to the cloud when… |
|---|---|
| Task type | it's an image request (a local text model can't draw) |
| Device mode | the device is flagged as low-spec |
| Battery | it's under 20% and unplugged |
| Input length | the prompt is over ~1,500 tokens |
| Confidence | the request couldn't be classified |
| Complexity | the score is above the local model's limit |
| Memory | there isn't enough free RAM to load the model |

The complexity limit depends on the local model's size, read from Ollama: 0.35 for a ~1B model, 0.5 for ~3B, 0.6 for ~7B. A bigger local model keeps more work on the device.

Each answer gets a "Why?" panel listing every check, so you can see not just *that* it went to the cloud, but which rule sent it there.

## The honest math

This is the part I most wanted to get right, because "local AI is greener" is easy to say and easy to get wrong.

**The cloud side** comes from Google's own measurement, published in August 2025: the median text prompt to Gemini uses **0.24 Wh** of energy, **0.26 mL** of water and emits **0.03 g CO₂e**, counting the accelerators, the host machines, idle capacity kept for reliability and data-center cooling ([Google Cloud blog](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference), [paper](https://arxiv.org/abs/2508.15734)). That's far lower than the scary estimates that circulated in 2023, and it's the number I use as the baseline.

**The local side** is not free. Your laptop burns electricity while it generates. GreenRoute estimates it as *extra power draw × measured generation time*, with 25 W as the default for a laptop CPU, and carbon from the grid's intensity (458 gCO₂/kWh, the 2025 world average from [Ember via Our World in Data](https://ourworldindata.org/grapher/carbon-intensity-electricity)). Local inference uses no data-center cooling water. Water used by power plants is left out on both sides so the comparison stays like-for-like.

**Savings = cloud baseline − local cost.** If a slow local answer on a power-hungry machine costs more than the cloud would have, the saving shows up as negative. I wanted the tool to be able to say "this one wasn't worth it".

![Methodology section of the app](https://raw.githubusercontent.com/ironman2cool/greenroute/main/docs/images/impact.png)

## Results

I wrote 60 everyday prompts and labelled each one, before running anything, with where it *should* run: "would a ~1B on-device model give an answer good enough that I wouldn't need to ask again?" 38 were labelled local and 22 cloud. Then I ran all 60 through the real system on my laptop (an Intel Core i5-1135G7 laptop: 4 cores, 12 GB of RAM, no discrete GPU) and, for comparison, ran the local model on *every* prompt, including the ones the router sent away. A larger cloud model (Gemma 4 26B through the Gemini API) wrote reference answers and then judged each local answer from 1 to 5.

**Routing.** GreenRoute kept 35 of the 60 prompts on the device (58%) and agreed with my labels on 57 of 60. All three disagreements went the safe way: prompts I'd have kept local (a question about Python's `len()`, a one-line SQL query and a short email to a landlord) went to the cloud. None of the prompts I'd labelled for the cloud were kept local. Some cloud decisions were right for a less flattering reason: a proof, a travel itinerary and a system-design question matched none of my rules, and were sent away by the "can't classify, play it safe" check rather than recognised as hard.

**Quality.** This is the result I care most about. On the 35 prompts the router kept local, the 1B model's answer was judged acceptable 30 times (86%, mean score 4.4 out of 5). On the 23 text prompts it sent to the cloud, the same model's answers were acceptable only 4 times (17%, mean 2.0). The router's line sits roughly where the small model's ability falls off.

The five weak answers it let through are instructive: a grammar fix that left "Me and him" untouched, two translations, a date extraction that dropped "June 3rd", and a TL;DR that changed the reason a project had slipped. For a 1B model, "simple" isn't the same as "safe".

![Local answer quality against the router's complexity score](https://raw.githubusercontent.com/ironman2cool/greenroute/main/docs/images/quality_vs_complexity.png)

**Footprint.** Compared with sending all 60 prompts to the cloud, GreenRoute's estimated footprint was 48% lower in energy (7.5 vs 14.4 Wh), 58% lower in water (6.5 vs 15.6 mL) and 19% lower in CO₂e (1.46 vs 1.80 g). The carbon saving is the smallest because Google's per-prompt figure already reflects its clean-energy purchasing, while my laptop runs on an average grid. If every weak local answer were asked again in the cloud, the savings shrink to 39%, 50% and 11%.

Per prompt these are tiny numbers, about 0.1 Wh saved on average. They matter at volume: for scale, the same saving across a billion prompts a day would be on the order of 100 MWh a day.

The energy result depends heavily on the device. Routing locally stops saving energy at about **136 W** of extra power draw while generating. A laptop CPU (around 25 W) or an Apple-silicon Mac (around 10 W) is far below that; a gaming desktop pushing a GPU at 150 W is not, and would have used about 6% *more* energy than the all-cloud baseline.

![Estimated energy, water and CO2e for the 60 prompts](https://raw.githubusercontent.com/ironman2cool/greenroute/main/docs/images/footprint.png)

**Speed.** On my laptop the 1B model answered the prompts it handled in a median 4.4 seconds (90th percentile 12.8 s), at about 12 tokens per second. The free Gemma 4 endpoint I used for the reference answers took a median 5.8 s on the same prompts, but a fast commercial model is quicker: Gemini 2.5 Flash answered short prompts in about 1–2 seconds in my spot checks. On a laptop CPU, local is not the fast option. Its case is energy, water, privacy and working offline.

**Caveats.** Sixty prompts is a small set, and one person (me) labelled them. The judge is itself an LLM, and it also wrote the reference answers. The local power draw is an assumption (25 W), not a measurement, and Google's figure is a median for its own traffic and models. The prompts, labels, judge prompt and every raw answer are in the repo so anyone can check or rerun them.

## What I'd do next

The decision itself should stay what it is now: a handful of cheap rules that run in under a millisecond and can be explained in one sentence. The work is in making those rules more accurate without making them heavier.

- **A limit per task type, not one for everything.** Today every task shares one complexity limit for a given model size. The benchmark shows the 1B model is reliable at facts and rewording but shaky at translation and extraction. A small table of limits per task type, set from benchmark results, is still just a lookup, and it would have caught several of the weak answers that got through.
- **Tune the limits from feedback instead of by hand.** A thumbs-down button on local answers, together with the judge scores from the benchmark, is enough to nudge each task's limit up or down over time. That's a running count per task type, not a model.
- **A cheap check on the local answer.** Some failures only show up in the output: an answer far shorter than what was asked for, one that repeats itself, or one that drops part of the request. Simple checks on the answer (its length against the request, whether the prompt's key terms appear) could flag a doubtful local answer and quietly retry it in the cloud. The routing decision stays cheap; only the doubtful cases pay for a second call.
- **Fix the rules where they're known to miss.** All three routing misses were short, harmless requests: a question about a Python function, a one-line SQL query and a short email. A "short code question" rule and a "short message" rule would cover them, and a larger labelled prompt set would show the next gaps before users do.
- **A tiny learned scorer, only if the rules stop scaling.** If the rule list grows unwieldy, a logistic regression over the signals the rules already compute (task keywords, input length, requested length, detail cues) would replace hand-picked weights with fitted ones. It's still a weighted sum that runs in microseconds, and its weights still explain each decision.

## Try it

The code is on GitHub: **[ironman2cool/greenroute](https://github.com/ironman2cool/greenroute)**. It runs on Windows, macOS and Linux with a free Gemini key; Ollama is optional. The benchmark, the prompts, the judge prompts and every result are in the repo, so you can check my numbers or run them on your own machine.

If your app sends every request to the cloud by default, it's worth asking how many of them actually need to go.
