# Publishing GreenRoute

The repo is the evidence, the article is the story, and a short post points people to both. The
article was drafted with AI assistance, so every venue below was chosen because its published
policy **accepts AI-assisted writing that is disclosed and fact-checked**. Policies were checked on
2026-10-10; re-read them before submitting, they change.

**Before you publish anywhere:** read the article end to end, change anything that doesn't sound
like you, and keep the disclosure paragraph near the top. Every venue below requires or rewards
it, and "I can vouch for every number" is exactly what they ask for.

## Where to publish

### A. Platforms you control (no editor can reject it)

| Venue | AI policy (checked 2026-10-10) | Notes |
|---|---|---|
| **[DEV (dev.to)](https://dev.to)** | Allowed with a disclosure note (or the `#abotwrotethis` tag) and fact-checking; no promoting a business ([guidelines](https://dev.to/guidelines-for-ai-assisted-articles-on-dev)) | **Publish here first** and use it as the original (canonical) copy. `article.md` already has DEV front matter. |
| **[Medium](https://medium.com)** (your own profile) | AI-assisted writing is allowed if disclosed **within the first two paragraphs** (done). Disclosed AI writing gets *General* distribution but not curator *Boost*, and can't go behind the Partner Program paywall. Undisclosed AI writing is limited to your followers ([Medium policy](https://help.medium.com/hc/en-us/articles/22576852947223), as reported by [Plagiarism Today](https://www.plagiarismtoday.com/?p=42690)) | The best-known general blog platform. Use *Import a story* with the DEV URL so it's marked as a copy. Leave it outside the paywall. |
| **[Hashnode](https://hashnode.com)** | "AI-generated content is permitted, but you must review and take responsibility for everything you publish" ([code of conduct](https://hashnode.com/code-of-conduct)) | Your own developer blog, optionally on your own domain. Set its canonical URL to the DEV post. |
| **[Substack](https://substack.com)** | No official AI policy; Substack says it doesn't remove content for being AI-made ([WIRED via eWeek](https://www.eweek.com/news/top-substack-newsletters-use-ai-tech/)) | Good if you want a newsletter for follow-up posts. Keep the disclosure anyway. |
| **LinkedIn article** | No editorial review | Reaches your professional network directly; link back to the DEV post. |

### B. Edited publications that accept disclosed AI-assisted writing

| Venue | AI policy | Notes |
|---|---|---|
| **[Towards AI](https://towardsai.com/contribute/)** (Medium publication) | Follows Medium's rules: disclose in the first two paragraphs, verify all AI output | **Best CV credit.** LLM applications and evaluation are core topics; aim for 850+ words. Submit the Medium draft (see step 3). |

### C. Ask first (no published AI policy, so disclose in your pitch)

| Venue | Audience | Notes |
|---|---|---|
| **[Green Software Foundation](https://github.com/Green-Software-Foundation/writers)** | Green-software / climate-tech professionals | **Best climate audience.** Wants evidence-based, non-promotional pieces of 500–1,200 words: send `article-gsf.md` with the pitch below. |
| **[Planet Forward](https://planetforward.org)** | Environmental innovation (run with George Washington University) | Takes contributor stories of 1,200–2,000 words. Pitch the full article. |
| **[Level Up Coding](https://levelup.gitconnected.com/how-to-get-published-on-gitconnected-dac547ef556b)** (Medium publication) | Large general programming audience | Email submit@gitconnected.com with your Medium draft link; mention the AI disclosure. Decisions take up to a week. |
| **[HackerNoon](https://hackernoon.com)** | General tech | Reviews disclosed AI-assisted stories, but says it "neither accept[s] nor encourage[s] the use of AI to generate text" and runs AI detection ([policy](https://hackernoon.com/the-right-way-to-use-ai-on-hackernoon)). A long shot; only try it after rewriting the article in your own words. |

### D. Skip: these reject AI-written articles

- **Towards Data Science**: "human authors only"; no posts "written in whole or in part by AI tools".
- **DZone**: "articles partially or fully created using AI tools… are not allowed"
  ([guidelines](https://dzone.com/pages/submission-guidelines)).
- **The New Stack**: [won't publish AI-written articles](https://thenewstack.io/why-the-new-stack-wont-give-you-ai-written-articles/).
- **EGU climate blogs**: ban AI-produced writing.
- **freeCodeCamp News**: its style guide reportedly rejects "AI dump" content. I couldn't confirm the
  exact rule, so assume no.

**Watch:** Branch Magazine (ClimateAction.tech) is a perfect climate-tech fit, but its last open
call (Issue 9) closed in April 2025. Check [its open-call page](https://branch.climateaction.tech/open-call-for-contributions/)
for the next one.

**Communities to share the link in** (not publications): Hacker News *Show HN*, Reddit
r/LocalLLaMA and r/ClimateTech, and the [ClimateAction.tech](https://climateaction.tech) Slack.

## Step by step

### 1. GitHub (do this first; every article links here)

1. Rename the repo to `greenroute` (*Settings → General → Repository name*). The links in this
   repo already point to `github.com/ironman2cool/greenroute`, and GitHub redirects the old URL.
2. *About* box (gear icon): description *"Local-first AI router: answers on-device when it can, in
   the cloud when it must, and shows the energy and water it saved."* Topics: `llm`, `ollama`,
   `gemini`, `green-ai`, `green-software`, `sustainability`, `fastapi`, `llm-router`.
3. Pin the repo on your profile.

### 2. DEV

*Create post* → paste all of `docs/article.md` (front matter included) → preview → change
`published: false` to `true` → publish. Add the tags it suggests (`ai`, `llm`, `sustainability`,
`python`).

### 3. Medium and Towards AI

Import the DEV post into Medium (*Import a story* → paste the DEV URL; this sets the canonical
link), keep it as a **draft**, check the disclosure is in the first two paragraphs, then *⋯ →
Submit to publication → Towards AI → Send for review*. If there's no reply in 72 hours, it wasn't
accepted this time; publish it on your own Medium profile instead (outside the paywall).

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
