import pytest

from classifier import classify, estimate_tokens


@pytest.mark.parametrize("prompt, task", [
    ("What's the capital of Japan?", "qa"),
    ("hello", "chat"),
    ("Summarize: the meeting moved to Friday.", "summarize"),
    ("Translate good morning to French", "translate"),
    ("Fix the grammar: me and him goes to school", "rewrite"),
    ("Is this review positive or negative: cold food, slow service.", "classify"),
    ("What is 15% of 80?", "math"),
    ("Write a haiku about rain", "creative"),
    ("Write a python function to reverse a string", "code"),
    ("Compare REST and GraphQL for a mobile backend", "analysis"),
    ("Write an essay on climate policy", "long_form"),
    ("Generate an image of a cat in a raincoat", "image"),
    ("Draw me a logo for a coffee shop", "image"),
    ("Bananas", "unknown"),
])
def test_task_type(prompt, task):
    assert classify(prompt).task == task


def test_simple_prompts_are_low_complexity():
    for p in ["What's the capital of Japan?", "hello", "Translate thank you to Spanish", "What is 12 * 34?"]:
        assert classify(p).complexity <= 0.35, p


def test_demanding_prompts_are_high_complexity():
    for p in ["Write a detailed 5-paragraph essay on renewable energy policy.",
              "Write a 1500-word blog post about remote work",
              "Prove that the square root of 2 is irrational",
              "Design a scalable microservices architecture for an e-commerce app in Java"]:
        assert classify(p).complexity >= 0.6, p


def test_length_cues_drive_expected_output():
    assert classify("Write a 1500-word blog post").est_output_tokens == round(1500 * 1.33)
    assert classify("Write a 3-paragraph summary of the plot").est_output_tokens == 330
    assert classify("In one sentence, what is DNS?").est_output_tokens <= 80


def test_detail_cue_raises_complexity():
    plain, detailed = classify("Explain photosynthesis"), classify("Explain photosynthesis in detail")
    assert detailed.complexity > plain.complexity


def test_long_input_raises_complexity_and_is_reported():
    doc = "word " * 3000
    c = classify("Summarize this: " + doc)
    assert c.task == "summarize"
    assert c.input_tokens == estimate_tokens("Summarize this: " + doc)
    assert c.complexity > classify("Summarize this: short note").complexity
    assert any("input tokens" in s for s in c.signals)


def test_keywords_in_pasted_text_do_not_change_task():
    # The instruction is a summary; the pasted text later mentions an essay and code.
    prompt = "Summarize the following email.\n\n" + ("filler text " * 60) + "Also, write an essay and debug the code."
    assert classify(prompt).task == "summarize"


def test_keywords_inside_quotes_are_content_not_instructions():
    assert classify('Rewrite this to sound more polite: "Send me the report now."').task == "rewrite"
    assert classify('Fix the grammar: "I write a essay about code yesterday."').task == "rewrite"


def test_signals_explain_the_decision():
    c = classify("Write a detailed 5-paragraph essay on renewable energy policy.")
    assert any("essay" in s for s in c.signals)
    assert any("paragraph" in s for s in c.signals)
    assert c.to_dict()["label"] == "Long-form writing"
