import asyncio
import os
import json
import re
from pathlib import Path
from scraper import (
    manual_login, get_categories,
    get_levels_and_topics, get_topic_questions, scrape_question
)
from playwright.async_api import async_playwright


def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)


async def main():
    os.makedirs("data", exist_ok=True)
    storage_state_path = "data/storage_state.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # If we have session saved, use it
        if os.path.exists(storage_state_path):
            context = await browser.new_context(storage_state=storage_state_path)
            print("🍪 Loaded session from storage_state.json")
        else:
            # No session - let user log in manually and save session
            context = await browser.new_context(
    viewport={"width": 1280, "height": 800},
    device_scale_factor=1.0,
    is_mobile=False,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)

            page = await context.new_page()
            await manual_login(page)
            await context.storage_state(path=storage_state_path)
            print("✅ Session saved to storage_state.json")

        page = await context.new_page()

        try:
            categories = await get_categories(page)
        except Exception as e:
            print(f"❌ Failed to get categories: {e}")
            return

        for cat_url, cat_name in categories:
            print(f"📁 Entering category: {cat_name}")
            try:
                levels = await get_levels_and_topics(page, cat_url)
            except Exception as e:
                print(f"❌ Failed to get levels/topics for {cat_name}: {e}")
                continue

            for level_name, topic_name, topic_url in levels:
                print(f"   🔹 {level_name} ➤ {topic_name}")
                question_links = await get_topic_questions(page, topic_url)

                folder_path = os.path.join("data", sanitize(cat_name), sanitize(topic_name))
                os.makedirs(folder_path, exist_ok=True)

                for q_url in question_links:
                    data = await scrape_question(page, q_url)

                    if data is None or data.get("question") == "Question content not found.":
                        print(f"⚠️ Skipping {q_url}")
                        continue

                    file_name = sanitize(data['title'])[:50] + ".json"
                    file_path = os.path.join(folder_path, file_name)

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)

                    print(f"✅ Saved: {file_name}")

        print("🎉 Done scraping.")
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
