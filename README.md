# 🚀 Friends List API & Telegram Bot

This project is a complete backend system featuring a **FastAPI API** (`/app`) for managing a "friends" list and a **Telegram Bot** (`/bot`) for interaction. The entire stack (API, Bot, and Postgres DB) is containerized with **Docker Compose** and uses **Alembic** for database migrations.

---

## 1. 🛠️ Prerequisites

Before you start, make sure you have the following installed:

* [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/install/)
* [Git](https://git-scm.com/downloads)
* A **Telegram Bot Token** (get one from [@BotFather](https://t.me/BotFather))

---

## 2. ⚙️ Environment Variables

Before launching, you must create a `.env` file in the project root. You can copy the example:

```bash
cp .env.example .env
```
Then, edit `.env` and fill in your `TELEGRAM_BOT_TOKEN`.

Here is what each variable means:

| Variable | Description | Example (for Docker) |
| :--- | :--- | :--- |
| `DATABASE_USER` | Username for the Postgres database. | `postgres` |
| `DATABASE_PASSWORD` | Password for the Postgres database. | `mysecretpassword` |
| `DATABASE_NAME` | Name of the Postgres database. | `friends_db` |
| `DATABASE_HOSTNAME` | Hostname for the DB. Use `db` for Docker. | `db` |
| `DATABASE_PORT` | Port for Postgres. | `5432` |
| `TELEGRAM_BOT_TOKEN`| Your secret token from @BotFather. | `12345:ABC...` |
| `BACKEND_BASE_URL`| The URL the bot uses to find the API. | `http://api:8000` |

---

## 3. ⚡ How to Run Locally (Docker)

This single process will launch the API, the database, and the bot.

**1. Clone the Repository**
```bash
git clone <your-repo-url>
cd <your-project-folder>
```

**2. Create the `.env` File**
(If you haven't already from the step above)
```bash
cp .env.example .env
# Now, edit the .env file and add your TELEGRAM_BOT_TOKEN
```

**3. Build and Run with Docker Compose**
This command will build the `api` and `bot` images and start all three containers.
```bash
docker-compose up --build
```
*(You can add the `-d` flag to run it in the background)*

**4. Apply Database Migrations**
The API container is running, but the database is empty. You must run this **one time** to create the `friends` table.

**In a new terminal window**, run:
```bash
docker-compose exec api alembic upgrade head
```

**That's it!**
* The API is now running at `http://localhost:8000/docs`.
* The Telegram Bot is running and connected to the API.

---

## 4. 🔬 How to Run Tests

The tests are designed to run inside the Docker containers.

### API Tests (FastAPI)

1.  Make sure your containers are running:
    ```bash
    docker-compose up -d
    ```
2.  Execute `pytest` inside the `api` container:
    ```bash
    docker-compose exec api pytest test_main.py
    ```

### Bot Tests (Telegram)

1.  Make sure containers are running.
2.  Execute `pytest`:
    ```bash
    docker-compose exec bot pytest
    ```

---

## 5. 🤖 How to Use the Telegram Bot

The bot starts automatically with `docker-compose up`. Just find your bot on Telegram and start sending commands:

* `/start` - Shows a welcome message.
* `/addfriend` - Starts a step-by-step wizard to add a new friend (Photo -> Name -> Profession -> Description).
* `/list` - Shows all friends in your database.
* `/friend <id>` - Shows the full details for a single friend, including the photo.

---

## 6. 📖 API Endpoints

You can test these manually via `http://localhost:8000/docs` or the provided `requests.http` file (requires the "REST Client" extension in VS Code).

#### `POST /friends/`
Creates a new friend. Requires `multipart/form-data`.

**Form Fields:**
* `name` (str, required)
* `profession` (str, required)
* `profession_description` (str, optional)
* `photo` (file, required)

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/friends/" \
     -H "Content-Type: multipart/form-data" \
     -F "name=Alice" \
     -F "profession=Data Scientist" \
     -F "photo=@/path/to/your/image.jpg"
```

#### `GET /friends/`
Returns a list of all friends.

**Example (cURL):**
```bash
curl http://localhost:8000/friends/
```

#### `GET /friends/{id}`
Returns a single friend by their ID. (Note: no trailing slash).

**Example (cURL):**
```bash
curl http://localhost:8000/friends/1
```

#### `GET /media/{filename}`
Returns the static image file for a friend.

**Example (cURL):**
```bash
curl http://localhost:8000/media/a1b2c3d4-e5f6.jpg
```

---

## 7. 🏛️ Architecture Notes

This project runs in a Docker-internal network.
* The **Bot** (`bot-1`) finds the **API** (`api-1`) using its service name: `http://api:8000` (this is set in `BACKEND_BASE_URL`).
* The **API** (`api-1`) finds the **Database** (`db-1`) using its service name: `db` (this is set in `DATABASE_HOSTNAME`).
* You (the user) access the API from your browser/Postman via `http://localhost:8000`.
* Telegram's servers **cannot** access `http://api:8000`. This is why the bot must download photos itself (as bytes) and send them to Telegram, rather than sending the URL.
```