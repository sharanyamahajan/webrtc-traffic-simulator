import asyncio
import os
import sys
from playwright.async_api import async_playwright


async def launch_bot(bot_id, meet_url):
    """Launches a single isolated headless browser instance"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",  # Auto-bypass camera/mic alerts
                "--mute-audio",  # Don't decode audio (saves massive cloud CPU)
                "--disable-gpu",  # Serverless instances don't have hardware GPUs
            ],
        )

        # Open an isolated incognito browser context
        context = await browser.new_context(
            permissions=["microphone", "camera"]
        )
        page = await context.new_page()

        try:
            print(f"[Bot {bot_id}] Navigating to URL...")
            await page.goto(meet_url, timeout=45000)

            # Block heavy image assets to optimize cloud network bandwidth
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media", "font"]
                    else route.continue_()
                ),
            )

            # Wait for the entry name text input field to render
            await page.wait_for_selector("input[type='text']", timeout=15000)
            await page.fill("input[type='text']", f"CloudUser_{bot_id}")

            # Click the main submission / entry button
            join_button = page.locator("button:has-text('Join')")
            await join_button.click()
            print(f"[Bot {bot_id}] Successfully connected to session.")

            # Keep the bot alive inside the room for 15 minutes (900 seconds)
            await asyncio.sleep(900)

        except Exception as e:
            print(f"[Bot {bot_id}] Error: {e}")
        finally:
            await context.close()
            await browser.close()


async def main():
    # Grab configuration parameters sent from the GitHub user interface
    meet_url = os.environ.get("MEET_URL")
    batch_num = int(os.environ.get("BATCH_NUM", 0))

    if not meet_url:
        print("Error: MEET_URL environment variable is missing.")
        sys.exit(1)

    # Each cloud runner handles a unique offset block of 10 bots
    start_id = batch_num * 10
    print(
        f"[*] Cloud Machine Initiated. Running Bots {start_id} through {start_id + 9}..."
    )

    # Launch 10 instances concurrently on this specific machine pool, staggered by 2 seconds
    tasks = []
    for i in range(10):
        bot_id = start_id + i
        tasks.append(launch_bot(bot_id, meet_url))
        await asyncio.sleep(2)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
