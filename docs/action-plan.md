# GreenRoute publishing action plan

Follow this top to bottom. Each step says where to go, exactly what to do, and how you know it
worked. Tick the boxes as you go. Total time: about 3–4 hours spread over a week or two.

Files you'll use:
- `docs/article.md`: the article (read and edit this one)
- `docs/publish/dev.md`: the same article with DEV's settings block, ready to paste
- `docs/article-gsf.md`: the short (~1,000-word) version for climate outlets
- `docs/publishing.md`: why each venue was chosen, and each one's AI policy

---

## Phase 0: Prepare (day 1, ~1 hour)

**0.1 Make the article yours.** This matters more than any other step. Every venue below expects
you to stand behind every claim, and interviewers will ask about it.

- [ ] Read `docs/article.md` out loud once, start to finish.
- [ ] Reword any sentence that doesn't sound like you. Add one or two personal details only you
      know: why you entered the hackathon, what your team built in the first 24 hours, what you
      would do differently.
- [ ] Check the numbers against `backend/benchmark/results/summary.md`: 35/60 on-device, 57/60
      agreement, 86% vs 17% acceptable, 48% / 58% / 19% savings, ~136 W break-even.
- [ ] Keep the **AI disclosure** box near the top. Medium and Towards AI require it within the first
      two paragraphs.
- [ ] If you changed `article.md`, make the same edits in `docs/publish/dev.md` (it's the same text
      below its settings block). Or send me the edited file and I'll sync them.

**0.2 Polish the GitHub repo** (github.com/ironman2cool/greenroute)

- [ ] Click the gear icon next to **About** (top right of the repo page).
  - Description: `Local-first AI router: answers on-device when it can, in the cloud when it must, and shows the energy and water it saved.`
  - Topics: `llm` `ollama` `gemini` `green-ai` `green-software` `sustainability` `fastapi` `llm-router`
  - Save.
- [ ] On your profile page, click **Customize your pins** and pin `greenroute`.
- [ ] Open the repo's **Actions** tab and check the latest run is green. The README badge reads from it.

**Done when:** the repo page shows the description, the topics and a green "tests" badge.

---

## Phase 1: DEV, the original copy (day 1, ~30 min)

DEV is where the article is "born". Every other copy points back to it.

1. [ ] Create an account at https://dev.to (signing in with GitHub links your profile to the repo).
2. [ ] Switch to the plain-text editor so the settings block works: profile picture →
       **Settings → Customization → Editor → "Basic markdown"** → Save.
3. [ ] Click **Create Post**. Delete the template text, paste the **entire** contents of
       `docs/publish/dev.md`, including the block between the `---` lines.
4. [ ] If the editor asks for an **AI disclosure level**, choose **AI-assisted**.
5. [ ] Click **Preview**. Check that the cover image, both charts and the screenshots appear.
6. [ ] Click **Publish**. (Or change `published: false` to `published: true` in the settings block,
       then save.)
7. [ ] Copy the article's URL; you'll need it in every later step. Write it here: ______________

**Done when:** the article is live with its images, and the URL works in a private browser window.

---

## Phase 2: Medium + Towards AI (day 2, ~30 min)

Towards AI is an edited publication, so acceptance gives you a "Published in Towards AI" credit.

