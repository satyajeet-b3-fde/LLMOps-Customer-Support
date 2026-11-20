"""Capture screenshots of the live app for the deployment guide.

Usage: python docs/capture_app_screenshots.py [base_url]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://llmops-cs-api-1260.azurewebsites.net"
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)

    for name, path in [("app-01-home.png", "/"), ("app-02-health.png", "/health")]:
        page.goto(BASE + path, wait_until="networkidle")
        page.screenshot(path=OUT / name)

    page.goto(BASE + "/docs", wait_until="networkidle")
    page.wait_for_selector(".opblock")
    page.screenshot(path=OUT / "app-03-swagger.png")

    # Execute POST /chat inside Swagger UI
    op = page.locator(".opblock-post").first
    op.locator(".opblock-summary").click()
    op.locator("button.try-out__btn").click()
    op.locator("textarea.body-param__text").fill('{\n  "question": "How can I cancel my order?"\n}')
    op.locator("button.execute").click()
    page.wait_for_selector(".live-responses-table .response-col_status", timeout=90000)
    page.wait_for_timeout(500)
    op.locator("textarea.body-param__text").evaluate(
        "e => e.style.setProperty('min-height', '70px', 'important') || e.style.setProperty('height', '70px', 'important')")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    top = op.locator(".opblock-section-request-body").bounding_box()
    resp = op.locator(".live-responses-table").first.bounding_box()
    page.screenshot(
        path=OUT / "app-04-chat.png",
        full_page=True,
        clip={"x": top["x"], "y": top["y"], "width": top["width"],
              "height": resp["y"] + resp["height"] - top["y"]},
    )

    browser.close()

print("saved to", OUT)
