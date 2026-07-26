import asyncio
import os
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright

async def main():
    print("Launching Chromium browser for automated UI verification...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1100})
        
        print("Navigating to http://localhost:8501...")
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Take landing page screenshot
        output_landing = r"C:\Users\DELL\.gemini\antigravity-ide\brain\2812706f-cfc2-4092-906d-37da362aa2d2\streamlit_landing.png"
        await page.screenshot(path=output_landing, full_page=True)
        print(f"Landing page screenshot saved to: {output_landing}")
        
        print("Clicking 'Connect Demo Dataset (IBM HI-Small)'...")
        btn_demo = page.get_by_role("button", name="Connect Demo Dataset (IBM HI-Small)").first
        if await btn_demo.is_visible():
            await btn_demo.click()
            await asyncio.sleep(2)
            
        print("Clicking scenario chip: Find structuring in last 30 days...")
        chip_btn = page.get_by_role("button", name="Find structuring in last 30 days").first
        if await chip_btn.is_visible():
            await chip_btn.click()
            print("Waiting for AI workspace pipeline & results to synthesize...")
            await asyncio.sleep(8)
            
        # Take AI workspace screenshot
        output_workspace = r"C:\Users\DELL\.gemini\antigravity-ide\brain\2812706f-cfc2-4092-906d-37da362aa2d2\streamlit_results.png"
        await page.screenshot(path=output_workspace, full_page=True)
        print(f"AI Workspace screenshot saved to: {output_workspace}")
        
        await browser.close()
        print("Verification complete!")

if __name__ == "__main__":
    asyncio.run(main())
