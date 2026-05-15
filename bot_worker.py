import asyncio
import os
import sys
from playwright.async_api import async_playwright


async def launch_bot(bot_id, meet_url):
    """Launches an optimized, resilient headless instance to join the session"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",  # Auto-bypasses hardware device permissions
                "--use-fake-device-for-media-stream",  # Simulates a fake webcam/mic to satisfy the UI loading
                "--mute-audio",  # Disables incoming audio stream decoding to preserve memory
                "--disable-gpu",  # Drops unnecessary graphical processor loops on servers
            ],
        )

        # Generate a clean, isolated browsing context
        context = await browser.new_context(
            permissions=["microphone", "camera"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        try:
            print(f"[Bot {bot_id}] Routing to network stream target...")
            # Use 'load' to guarantee the DOM tree structure is available
            await page.goto(meet_url, wait_until="load", timeout=60000)

            # Give the page a moment to process media check transitions
            await page.wait_for_timeout(5000)

            # --- STEP 1: IDENTITY FIELDS ---
            print(f"[Bot {bot_id}] Locating interactive name assignment fields...")

            name_selector = "input[aria-label='Your name'], input[placeholder='Your name'], input[type='text']"

            # Wait for the input element to exist in the DOM (ignoring visibility constraints)
            input_element = page.locator(name_selector).first
            await input_element.wait_for(state="attached", timeout=30000)

            # Force fill the element using Javascript evaluation if the CSS visibility flag is hidden
            await input_element.evaluate(
                f"(el) => {{ el.value = 'CloudUser_{bot_id}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}"
            )
            print(
                f"[Bot {bot_id}] Forcefully assigned 'CloudUser_{bot_id}' via DOM injection."
            )

            # --- STEP 2: SESSION SUBMISSION ---
            join_button = page.locator(
                "button:has-text('Join'), button:has-text('Ask to join'), button:has-text('Join now')"
            ).first

            await join_button.wait_for(state="attached", timeout=10000)
            # Force click the button using a programmatic trigger to bypass structural overlays
            await join_button.click(force=True)
            print(f"[Bot {bot_id}] Sent registration/connection payload.")

            # Keep connection active for 15 minutes before cycle teardown
            await asyncio.sleep(900)

        except Exception as e:
            print(f"[Bot {bot_id}] Exception encountered during lifecycle: {e}")
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
        await asyncio.sleep(3)  # Stagger to mitigate API rate drops

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
