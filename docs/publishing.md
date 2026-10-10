# Publishing GreenRoute

The repo is the evidence, the article is the story, and a short post points people to both. The
article was drafted with AI assistance, so every venue below was chosen because its published
policy **accepts AI-assisted writing that is disclosed and fact-checked**. Policies were checked on
2026-10-10; re-read them before submitting, they change.

**Before you publish anywhere:** read the article end to end, change anything that doesn't sound
like you, and keep the disclosure paragraph near the top. Every venue below requires or rewards
it, and "I can vouch for every number" is exactly what they ask for.

## Where to publish, in order

| # | Venue | Audience | AI policy (checked 2026-10-10) | Why it's here |
|---|---|---|---|---|
| 1 | **[DEV (dev.to)](https://dev.to)** | Developers | Allowed with disclosure (a note anywhere in the post, or the `#abotwrotethis` tag) and fact-checking; no promotion of a business ([guidelines](https://dev.to/guidelines-for-ai-assisted-articles-on-dev)) | Publish here first. Markdown-native; `article.md` already has DEV front matter. |
| 2 | **[Towards AI](https://towardsai.com/contribute/)** (Medium publication) | AI/ML practitioners | Follows Medium's rules: disclose AI-generated text **within the first two paragraphs**; check all AI output | An edited publication: being accepted gives you a "published in Towards AI" credit for your CV. LLM applications and evaluation are core topics. |
| 3 | **[Hashnode](https://hashnode.com)** (your own blog) | Developers | "AI-generated content is permitted, but you must review and take responsibility for everything you publish" ([code of conduct](https://hashnode.com/code-of-conduct)) | Your own blog, optionally on your own domain, so nobody can reject it. Set its canonical URL to the DEV post. |
| 4 | **[Green Software Foundation](https://github.com/Green-Software-Foundation/writers)** articles | Green-software / climate-tech professionals | No AI rule published; wants evidence-based, non-promotional pieces of 500–1,200 words | The best climate-tech audience. Use `article-gsf.md` (the short version), disclose AI use in your pitch, and ask first. |
| 5 | **[HackerNoon](https://hackernoon.com)** (optional) | Tech general | Reviews disclosed AI-assisted stories but says it "neither accept[s] nor encourage[s] the use of AI to generate text" and runs AI detection ([policy](https://hackernoon.com/the-right-way-to-use-ai-on-hackernoon)) | Large audience, but the least likely to accept. Only try it after you've rewritten the article in your own words. |

**Communities to share the link in** (not publications, so no editorial rejection): Hacker News
*Show HN*, Reddit r/LocalLLaMA and r/ClimateTech, the
[ClimateAction.tech](https://climateaction.tech) Slack, and LinkedIn.

**Skip these:** Towards Data Science says it publishes "human authors only" and rejects posts
"written in whole or in part by AI tools". The EGU climate blogs ban AI-produced writing. Branch
Magazine (ClimateAction.tech) welcomes this topic, but its last open call (Issue 9) closed in April
2025. Watch [its open-call page](https://branch.climateaction.tech/open-call-for-contributions/) for the
next one.

## Step by step

### 1. GitHub (do this first; every article links here)

1. Optional but recommended: rename the repo to `greenroute` (*Settings → General → Repository
   name*). GitHub redirects the old URL; then replace `Powered_by_caffeine` in `README.md` and
   `docs/*.md`.
2. *About* box (gear icon): description *"Local-first AI router: answers on-device when it can, in
   the cloud when it must, and shows the energy and water it saved."* Topics: `llm`, `ollama`,
   `gemini`, `green-ai`, `green-software`, `sustainability`, `fastapi`, `llm-router`.
3. Pin the repo on your profile.

### 2. DEV

*Create post* → paste all of `docs/article.md` (front matter included) → preview → change
`published: false` to `true` → publish. Add the tags it suggests (`ai`, `llm`, `sustainability`,
`python`).

### 3. Towards AI

Import the DEV post into Medium (*Import a story* → paste the DEV URL; this sets the canonical
link), keep it as a **draft**, check the disclosure is in the first two paragraphs, then *⋯ →
Submit to publication → Towards AI → Send for review*. If there's no reply in 72 hours, it wasn't
accepted this time; publish it on your own Medium profile instead.

### 4. Hashnode

Create a blog, paste the article, and set *canonical URL* to the DEV post. Optional: connect a
custom domain (for example `yourname.dev`) so it becomes your portfolio blog.

### 5. Green Software Foundation

Post a short pitch in the community discussions, or email news@greensoftware.foundation:

> **Pitch: "Should this prompt leave the device?" — measuring a local-first LLM router**
> I built an open-source router that keeps simple LLM prompts on the user's device and sends only
> demanding ones to the cloud, then benchmarked it on 60 prompts with real models. The piece
> (~1,000 words) covers the routing rules, the energy/water/carbon accounting (net of local device
> power, using Google's published per-prompt figures), and the results, including where local
> doesn't pay off. I used an AI assistant while building the project and drafting the text; I ran
> the benchmark and have checked every figure. Code and data: ⟨repo link⟩. Draft: ⟨link⟩.

### 6. LinkedIn post (~150 words)

> Most AI apps send every request to a data center, even "what's the capital of Australia?".
>
> I built GreenRoute, a router that asks whether a prompt needs to leave your device at all.
> Simple requests go to a small model running locally; demanding ones go to the cloud; every
> answer explains why and estimates the energy and water it saved.
>
> On a 60-prompt benchmark it kept 58% of requests on my laptop, 86% of those local answers were
> judged good enough, and the estimated energy use fell by 48% (water by 58%).
>
> The most interesting part was doing the math honestly: local inference isn't free, and on a
> laptop CPU a 1B model is slower than the cloud. The write-up covers where local wins, where it
> doesn't, and the break-even point.
>
> Article: ⟨link⟩ · Code: ⟨link⟩
>
> #AI #LLM #Sustainability #GreenSoftware #Python

Attach `docs/images/footprint.png` as the image.

## The CV entry

**GreenRoute — local-first LLM router** · Python, FastAPI, Ollama, Gemini API · ⟨repo link⟩

- Built a local-first LLM router (Python, FastAPI) that classifies each prompt and runs seven device and complexity checks to choose between an on-device model (Ollama, Llama 3.2 1B) and the cloud (Gemini), with a streaming web UI that explains every routing decision.
- Benchmarked it on 60 hand-labelled prompts with real models and an LLM judge: 95% routing agreement; 58% of requests kept on-device, with 86% of those answers judged acceptable vs 17% for the prompts it sent to the cloud.
- Designed a cited energy/water/CO₂e estimator that nets out local device power (est. 48% less energy and 58% less water than all-cloud; break-even at ~136 W); 63 automated tests and CI.
- Wrote and published a technical write-up on the method and results (⟨venue⟩, ⟨link⟩).
