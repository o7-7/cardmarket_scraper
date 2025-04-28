import cloudscraper
import sys
import time
import os
import threading
from urllib.parse import quote
from bs4 import BeautifulSoup
from collections import defaultdict

def clear_lines(n):
    for _ in range(n):
        sys.stdout.write('\x1b[1A')
        sys.stdout.write('\x1b[2K')


def spinner(progress, done_event, rate_limit_event, countdown_seconds, found_list):
    frames = ['-', '\\', '|', '/']
    current_frame = 0
    prev_lines = 0
    while not done_event.is_set():
        if prev_lines:
            clear_lines(prev_lines)
        preview_lines = []
        if found_list:
            preview_lines.append('')
            for name in found_list:
                preview_lines.append(f"Found: {name}")
            preview_lines.append('')
        if rate_limit_event.is_set():
            spinner_line = f" CLOUDFLARE RATE LIMIT REACHED, WAITING: {countdown_seconds[0]} s"
        else:
            current, total = progress
            spinner_line = f" {frames[current_frame]}   PROCESSING: {current}/{total}"
            current_frame = (current_frame + 1) % len(frames)
        preview_lines.append(spinner_line)
        for line in preview_lines:
            sys.stdout.write(line + '\n')
        sys.stdout.flush()
        prev_lines = len(preview_lines)
        time.sleep(0.1)
    if prev_lines:
        clear_lines(prev_lines)


def make_request(scraper, url, headers):
    try:
        response = scraper.get(url, headers=headers)
        return response.text, response.status_code
    except Exception:
        return None, None


def clean_card_name(card_name):
    return card_name.split('\t')[0].strip()


def parse_articles(html):
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    for article_row in soup.find_all('div', class_='article-row'):
        try:
            name_tag = article_row.find('div', class_='col-seller').find('a')
            name = name_tag.text.strip() if name_tag else 'N/A'
            rarity_tag = article_row.find('svg', title=True)
            rarity = rarity_tag['title'] if rarity_tag else 'N/A'
            edition_tag = article_row.find('a', class_='expansion-symbol')
            edition = edition_tag.find('span').text.strip() if edition_tag else 'N/A'
            condition_tag = article_row.find('span', class_='badge')
            condition = condition_tag.text.strip() if condition_tag else 'N/A'
            price_container = article_row.find('div', class_='price-container')
            price_tag = price_container.find('span', class_='fw-bold') if price_container else None
            price = price_tag.text.strip() if price_tag else 'N/A'
            qty_tag = article_row.find('span', class_='item-count')
            qty = qty_tag.text.strip() if qty_tag else 'N/A'
            articles.append({
                'name': name,
                'rarity': rarity,
                'edition': edition,
                'condition': condition,
                'price': price,
                'qty': qty
            })
        except Exception:
            continue
    return articles


def print_custom_table(results_by_card):
    def format_rarity(r):
        r_low = r.lower()
        return {
            "common": "",
            "ultra rare": "Ultra",
            "super rare": "Super",
            "platinum secret rare": "Platinum Secret",
            "ultimate rare": "Ultimate"
        }.get(r_low, r)

    headers = ["NAME", "RARITY", "EDITION", "CONDITION", "PRICE", "QTY"]
    col_widths = [len(h) for h in headers]
    groups = []
    for card_name, group in results_by_card.items():
        rows = []
        for art in group:
            rows.append([
                art['name'],
                format_rarity(art['rarity']),
                art['edition'],
                art['condition'],
                art['price'],
                art['qty']
            ])
        groups.append(rows)
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    def format_row(row):
        parts = []
        for i, cell in enumerate(row):
            parts.append(f" {str(cell):^{col_widths[i]}} ")
        return "|" + "|".join(parts) + "|"

    print(border)
    print(format_row(headers))
    print(border)
    for rows in groups:
        for row in rows:
            print(format_row(row))
        print(border)


def main(game, seller_name, card_names):
    headers = {
        "User-Agent": "aaa",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    scraper = cloudscraper.create_scraper()
    not_found_cards = []
    results_by_card = defaultdict(list)
    total = len(card_names)
    progress = [0, total]
    done_event = threading.Event()
    rate_limit_event = threading.Event()
    countdown_seconds = [0]
    found_list = []
    print()
    spinner_thread = threading.Thread(
        target=spinner,
        args=(progress, done_event, rate_limit_event, countdown_seconds, found_list),
        daemon=True
    )
    spinner_thread.start()

    idx = 0
    try:
        while idx < len(card_names):
            card_line = card_names[idx]
            card_name = clean_card_name(card_line)
            if not card_name:
                progress[0] = idx + 1
                idx += 1
                continue
            encoded = quote(card_name.replace(' ', '+'))
            url = f"https://www.cardmarket.com/en/{game}/Users/{seller_name}/Offers/Singles?name={encoded}"
            headers["Referer"] = url
            html, status = make_request(scraper, url, headers)
            if status == 429:
                rate_limit_event.set()
                for i in range(60, 0, -1):
                    countdown_seconds[0] = i
                    time.sleep(1)
                rate_limit_event.clear()
                continue
            if status == 400:
                done_event.set()
                spinner_thread.join()
                if results_by_card:
                    print_custom_table(results_by_card)
                print("ERROR 400: THERE IS PROBABLY A PROBLEM WITH THE CONFIGURATION OF THE HEADERS")
                sys.exit(1)
            if status is None or status != 200:
                done_event.set()
                spinner_thread.join()
                if results_by_card:
                    print_custom_table(results_by_card)
                print(f"ERROR: {status}")
                sys.exit(1)
            articles = parse_articles(html)
            found_articles = [a for a in articles if card_name.lower() in a['name'].lower()]
            if found_articles:
                results_by_card[card_name].extend(found_articles)
                found_list.append(card_name)
            else:
                not_found_cards.append(card_name)
            progress[0] = idx + 1
            idx += 1
            if idx < len(card_names):
                time.sleep(2)
    finally:
        done_event.set()
        spinner_thread.join()
    if results_by_card:
        print_custom_table(results_by_card)
    if not_found_cards:
        print("\nCARDS NOT FOUND:")
        for c in not_found_cards:
            print(f"  - {c}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python search_cards.py [Y|M|P] SELLER_NAME CARD_OR_FILE")
        print("  Y = YuGiOh, M = Magic, P = Pokemon")
        sys.exit(1)
    game_code = sys.argv[1].upper()
    if game_code not in ('Y', 'M', 'P'):
        print("Error: Game type must be 'Y', 'M', or 'P'")
        sys.exit(1)
    game = {'Y': 'YuGiOh', 'M': 'Magic', 'P': 'Pokemon'}[game_code]
    seller = sys.argv[2]
    input_arg = sys.argv[3]
    if os.path.isfile(input_arg):
        with open(input_arg, 'r', encoding='utf-8') as f:
            cards = [line.strip() for line in f]
    else:
        cards = [input_arg]
    main(game, seller, cards)

