# Reddit Memes Filtering Bot

This bot is part of a larger project, the main repository for which can be found [here](https://github.com/avkaz/code_review/tree/main). This bot is one of three that create an almost fully automated Telegram posting system. It focuses on the filtering aspect, allowing users to manage, approve, and interact with memes scraped by another bot and stored in a PostgreSQL database.

## Features

*   **Meme Management:**
    *   Browse all memes scraped and stored in the database.
    *   View memes individually.
    *   Approve, reject, and add comments to memes.
*   **Meme Upload:**
    *   Upload your own memes (photo or video).
*   **Upload Order:**
    *   View and manage the list of approved memes scheduled for posting.
    *   Delete memes from the posting queue.
    *   Modify the order of memes in the queue.
*   **Deleted Memes Management:**
    *   Manage deleted memes.
    *   Restore memes from the deleted list.
    *   Permanently delete memes from the database.
*   **Statistics:**
    *   View statistics on the number of memes scraped, approved, and uploaded by you.

## Screenshots

![74eda21a-460a-4bf1-92e5-b5f5acbba7f1](https://github.com/user-attachments/assets/334f277e-8db0-44f6-8c9e-b9aa5ac9d0bb)
![8172811a-9122-498e-adcd-ebc25918e795](https://github.com/user-attachments/assets/4f6ce43a-2c85-449c-abe6-0b7ac76f1497)
![6d237bac-f2ec-4e75-b488-3ab0b71529d4](https://github.com/user-attachments/assets/3053d886-dcf4-477e-82c5-7a5a3693aa95)

## Requirements

*   **Telegram Bot:** You need to create a Telegram bot using BotFather and obtain its token.  This token needs to be placed in both `main.py` and `config.py` files.
*   **Docker:** The application is containerized with Docker for easy setup and deployment.
*   **Google Firebase API Key:** A Google Firebase API key is required. Obtain the `key.json` file and place it in the main directory.

## How to Run

1.  **Create a Telegram Bot:** Talk to BotFather on Telegram to create your bot.  You'll receive a bot token.

2.  **Paste Telegram Token:** Paste the bot token into the appropriate locations in both `main.py` and `config.py`.

3.  Clone this repository:

    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

4.  Ensure the `key.json` file from Google Firebase is in the main directory.

5.  Build and run the Docker container:

    ```bash
    docker-compose up --build
    ```

6.  Access the bot's functionalities as specified.

## Main Repository

*   Main Project Repository: [https://github.com/avkaz/code_review/tree/main](https://github.com/avkaz/code_review/tree/main)
