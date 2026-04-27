# Telegram Political Party Survey Bot - Work In Progress

## Overview

This Telegram bot is designed to help a political group survey its members to gather feedback, understand engagement levels, and identify barriers to participation. The bot guides users through a multi-step survey and saves the responses to a Google Sheet for easy analysis.

It also includes administrative features, such as the ability to broadcast messages to all users who have interacted with the bot.

## Features

- **Multi-step Survey**: A guided conversation to collect structured feedback from members.
- **Google Sheets Integration**: Automatically saves all survey responses to a designated Google Sheet.
- **Admin Broadcast**: Allows authorized admins to send messages to all known users of the bot.
- **Secure Configuration**: Separates sensitive information (like API tokens) from the main codebase.
- **Simple Commands**: Easy-to-use commands for starting the survey, canceling, and getting help.

## Setup and Installation

Follow these steps to get the bot up and running.

### 1. Prerequisites

- Python 3.8 or higher.
- A Telegram Bot Token. You can get one by talking to the [BotFather](https://t.me/BotFather) on Telegram.
- A Google Cloud Platform (GCP) project with the Google Sheets API and Google Drive API enabled.
- Google Cloud service account credentials (`credentials.json`).

### 2. Clone the Repository

Clone this repository to your local machine or server:
```bash
git clone <repository_url>
cd <repository_directory>
```

### 3. Create `config.py`

Create a file named `config.py` in the root directory and add your Telegram Bot Token and Google Sheet name:

```python
# config.py
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN_HERE'
SHEET_NAME = 'Your Google Sheet Name Here'
```

### 4. Set Up Google Credentials

1.  Follow the [gspread authentication guide](https://docs.gspread.org/en/latest/oauth2.html) to get your `credentials.json` file.
2.  Place the downloaded `credentials.json` file in the root directory of this project.
3.  Share your Google Sheet with the `client_email` found in your `credentials.json` file, giving it "Editor" permissions.

### 5. Install Dependencies

Install the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 6. Configure Admins

Open `bot.py` and find the `ADMIN_USER_IDS` list. Replace the placeholder ID with the actual Telegram User ID(s) of the bot administrators.

```python
# In bot.py
ADMIN_USER_IDS = [123456789, 987654321]  # Replace with actual admin User IDs
```
To find your Telegram User ID, you can talk to a bot like [@userinfobot](https://t.me/userinfobot).

## Running the Bot

Once the setup is complete, you can start the bot with the following command:

```bash
python bot.py
```

You should see the message "Bot is polling..." in your terminal, which means the bot is active and listening for messages.

## How to Use

### For Members

-   `/start`: Begins the survey.
-   `/cancel`: Cancels the survey at any point.
-   `/help`: Shows a list of available commands.

### For Admins

-   `/broadcast <message>`: Sends a message to every user who has ever started the survey. The message will be the text you provide after the command.
    -   *Example*: `/broadcast Hello everyone, our next meeting is on Tuesday!`

## Internationalization (i18n)

This bot supports multiple languages. Here's how to manage translations.

### Adding a New Language

1.  **Initialize the language**: Run the following command, replacing `xx` with the new language code (e.g., `fr` for French):
    ```bash
    pybabel init -i locales/messages.pot -d locales -l xx
    ```
2.  **Translate the strings**: Edit the newly created `locales/xx/LC_MESSAGES/messages.po` file and add the translations for each `msgid`.
3.  **Compile the translations**: Run the compile command to make the translations available to the bot:
    ```bash
    pybabel compile -d locales
    ```

### Updating Translations

After adding new user-facing strings to the Python code, follow these steps to update the translation files:

1.  **Extract the new strings**:
    ```bash
    pybabel extract -F babel.cfg -o locales/messages.pot .
    ```
2.  **Update the language files**:
    ```bash
    pybabel update -i locales/messages.pot -d locales
    ```
3.  **Add the new translations**: Edit the `.po` files for each language and add the translations for the new strings.
4.  **Compile the translations**:
    ```bash
    pybabel compile -d locales
    ```
