# Telegram Drug Group Scraper

This project is a Telegram scraper built using [Telethon](https://docs.telethon.dev/).
It searches for Telegram groups and channels based on drug-related keywords, joins them (if possible), fetches messages, media (photos/videos), and admin information, and saves the results locally.

## Features

-   Searches Telegram for groups and channels using a list of keywords.
-   Joins public groups/channels.
-   Fetches messages, photos, videos, and documents.
-   Collects admin information for each group/channel.
-   Organizes data in structured folders:
    -   `texts/` – Text messages and admin info
    -   `photos/` – Downloaded images
    -   `videos/` – Downloaded videos
    -   `documents/` – Other documents

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/tbharathraj205/telegram-bot.git](https://github.com/tbharathraj205/telegram-bot.git)
    cd telegram-drug-scraper
    ```

2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Update your Telegram credentials in `main.py`:
    ```python
    api_id = 'YOUR_API_ID'
    api_hash = 'YOUR_API_HASH'
    phone_number = 'YOUR_PHONE_NUMBER'
    ```

## Usage

Run the script using Python 3.10+:

```bash
python main.py