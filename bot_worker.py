import asyncio
import os
import sys
from playwright.async_api import async_playwright


async def launch_bot(bot_id, meet_url):
    """Launches an optimized, resilient headless instance with an obscured footprint"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--mute-audio",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",  # Disables core automation flags
            ],
        )

        # Build a complete consumer profile context
        context = await browser.new_context(
            permissions=["microphone", "camera"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York",
        )

        page = await context.new_page()

        # Stealth Patch: Prevent scripts from seeing that this browser is automated
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print(f"[Bot {bot_id}] Routing to network stream target...")
            # Navigate and wait until the DOM structure resolves safely
            await page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)

            # Let async scripts finish stabilizing
            await page.wait_for_timeout(5000)

            # Check what page we are actually on
            current_title = await page.title()
            print(f"[Bot {bot_id}] Currently on page: '{current_title}'")

            # Dismiss interstitial security panels or cookie preferences if visible
            try:
                consent_buttons = page.locator(
                    "button:has-text('Accept'), button:has-text('Got it'), button:has-text('I agree')"
                )
                if await consent_buttons.first.is_visible(timeout=2000):
                    await consent_buttons.first.click()
            except:
                pass

            # --- STEP 1: IDENTITY FIELDS ---
            name_selector = "input[aria-label='Your name'], input[placeholder='Your name'], input[type='text']"
            input_element = page.locator(name_selector).first

            # Wait for element presence in the DOM layout
            await input_element.wait_for(state="attached", timeout=20000)

            # Inject character variables directly into the document object model element properties
            await input_element.evaluate(
                f"(el) => {{ el.value = 'CloudUser_{bot_id}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}"
            )
            print(f"[Bot {bot_id}] Assigned variable identity matching.")

            # --- STEP 2: RECRUIT ENTRY ---
            join_button = page.locator(
                "button:has-text('Join'), button:has-text('Ask to join'), button:has-text('Join now')"
            ).first

            await join_button.wait_for(state="attached", timeout=10000)
            await join_button.click(force=True)
            print(f"[Bot {bot_id}] Sent connection/handshake payload.")

            # Hold thread active
            await asyncio.sleep(900)

        except Exception as e:
            # Diagnostics: Capture the actual page title upon failure to trace redirections
            try:
                err_title = await page.title()
                print(
                    f"[Bot {bot_id}] Failed on page: '{err_title}'. Error detail: {e}"
                )
            except:
                print(f"[Bot {bot_id}] Exception encountered: {e}")
        finally:
            await context.close()
            await browser.close()


async def main():
    meet_url = os.environ.get("MEET_URL")
    batch_num = int(os.environ.get("BATCH_NUM", 0))

    if not meet_url:
        print("[CRITICAL] Environment configuration execution missing MEET_URL link.")
        sys.exit(1)

    start_id = batch_num * 10
    print(
        f"[*] Initializing Container Node Batch. Managing range: [{start_id} to {start_id + 9}]"
    )

    tasks = []
    for i in range(10):
        bot_id = start_id + i
        tasks.append(launch_bot(bot_id, meet_url))
        await asyncio.sleep(4)  # 4-second stagger window to flatten resource spikes

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
