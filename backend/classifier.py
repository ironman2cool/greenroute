"""Rules + heuristics prompt classifier (no ML, no network, runs in well under 1 ms).

classify(prompt) -> Classification with:
  task        one of TASKS (what kind of request this is)
  complexity  0..1, how demanding the request is for a model
  confidence  0..1, how sure the rules are about `task`
  signals     human-readable evidence, shown in the UI's "why" panel
"""
import re
from dataclasses import dataclass, field, asdict

# task -> (label, base complexity, default expected output tokens)
TASKS = {
    "chat":      ("Small talk",         0.05,   40),
    "qa":        ("Q&A",                0.15,  150),
    "classify":  ("Classification",     0.15,   30),
    "rewrite":   ("Rewriting",          0.20,  None),  # None = proportional to input
    "summarize": ("Summarization",      0.20,  None),
    "translate": ("Translation",        0.25,  None),
    "math":      ("Math",               0.25,  150),
    "creative":  ("Creative writing",   0.30,  250),
    "code":      ("Code",               0.45,  350),
    "analysis":  ("Analysis",           0.55,  600),
    "long_form": ("Long-form writing",  0.70, 1200),
    "image":     ("Image generation",   1.00,    0),
    "unknown":   ("Unclassified",       0.35,  300),
}


def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


IMAGE = [
    _rx(r"\b(generate|create|draw|make|design|render|paint|sketch|produce)\b[^.?!\n]{0,40}?"
        r"\b(image|picture|photo|photograph|logo|illustration|drawing|artwork|icon|poster|wallpaper|portrait|painting)s?\b"),
    _rx(r"\b(dall-?e|midjourney|stable diffusion)\b"),
]
# Pasted code is a strong signal wherever it appears; code *words* only count in the instruction.
CODE_STRUCT = [_rx(r"```"), re.compile(r"^\s*(def |import |from \w+ import|public |#include|SELECT |const |let )",
                                       re.IGNORECASE | re.MULTILINE)]
CODE_WORDS = [
    _rx(r"\b(python|javascript|typescript|java|c\+\+|c#|rust|golang|kotlin|swift|php|ruby|sql|bash|powershell|html|css|regex|react|node\.?js|django|flask|fastapi)\b"),
    _rx(r"\b(function|class|method|script|program|algorithm|unit tests?|stack ?trace|compile|refactor|debug|endpoint|code)\b"),
]
CODE_SMALL = _rx(r"\b(simple|small|short|one-?liner|snippet|reverse a string|hello world|fizzbuzz)\b")
CODE_BIG = _rx(r"\b(app|application|full[- ]stack|system|architecture|microservices?|scalable|production|framework|entire|complete)\b")
LONG_FORM = _rx(r"\b(essay|report|article|blog post|white ?paper|thesis|chapter|business plan|proposal|cover letter|"
                r"research paper|literature review|documentation|speech|newsletter|press release|curriculum|syllabus)\b")
CREATIVE = _rx(r"\b(poem|haiku|story|short story|song|lyrics|limerick|joke|slogan|tagline|riddle|toast|rhyme)\b")
CREATIVE_TINY = _rx(r"\b(haiku|joke|slogan|tagline|riddle|limerick|rhyme)\b")
ANALYSIS = _rx(r"\b(compare|comparison|contrast|analy[sz]e|analysis|evaluate|assess|pros and cons|trade-?offs?|"
               r"advantages and disadvantages|strategy|critique|implications|root cause|forecast|recommendations?)\b")
MATH = _rx(r"\b(calculate|compute|solve|equation|integral|derivative|probability|percent(age)?|square root|"
           r"multiply|divide|average of|sum of|how many|convert \d)\b")
MATH_EXPR = _rx(r"\d+(\.\d+)?\s*[-+*/x×^%]\s*\d+|\d+(\.\d+)?\s*%\s*of\s*\d+")
MATH_HARD = _rx(r"\b(prove|proof|derive|integral|differential equation|eigen\w*|theorem|optimi[sz]ation)\b")
SUMMARIZE = _rx(r"\b(summari[sz]e|summary|tl;?dr|key points|main points|condense|recap|gist)\b")
TRANSLATE = _rx(r"\btranslat(e|ion)\b|\bhow do you say\b")
REWRITE = _rx(r"\b(rewrite|rephrase|paraphrase|proofread|reword|fix (the |my |this )?(grammar|spelling|typos?)|"
              r"correct (the |my |this )?(grammar|sentence|spelling)|make (this|it) (more |less )?"
              r"(formal|polite|concise|friendly|professional|casual|shorter|clearer))\b")
CLASSIFY = _rx(r"\b(classify|categori[sz]e|sentiment|is this (email |message |review |text )?(spam|positive|negative|neutral)|"
               r"extract (the |all )?\w+|which category|detect the (language|intent)|label (this|these|each))\b")
QUESTION = _rx(r"^\s*(what|who|whom|when|where|which|why|how|is|are|was|were|do|does|did|can|could|should|would|"
               r"will|define|explain|describe|tell me|list|name|give me)\b")
