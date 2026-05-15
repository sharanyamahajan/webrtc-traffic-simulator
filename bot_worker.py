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
            # Navigate and wait for DOM elements to drop structural idle markers
            await page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)

            # --- PRE-CHECK: SELF-HEALING DISMISSALS ---
            # Automatically try to bypass cookie policies or regional consent prompts
            try:
                consent_buttons = page.locator(
                    "button:has-text('Accept'), button:has-text('Got it'), button:has-text('I agree')"
                )
                if await consent_buttons.first.is_visible(timeout=2000):
                    await consent_buttons.first.click()
                    print(f"[Bot {bot_id}] Consent overlay dismissed.")
            except:
                pass  # Move on if no interstitial walls are present

            # --- STEP 1: IDENTITY FIELDS ---
            print(f"[Bot {bot_id}] Locating interactive name assignment fields...")

            # Semantic matching array ranging from exact placeholder names to general definitions
            name_input = page.locator(
                "input[aria-label='Your name'], input[placeholder='Your name'], input[type='text']"
            )

            # Enforce execution patience up to 30 seconds
            await name_input.first.wait_for(state="visible", timeout=30000)
            await name_input.first.fill(f"CloudUser_{bot_id}")
            print(f"[Bot {bot_id}] Assigned variable 'CloudUser_{bot_id}' to input.")

            # --- STEP 2: SESSION SUBMISSION ---
            # Search for submission controls that either contain standard text strings
            join_button = page.locator(
                "button:has-text('Join'), button:has-text('Ask to join'), button:has-text('Join now')"
            )

            await join_button.first.wait_for(state="visible", timeout=10000)
            await join_button.first.click()
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

    # Offset batch logic to ensure 4 distinct containers generate clean sequence blocks
    start_id = batch_num * 10
    print(
        f"[*] Initializing Container Node Batch. Managing range: [{start_id} to {start_id + 9}]"
    )

    # Build and concurrently deploy 10 jobs per runner, staggered to mitigate throttling
    tasks = []
    for i in range(10):
        bot_id = start_id + i
        tasks.append(launch_bot(bot_id, meet_url))
        await asyncio.sleep(3)  # Increased stagger to 3 seconds for connection safety

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
