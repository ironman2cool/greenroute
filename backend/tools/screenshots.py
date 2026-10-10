"""Capture README/article screenshots by driving the real app in a browser.

    python tools/screenshots.py [--url http://127.0.0.1:8001] [--channel msedge]

Needs a running server (start one with an empty DATA_DIR so the counters start at zero) and
`pip install playwright`. Uses an installed Edge/Chrome via `channel`, so no browser download.
"""
import argparse
import os

from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "images")


def ask(page, text, timeout=180_000):
    page.fill("#prompt", text)
    page.click("#send")
    page.wait_for_function("() => !busy", timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8001")
    ap.add_argument("--channel", default="msedge")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        page = browser.new_page(viewport={"width": 1280, "height": 860}, color_scheme="light", device_scale_factor=2)
        page.goto(args.url)
        page.evaluate("localStorage.setItem('greenroute-local-choice', 'cloud')")  # no offer card in shots
        page.reload()
        page.add_style_tag(content=".reveal{opacity:1!important;transform:none!important;transition:none!important}"
                                   ".msg{animation:none!important} .log{height:auto!important;max-height:none!important}")
        page.wait_for_timeout(1500)

        # 1. A local answer with its "Why?" panel, an image request, then the low-spec flip
        ask(page, "What's the capital of Japan?")
        page.locator("details.why").last.evaluate("d => d.open = true")
        ask(page, "Translate 'thank you very much' into French.")
        page.click("#t-lowspec")
        ask(page, "What's the capital of Japan?")
        page.locator("details.why").last.evaluate("d => d.open = true")
        page.click("#t-lowspec")
        page.locator(".chat").screenshot(path=os.path.join(OUT, "chat.png"))

        # 2. Live route preview while typing a demanding prompt
        page.fill("#prompt", "Write a detailed 1500-word report on the future of urban transport")
        page.dispatch_event("#prompt", "input")
        page.wait_for_function("() => document.querySelector('#preview').textContent.length > 0", timeout=10_000)
        page.locator(".preview").evaluate("n => n.style.paddingBottom = '10px'")
        page.locator("#preview, form.input").first.scroll_into_view_if_needed()
        box_prev, box_form = page.locator("#preview").bounding_box(), page.locator("form.input").bounding_box()
        chat = page.locator(".chat").bounding_box()
        page.screenshot(path=os.path.join(OUT, "preview.png"), clip={
            "x": chat["x"], "y": box_prev["y"] - 8, "width": chat["width"],
            "height": box_form["y"] + box_form["height"] - box_prev["y"] + 8})
        page.fill("#prompt", "")

        # 3. Hero with live counters, and the impact methodology section
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(OUT, "hero.png"))
        page.locator("#impact").screenshot(path=os.path.join(OUT, "impact.png"))
        browser.close()
    print("Saved screenshots to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
