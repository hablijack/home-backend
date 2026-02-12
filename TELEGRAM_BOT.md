# Telegram Bot Setup

To use the Telegram bot feature, you need to configure the following environment variables in your `.env` file:

## Required Environment Variables

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Ollama Configuration (optional, has defaults)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Getting a Telegram Bot Token

1. Open Telegram and search for @BotFather
2. Send `/start` to BotFather
3. Send `/newbot` to create a new bot
4. Follow the prompts to name your bot and get a username
5. BotFather will give you a token - copy this to your `TELEGRAM_BOT_TOKEN`

## Setting up Ollama

1. Install Ollama: https://ollama.ai/download
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama service: `ollama serve`

## Usage

Once configured, the Telegram bot will:
- Start automatically when you run the application
- Respond to any text message with Ollama-generated responses
- Log messages and responses to the application log

## Health Check

You can check the bot status at: `http://localhost:8080/api/telegram/health`

This endpoint will show:
- Whether Telegram bot is properly configured
- Whether Ollama service is accessible
- Overall health status of the integration