# Telegram Channel Monitor with AI Analysis

A service for monitoring Telegram channels with intelligent content filtering using AI and regular expressions.

## 🚀 Key Features

- **Real-time Telegram channel monitoring** using Telethon
- **AI-powered relevance checking** using OpenAI GPT
- **Smart content filtering** using regular expressions and source lists
- **Automatic saving** of relevant messages to database
- **REST API** for filter and message management
- **Simple API token authentication**

## 🧠 How AI Analysis Works

The service uses OpenAI GPT to check message relevance based on custom prompts:
- Each filter can have a custom prompt to define what content is relevant
- Messages are checked against the filter's prompt using GPT
- Only messages that pass the relevance check are saved
- Additional filtering is done using regular expressions and source lists

## 🛠 Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL or SQLite
- **Telegram API**: Telethon
- **AI**: OpenAI dspy
- **Authentication**: API Token
- **Async Processing**: asyncio
- **Logging**: loguru

## 🐳 Running the Project with Docker

1. Make sure you have Docker and Docker Compose installed.
2. Clone the repository and navigate to the project directory.
3. Create a `.env` file with the required environment variables (see `.env.example` if available).
4. Build and start the services:
```bash
docker-compose up --build
```

The application will be available at: http://localhost:8000

---

## 📚 How to Use the API Routes

- All main features are available via the REST API.
- You need an API token (pass it in the `Authorization` header).
- **After successful verification (`/auth/verify`), you will receive an API token. You must include this token in the `Authorization` header for all subsequent requests.**

### Main Endpoints:

- `POST /auth/request` — Request a code for Telegram login.
- `POST /auth/verify` — Verify the code and create a session.
- `POST /filters/` — Create a new filter with pattern and prompt
- `GET /filters/` — Get all filters
- `GET /filters/{filter_id}` — Get a specific filter
- `PUT /filters/{filter_id}/sources` — Update filter sources
- `DELETE /filters/{filter_id}/sources` — Remove sources from filter
- `DELETE /filters/{filter_id}` — Delete a filter
- `GET /messages/` — Get all messages with date filtering
- `GET /messages/sources/{source_id}/messages` — Get messages from a source
- `GET /messages/filters/{filter_id}/messages` — Get messages from a filter
- `GET /messages/{message_id}` — Get a specific message
- `DELETE /messages/{message_id}` — Delete a message

Full interactive API documentation is available at:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)
