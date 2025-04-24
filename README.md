# Telegram Channel Monitor with AI Analysis

A service for monitoring Telegram channels with intelligent content analysis using artificial intelligence technologies.

## 🚀 Key Features

- **Real-time Telegram channel monitoring** using Telethon
- **AI-powered post analysis** using OpenAI GPT for relevance determination and categorization
- **Smart content filtering** based on specified topics and interests
- **Automatic saving** of relevant posts to database
- **REST API** for channel and topic management
- **Simple API token authentication**

## 🧠 How AI Analysis Works

The service uses OpenAI GPT to analyze each post based on the following parameters:
- Determining relevance to specified topics
- Extracting key themes and concepts
- Analyzing sentiment and emotional tone
- Content classification by categories

## 🛠 Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Telegram API**: Telethon
- **AI**: OpenAI dspy
- **Authentication**: API Token
- **Async Processing**: asyncio