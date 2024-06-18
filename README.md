# Aiogram Scenes Example

___

## Chat Settings

A simple example of using the aiogram library to create a chat bot with the `Chat Settings` ability.
___

### How to run

Clone the repository:

```bash
git clone git@github.com:andrew000/aiogram-scenes-chat-settings.git
```

Fill `.env` file (don't forget to set `developer_id`):

```bash
cp .env-dist .env
nano .env
```

Deploy the project using docker-compose

```bash
make up
```

After deployment, consider use `/prepare` command to create prepare media files. Also, you can use deeplink in terminal.
___

### How to use

Create a new chat and add your Bot to it. Then, send `/start` and `/prepare` commands to the chat to init settings.
To open chat settings, use `/chat_settings` command.

### Codebase

* The project is based on the `aiogram` library and uses `scenes` (built-in feature) to manage the chat settings.
  The `ChatSettings` scene is built as a tree structure with nested scenes for each setting.

* Each scene has an `entry` and `exit` points for different update types (`Message`, `CallbackQuery`) where necessary.

* The `ChatSettings` scene is a simplified scene without i18n support, from the t.me/DarkKusBot telegram bot.
  If you need i18n support, you can use the `aiogram_i18n` library or implement your own solution.

* The feature `set_reports_special_chat` uses some kind of hashing algorithm to prevent users from trying to setup
  special chat without pending record in Redis. I don't recommend using this feature if you don't understand how it
  works.

* The project may contain some bugs or issues, so feel free to create an issue or PR if you find something wrong.

### License

I use the `GNU GENERAL PUBLIC LICENSE v3.0` for this project. You can read the license in the `LICENSE` file.
You are free to use this project for any purpose, but you must provide a link to the original repository.

### Questions

If you have any questions, feel free to ask me in the [Aiogram Chat](https://t.me/aiogram_pcr)
