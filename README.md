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

## 🐳 Running the Project with Docker

1. Make sure you have Docker and Docker Compose installed.
2. Clone the repository and navigate to the project directory.
3. Create a `.env` file with the required environment variables (see `.env.example` if available).
4. Build and start the services:

```bash
docker-compose up --build
```

5. The application will be available at: http://localhost:8000

---

## 📚 How to Use the API Routes

- All main features are available via the REST API.
- You need an API token (pass it in the `Authorization` header).
- **After successful verification (`/auth/verify`), you will receive an API token. You must include this token in the `Authorization` header for all subsequent requests.**

### Main Endpoints:

- `POST /auth/request` — Request a code for Telegram login.
- `POST /auth/verify` — Verify the code and create a session.
- `GET /posts/` — Get a list of posts (supports date filtering and pagination).
- `GET /posts/channels/{channel_id}/posts` — Get posts from a specific channel.
- `GET /posts/topics/{topic_id}/posts` — Get posts by topic.
- `POST /topics/` — Create a new topic.
- `PUT /topics/{topic_id}/channels` — Add channels to a topic.
- `DELETE /topics/{topic_id}/channels` — Remove channels from a topic.
- `DELETE /topics/{topic_id}` — Delete a topic.

Full interactive API documentation is available at:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)
