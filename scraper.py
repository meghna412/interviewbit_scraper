import asyncio
import json
from bs4 import BeautifulSoup
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_PATH = Path("data/cookies.json")


async def save_cookies(context):
    cookies = await context.storage_state(path=None)
    COOKIES_PATH.write_text(json.dumps(cookies), encoding="utf-8")
    print("💾 Cookies saved.")


async def load_cookies():
    if COOKIES_PATH.exists():
        return json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
    return None


async def manual_login(page):
    await page.goto("https://www.interviewbit.com/users/sign_in/")
    print("🔓 Please log in manually and solve CAPTCHA.")
    input("✅ After logging in and dashboard appears, press ENTER here to continue...")



async def get_categories(page):
    await page.goto("https://www.interviewbit.com/practice/")
    await page.wait_for_timeout(3000)
    soup = BeautifulSoup(await page.content(), "html.parser")
    links = soup.select("a.tappable.pp-page-section__course.no-highlight")
    categories = []
    for a in links:
        href = a.get("href")
        title_div = a.select_one("div.course-track-card__title")
        if href and title_div:
            url = "https://www.interviewbit.com" + href
            name = title_div.text.strip()
            categories.append((url, name))
    return categories


async def get_levels_and_topics(page, url):
    await page.goto(url)
    await page.wait_for_timeout(2000)
    soup = BeautifulSoup(await page.content(), "html.parser")
    levels = []
    level_sections = soup.select(".ib-tracks-layout__card-associations-section")

    for section in level_sections:
        level_div = section.select_one(".ib-tracks-layout__level-name")
        level_name = level_div.text.strip() if level_div else "Unknown Level"

        topic_cards = section.select("a.ib-tracks-layout__card")

        for card in topic_cards:
            topic_name_el = card.select_one(".ib-tracks-layout__card-heading-text")
            topic_name = topic_name_el.text.strip() if topic_name_el else "Untitled"
            topic_href = card.get("href")
            topic_url = "https://www.interviewbit.com" + topic_href if topic_href else None

            if topic_url:
                levels.append((level_name, topic_name, topic_url))

    return levels


async def get_topic_questions(page, topic_url):
    await page.goto(topic_url)
    await page.wait_for_timeout(2000)
    soup = BeautifulSoup(await page.content(), "html.parser")
    links = soup.select("a.ib-topic-section__problems-bucket-tile")
    return ["https://www.interviewbit.com" + a["href"] for a in links]


async def scrape_question(page, url):
    try:
        await page.goto(url)
        await page.wait_for_timeout(3000)
        soup = BeautifulSoup(await page.content(), "html.parser")

        title_el = soup.select_one("h1")
        title = title_el.get_text(strip=True) if title_el else "Title not found"

        question_el = soup.select_one(".question-description") or soup.select_one(".css-1jjp8jh")
        question_text = question_el.get_text(strip=True) if question_el else "Question content not found."

        return {
            "title": title,
            "question": question_text
        }
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None
