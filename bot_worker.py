import asyncio
import os
import random  # Handles random name selection
import sys
from playwright.async_api import async_playwright

# =====================================================================
# SYSTEM CONFIGURATION: RESIDENTIAL PROXIES PLACEHERE
# =====================================================================
PROXY_POOL = [
    # "http://username:password@your-proxy-provider.com:port",
]

# =====================================================================
# INDIAN NAMES POOL
# =====================================================================
INDIAN_NAMES = [
    "Aarav Sharma",
    "Vivaan Patel",
    "Aditya Mishra",
    "Vihaan Gupta",
    "Arjun Joshi",
    "Sai Reddy",
    "Reyansh Kumar",
    "Aayan Singh",
    "Krishna Murthy",
    "Ishaan Choudhury",
    "Ananya Iyer",
    "Diya Nair",
    "Pari Saxena",
    "Pihu Banerjee",
    "Isha Malhotra",
    "Aadhya Rao",
    "Avani Verma",
    "Saanvi Kulkarni",
    "Ahana Chatterjee",
    "Prisha Shah",
    "Rahul Mehta",
    "Amit Das",
    "Vikram Goel",
    "Sanjay Dutt",
    "Deepak Kapur",
    "Rohan Hegde",
    "Neha Trivedi",
    "Priya Deshmukh",
    "Anjali Kapoor",
    "Sneha Gill",
    "Rohan Sharma",
    "Manish Pandey",
    "Abhishek Bisht",
    "Siddharth Roy",
    "Karan Johar",
    "Divya Khosla",
    "Pooja Bhatt",
    "Kriti Sanon",
    "Riya Sen",
    "Shruti Haasan",
]


async def launch_bot(bot_id, meet_url, proxy_server=None):
    """Launches an isolated instance with stealth masking and custom routing"""
    async with async_playwright() as p:

        browser_args = [
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--mute-audio",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        if proxy_server:
            browser_args.append(f"--proxy-server={proxy_server}")

        browser = await p.chromium.launch(headless=True, args=browser_args)

        context = await browser.new_context(
            permissions=["microphone", "camera"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
        )

        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print(f"[Bot {bot_id}] Routing to network stream target...")
            await page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(6000)

            # --- STEP 1: IDENTITY INPUT (RANDOM INDIAN NAME) ---
            name_selector = "input[aria-label='Your name'], input[placeholder='Your name'], input[type='text']"
            input_element = page.locator(name_selector).first

            await input_element.wait_for(state="attached", timeout=20000)

            # Pick a random name from the pool
            random_name = random.choice(INDIAN_NAMES)

            # Inject the random name into the text box
            await input_element.evaluate(
                f"(el) => {{ el.value = '{random_name}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}"
            )
            print(
                f"[Bot {bot_id}] Assigned identity successfully: {random_name}"
            )
            await page.wait_for_timeout(1000)

            # --- STEP 2: OPEN ENTRY SUBMISSION ---
            join_selectors = [
                "button:has-text('Join now')",
                "button:has-text('Ask to join')",
                "button:has-text('Join')",
                "[jsname='Qx7uId']",
            ]

            target_button = None
            for selector in join_selectors:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    target_button = locator
                    break

            if target_button:
                await target_button.wait_for(state="attached", timeout=25000)
                await target_button.click(force=True)
                print(f"[Bot {bot_id}] Sent connection/handshake payload.")
            else:
                raise Exception(
                    "No active entry submission element discovered."
                )

            # --- STEP 3: THE KEEP-ALIVE LOOP (WHAT WE FIXED) ---
            print(
                f"[Bot {bot_id}] Successfully inside room. Starting keep-alive cycle."
            )

            # Runs a loop for 20 minutes (120 cycles * 10 seconds) to keep the browser alive
            for _ in range(120):
                await page.wait_for_timeout(10000)  # Check in every 10 seconds
                # Small page action to keep the network connection active so GitHub doesn't idle out
                await page.evaluate("window.scrollTo(0, 1);")

        except Exception as e:
            try:
                err_title = await page.title()
                print(
                    f"[Bot {bot_id}] Terminated on page: '{err_title}'. Details: {e}"
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
        print("[CRITICAL] Missing target destination link.")
        sys.exit(1)

    start_id = batch_num * 10
    print(
        f"[*] Initializing Container Node Batch. Range: [{start_id} to {start_id + 9}]"
    )

    tasks = []
    for i in range(10):
        bot_id = start_id + i
        current_proxy = PROXY_POOL[i % len(PROXY_POOL)] if PROXY_POOL else None

        tasks.append(launch_bot(bot_id, meet_url, current_proxy))
        await asyncio.sleep(5)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
