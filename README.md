# CardMarket Scraper

A lightweight Python scraper for Cardmarket that scans seller inventories and checks for matches with a user-provided list of trading cards.

## Features
- Scan automatically with support for Cloudflare rate limits (auto-wait)
- Supports YuGiOh (Y), Magic (M), and Pokemon (P)
- Displays results in a formatted table and lists cards not found

## Requirements
- Python 3.7 or newer
- Libraries:
  - `cloudscraper`
  - `beautifulsoup4`

## Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/o7-7/cardmarket-scraper.git
cd cardmarket-scraper
pip install cloudscraper beautifulsoup4
```

Alternatively, create a `requirements.txt` with:

```
cloudscraper
beautifulsoup4
```

and run:

```bash
pip install -r requirements.txt
```

## Usage
Run the script with the game code, seller name, and either a single card or a text file of card names (one per line):

```bash
python CardMarket_scraper.py [GAME_CODE] SELLER_NAME CARD_OR_FILE
```

- `GAME_CODE`: `Y` for YuGiOh, `M` for Magic, `P` for Pokemon
- `SELLER_NAME`: Cardmarket seller username
- `CARD_OR_FILE`: single card name or path to a `.txt` file with a list of cards

### Card List Format
If you use a `.txt` file for your card list, each line should follow this format:

```
card_name1\tnote1
card_name2
card_name3\tnote3
```

- Each card name is mandatory.
- You can optionally add personal notes after the card name by separating them with a **tab character** (`\t`).
- Notes are ignored by the scraper but can help you organize your list.

**Example file content:**

```
Dark Magician\t1st Edition
Blue-Eyes White Dragon
Red-Eyes Black Dragon\tJapanese Version
```

## Example Command

```bash
python CardMarket_scraper.py Y bestSeller card_list.txt
```

## License
This project is licensed under the MIT License.


## Disclaimer

Please do not increase the rate limits in respect of the site and to avoid any temporary or permanent bans. The scraper is designed to respect Cardmarket’s terms of service, and responsible use is encouraged to maintain access for everyone.
