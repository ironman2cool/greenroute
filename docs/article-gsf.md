# Should this prompt leave the device? Measuring a local-first LLM router

*A ~1,000-word version for green-software publications. The full write-up is in `article.md`.*

> **AI disclosure:** I built this project with an AI coding assistant (Claude), which also helped
> draft this article. The benchmark ran on my own laptop, and I have checked every number and
> source against the code and raw results, which are public.

LLM routers usually decide *which* cloud model should answer a request. They rarely ask the
question before that: does the request need to leave the user's device at all? Small models such
as Llama 3.2 1B now answer many everyday requests (quick facts, short rewrites, translations,
classifications) well enough, on hardware people already own.

I built GreenRoute, an open-source router that keeps simple prompts on the device and sends
demanding ones to the cloud, then measured what that is worth: in answer quality, and in energy,
water and carbon.

## How the router decides

A rules-based classifier labels each prompt with a task type and a 0–1 complexity score, using
the input's length, the expected output's length ("1500 words", "in one sentence") and cues such
as "detailed". Seven checks then run in order: task type, device mode, battery, input length,
confidence, complexity against the local model's size, and free memory. The first failing check
sends the request to the cloud and becomes the reason shown to the user. When the rules can't
classify a prompt, it goes to the cloud. Mistakes therefore cost energy rather than answer quality.

## Accounting for both sides

The cloud baseline is Google's published measurement for the median Gemini text prompt: 0.24 Wh,
0.26 mL of water and 0.03 gCO₂e, including idle capacity and cooling
([Google, Aug 2025](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference)).

The local side is not free. GreenRoute estimates it as the device's extra power draw (25 W for a
laptop CPU) multiplied by the measured generation time, with carbon at the 2025 world-average grid
intensity of 458 gCO₂/kWh ([Ember via Our World in Data](https://ourworldindata.org/grapher/carbon-intensity-electricity)).
Local inference uses no data-center cooling water; power-plant water is excluded on both sides.
The saving is the baseline minus the local cost, so it can be negative.

## Results

I hand-labelled 60 everyday prompts (38 "should run locally", 22 "needs the cloud") before
running anything. Then I ran them on an Intel Core i5-1135G7 laptop with 12 GB of RAM and no GPU.
For comparison, the local model answered *every* prompt, and a larger model (Gemma 4 26B) wrote
reference answers and judged each local answer from 1 to 5.

| | Result |
|---|---|
| Kept on-device | 35 of 60 (58%) |
| Agreement with the labels | 57 of 60 (95%); all misses erred toward the cloud |
| Local answers acceptable, prompts kept on-device | 30 of 35 (86%) |
| Local answers acceptable, prompts sent to the cloud | 4 of 23 (17%) |
| Estimated saving vs all-cloud | 48% energy, 58% water, 19% CO₂e |
| With every weak local answer re-asked in the cloud | 39% energy, 50% water, 11% CO₂e |

The quality gap is the key evidence: the router's line falls roughly where the small model's
ability does. The carbon saving is the smallest of the three because Google's figure reflects its
clean-energy purchasing, while the laptop draws from an average grid.

Two findings matter for anyone designing this kind of system:

- **Device power decides the energy case.** On this prompt mix, local inference stops saving
  energy at about 136 W of extra draw while generating. Laptops and Apple-silicon machines are well
  below that. A desktop GPU at 150 W would have used about 6% more energy than the cloud.
- **Local is not faster on a laptop CPU.** The 1B model took a median 4.4 s per answer; a fast
  cloud model answered short prompts in 1–2 s. The case for local is energy, water, privacy and
  offline use, not speed.

## Caveats

Sixty prompts is a small set, labelled by one person; the judge is an LLM that also wrote the
reference answers; and the local power draw is assumed rather than measured. Google's figure is a
median for its own traffic. Everything is public, including the prompts, labels, judge prompt and
every raw answer, so the numbers can be checked or rerun.

## What next

The weakest number is the local power draw. Measuring it with RAPL counters on Linux or
`powermetrics` on macOS would replace the assumption. Grid intensity also changes by the hour, so
a carbon-aware router could make a different call when the grid is running on coal than when it is
running on solar. Finally, the same decision matters even more on phones, where the battery is the
constraint and NPUs make small models cheap.

Code, data and the full write-up: https://github.com/ironman2cool/greenroute