1. [ ] Create a Medium account (https://medium.com), with your real name and a one-line bio.
2. [ ] Go to https://medium.com/towards-artificial-intelligence and click **Follow**. Towards AI
       asks contributors to follow it before submitting.
3. [ ] Import the DEV article: profile picture → **Stories → Import a story**, or go straight to
       https://medium.com/p/import. Paste your DEV URL and click **Import**. Medium marks the copy
       as originally published on DEV.
4. [ ] In the imported **draft** (don't publish it yet):
   - Check the **AI disclosure** box is still within the first two paragraphs.
   - Check the images came through. If one didn't, drag it in from `docs/images/`.
   - Add up to 5 topics: `Artificial Intelligence`, `LLM`, `Sustainability`, `Green Tech`, `Python`.
   - **Don't** put it behind the paywall. Medium doesn't allow AI-assisted stories in the Partner Program.
5. [ ] Click **⋯ → Submit to publication → Towards AI → Send for review**. (If that option doesn't
       appear, use the form on https://towardsai.com/contribute/ and paste the draft link.)
6. [ ] **Wait 72 hours.**
   - **Accepted:** Towards AI publishes it. Note the URL: ______________
   - **No reply after 72 hours:** treat it as not accepted. Open the draft, click **Publish** to put
     it on your own Medium profile, and optionally email Level Up Coding (Phase 4).

**Done when:** the article is live on Medium, either in Towards AI or on your profile.

---

## Phase 3: Hashnode, your own blog (day 2 or 3, ~20 min)

1. [ ] Sign up at https://hashnode.com and create a blog (for example `akshayrao.hashnode.dev`).
       Optional: connect your own domain under **Blog dashboard → Domain**.
2. [ ] **Write an article** → paste `docs/article.md` (no settings block; Hashnode has its own
       title field). Upload `docs/images/hero.png` as the cover.
3. [ ] In the article settings, turn on **"Are you republishing?"** and paste your **DEV URL** as the
       canonical URL. Search engines then credit DEV as the original.
4. [ ] Tags: `AI`, `LLM`, `Sustainability`, `Python`. Publish.

**Done when:** the Hashnode post is live and its page source shows `rel="canonical"` pointing to DEV.

---

## Phase 4: Pitches (day 3, ~45 min; replies take 1–2 weeks)

Send these together; they're independent. Fill in your links first.

### 4a. Green Software Foundation: the best climate audience

- [ ] Email **news@greensoftware.foundation**, attaching `docs/article-gsf.md` (or a Google Doc link
      to it):

> **Subject:** Article pitch: "Should this prompt leave the device?" Measuring a local-first LLM router
>
> Hi,
>
> I built an open-source router that keeps simple LLM prompts on the user's own device and sends
> only demanding ones to the cloud, then benchmarked it on 60 prompts with real models. On a laptop
> it kept 58% of requests local, the local answers were judged acceptable 86% of the time, and the
> estimated energy use fell 48% against an all-cloud baseline (water 58%). It nets out the device's
> own power use and shows where local stops paying off (~136 W).
>
> The attached ~1,000-word piece covers the routing rules, the energy/water/carbon accounting
> (using Google's published per-prompt figures) and the results, including the caveats.
>
> Transparency: I used an AI assistant while building the project and drafting the text. I ran the
> benchmark and have checked every figure. Code, prompts and raw results are public:
> https://github.com/ironman2cool/greenroute
>
> Would this fit the GSF articles program? Happy to adapt it to your style.
>
> Thanks,
> Akshay Rao

### 4b. Planet Forward: environmental innovation stories

- [ ] Go to https://planetforward.org and find **Contribute / Submit a story**. Submit the full
      article (they take 1,200–2,000 words) with the same transparency note in your message.

### 4c. Level Up Coding: only if Towards AI said no

- [ ] Email **submit@gitconnected.com**:

> **Subject:** Submission: Should this prompt leave your laptop? (local-first LLM router)
>
> Hi, I'd like to submit this story to Level Up Coding: ⟨Medium draft link⟩
> It's a build-and-benchmark write-up of an open-source LLM router that keeps simple prompts
> on-device, with real results on 60 prompts. Note: I used an AI assistant for parts of the build and
> the drafting, disclosed at the top of the story; I've verified all numbers myself.
> Thanks, Akshay Rao

**Done when:** all pitches are sent. Note the date: ______. Follow up once, politely, after 2 weeks.

---

## Phase 5: Spread the word (days 3–5, ~45 min)

Do these **after** the DEV article is live, a day or so apart.

### 5a. LinkedIn post

- [ ] **Start a post**, attach `docs/images/footprint.png`, and paste:

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
> Article: ⟨DEV link⟩ · Code: https://github.com/ironman2cool/greenroute
>
> #AI #LLM #Sustainability #GreenSoftware #Python

- [ ] Optional: also publish the article itself on LinkedIn (**Write article**), adding a line at
      the top: "Originally published on DEV: ⟨link⟩".

### 5b. Hacker News

- [ ] https://news.ycombinator.com/submit, signed in.
  - Title: `Show HN: GreenRoute – a router that keeps simple LLM prompts on your laptop`
  - URL: `https://github.com/ironman2cool/greenroute`
- [ ] Right after posting, add a comment with 3–4 sentences: what it is, the headline result, the
      honest caveat (local is slower on a laptop CPU), and a link to the article. Reply to comments
      for the first few hours.

### 5c. Reddit

- [ ] **r/LocalLLaMA**: a text post titled `I benchmarked routing simple prompts to Llama 3.2 1B
      instead of the cloud: 86% of local answers were fine, 17% of the hard ones were` with the
      results table and both links. Read the subreddit's rules on self-promotion first.
- [ ] **r/ClimateTech**: lead with the energy/water accounting and the break-even point.

### 5d. Climate-tech community

- [ ] Join the ClimateAction.tech Slack (https://climateaction.tech) and share the article in the
      relevant channel with a two-line summary.
- [ ] Bookmark https://branch.climateaction.tech/open-call-for-contributions/ and check monthly. Branch
      is a perfect fit when its next open call opens.

---

## Phase 6: Your CV and profiles (day 5, ~20 min)

- [ ] Add a project entry to your CV:

> **GreenRoute — local-first LLM router** · Python, FastAPI, Ollama, Gemini API · github.com/ironman2cool/greenroute
> - Built a local-first LLM router (Python, FastAPI) that classifies each prompt and runs seven device and complexity checks to choose between an on-device model (Ollama, Llama 3.2 1B) and the cloud (Gemini), with a streaming web UI that explains every routing decision.
> - Benchmarked it on 60 hand-labelled prompts with real models and an LLM judge: 95% routing agreement; 58% of requests kept on-device, with 86% of those answers judged acceptable vs 17% for the prompts it sent to the cloud.
> - Designed a cited energy/water/CO₂e estimator that nets out local device power (est. 48% less energy and 58% less water than all-cloud; break-even at ~136 W); 63 automated tests and CI.
> - Published a technical write-up: ⟨Towards AI or DEV link⟩

- [ ] LinkedIn profile → **Add section → Projects**: add GreenRoute with the repo link. Then add
      the article under **Featured**.
- [ ] Add the DEV/Medium link to your GitHub profile README, if you have one.

---

## Tracker

| Venue | Submitted | Status | Link |
|---|---|---|---|
| DEV | | | |
| Medium / Towards AI | | | |
| Hashnode | | | |
| Green Software Foundation | | | |
| Planet Forward | | | |
| Level Up Coding | | | |
| LinkedIn post | | | |
| Show HN | | | |
| Reddit | | | |

## If something goes wrong

- **An image doesn't show on DEV or Medium:** the images load from GitHub, so check the repo is public
  and the URL opens in a private window. If not, upload the image directly from `docs/images/`.
- **A venue rejects the piece:** that's normal; take it to the next one on the list. If the reason
  given is "AI-generated", rewrite the article further in your own words before trying HackerNoon or
  anywhere else that runs AI detectors.
- **Someone questions a number:** every figure traces back to `backend/benchmark/results/`. Point
  them there; it's one of the strongest things about this project.
- **Someone asks for a live demo:** the app runs locally (`backend/start.bat`). Record a 30-second
  screen capture of the chat and the "Why?" panel, and link it from the README.