CHAT = _rx(r"^\s*(hi|hello|hey|yo|thanks|thank you|good (morning|afternoon|evening|night)|how are you|what's up)\b")
DETAIL = _rx(r"\b(detailed|in detail|comprehensive|thorough(ly)?|in[- ]depth|exhaustive|complete guide|step[- ]by[- ]step|elaborate)\b")
BRIEF = _rx(r"\b(brief(ly)?|short|one (word|sentence|line)|in a (word|sentence)|concise(ly)?|quick(ly)?|tl;?dr|yes or no)\b")
N_WORDS = _rx(r"\b(\d{2,5})[- ]?words?\b")
N_PARAS = _rx(r"\b(\d{1,2}|two|three|four|five|six|seven|eight|nine|ten)[- ]paragraphs?\b")
N_PAGES = _rx(r"\b(\d{1,2}|two|three|four|five)[- ]pages?\b")
QUOTED = re.compile(r'"[^"\n]{12,}"|“[^”\n]{12,}”')
_NUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


@dataclass
class Classification:
    task: str
    label: str
    complexity: float
    confidence: float
    input_tokens: int
    est_output_tokens: int
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    """~4 characters per token for English; good enough for routing thresholds."""
    return max(1, round(len(text) / 4))


def _num(s: str) -> int:
    return int(s) if s.isdigit() else _NUM.get(s.lower(), 1)


def _first(patterns, text):
    for p in patterns:
        m = p.search(text)
        if m:
            return m
    return None


def classify(prompt: str) -> Classification:
    text = prompt.strip()
    # Instructions usually sit in the first lines; pasted material follows. Match keywords there
    # so a pasted article that happens to mention "code" doesn't change the task.
    # Quoted material is content to work on, not instructions: in 'Make this polite: "Send me the
    # report"' the word "report" must not make this a report-writing task.
    head = QUOTED.sub(' "..." ', text[:400])
    tokens = estimate_tokens(text)
    signals: list[str] = []
    matched: dict[str, float] = {}  # task -> confidence

    def hit(task: str, m: re.Match | None, conf: float = 0.9) -> None:
        if m:
            matched[task] = max(matched.get(task, 0), conf)
            signals.append(f"{TASKS[task][0]}: '{m.group(0).strip()[:30]}'")

    hit("image", _first(IMAGE, head), 0.95)
    hit("code", _first(CODE_STRUCT, text[:2000]) or _first(CODE_WORDS, head), 0.85)
    hit("long_form", LONG_FORM.search(head))
    hit("creative", CREATIVE.search(head))
    hit("analysis", ANALYSIS.search(head), 0.8)
    hit("math", MATH.search(head) or MATH_EXPR.search(head), 0.8)
    hit("summarize", SUMMARIZE.search(head))
    hit("translate", TRANSLATE.search(head))
    hit("rewrite", REWRITE.search(head))
    hit("classify", CLASSIFY.search(head), 0.85)
    hit("chat", CHAT.search(head) if tokens < 15 else None, 0.8)
    if QUESTION.search(head) or head.rstrip().endswith("?"):
        matched.setdefault("qa", 0.6)
        if not any(s.startswith("Q&A") for s in signals):
            signals.append("Q&A: phrased as a question")

    if "image" in matched:
        task = "image"
    elif matched:
        # When several rules fire, the most demanding task wins (safer to over- than under-estimate).
        task = max(matched, key=lambda t: (TASKS[t][1], matched[t]))
    else:
        task = "unknown"
    label, base, default_out = TASKS[task]
    confidence = matched.get(task, 0.2)
    complexity = base

    # Task-specific adjustments
    if task == "code":
        if CODE_SMALL.search(head):
            complexity -= 0.15; signals.append("small code task")
        if CODE_BIG.search(head):
            complexity += 0.25; signals.append("large code scope")
    if task == "creative" and CREATIVE_TINY.search(head):
        complexity -= 0.1
    if task == "math":
        if MATH_HARD.search(head):
            complexity = 0.75; signals.append("proof/advanced math")
        elif MATH_EXPR.search(head) and tokens < 30:
            complexity = 0.1; signals.append("plain arithmetic")

    # Expected output length
    if default_out is None:  # proportional tasks: rewrite/translate/summarize
        default_out = round(tokens * (0.3 if task == "summarize" else 1.2)) + 40
    est_out = default_out
    if m := N_WORDS.search(head):
        est_out = round(int(m.group(1)) * 1.33); signals.append(f"asks for {m.group(1)} words")
    elif m := N_PARAS.search(head):
        est_out = _num(m.group(1)) * 110; signals.append(f"asks for {m.group(1)} paragraphs")
    elif m := N_PAGES.search(head):
        est_out = _num(m.group(1)) * 600; signals.append(f"asks for {m.group(1)} pages")
    if m := DETAIL.search(head):
        complexity += 0.15; est_out = max(est_out, 800); signals.append(f"detail cue '{m.group(0)}'")
    elif m := BRIEF.search(head):
        complexity -= 0.05; est_out = min(est_out, 80); signals.append(f"brevity cue '{m.group(0)}'")

    # Size terms: long inputs and long outputs both cost more
    complexity += min(0.3, tokens / 3000 * 0.3)
    complexity += min(0.3, max(0, est_out - 200) / 1500 * 0.3)
    if tokens > 200:
        signals.append(f"~{tokens:,} input tokens")
    if est_out > 400:
        signals.append(f"~{est_out:,} output tokens expected")
    if task == "image":
        complexity = 1.0

    return Classification(
        task=task, label=label,
        complexity=round(min(1.0, max(0.0, complexity)), 2),
        confidence=round(confidence, 2),
        input_tokens=tokens, est_output_tokens=est_out,
        signals=signals[:6],
    )
