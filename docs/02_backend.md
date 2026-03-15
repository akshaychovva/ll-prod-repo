## 02 – Backend (Flask, Postgres, Bedrock) line‑by‑line

In this file we walk through the main backend files:

- `backend/app.py`
- `backend/db.py`
- `backend/bedrock_client.py`

The goal is that you understand **every important line**.

---

### File: `backend/app.py`

```python
import os
import logging
from flask import Flask, jsonify, request
```

- **`import os`** – read environment variables (e.g. port, DB host).
- **`import logging`** – basic logging to stdout (useful for debugging, Kubernetes logs).
- **`from flask import ...`** – import Flask and helpers:
  - `Flask` – main web application class.
  - `jsonify` – helper to return JSON responses.
  - `request` – gives you access to the incoming HTTP request (body, headers, etc.).

```python
from db import init_db, save_llm_request
from bedrock_client import call_bedrock
```

- Import **your own modules**:
  - `init_db` – creates the Postgres table if it does not exist.
  - `save_llm_request` – inserts (prompt, response) into the table.
  - `call_bedrock` – sends the prompt to AWS Bedrock and returns text.

```python
def create_app() -> Flask:
    app = Flask(__name__)
```

- Define a factory function `create_app` that returns a `Flask` instance.
- Using a function is a clean pattern and works well with WSGI servers like Gunicorn.

```python
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
```

- Set up logging:
  - `basicConfig` sets a global logging level.
  - `app.logger` is Flask’s built-in logger – we set it to INFO so you see useful logs.

```python
    init_db(app.logger)
```

- Call `init_db` at startup:
  - Tries to connect to Postgres.
  - Creates the table if needed.
  - Logs a warning if Postgres is not reachable (for example, on first container start).

```python
    @app.route("/health", methods=["GET"])
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200
```

- Define the **health check** endpoint:
  - URL: `/health`, method: `GET`.
  - Returns JSON `{"status": "ok"}` and HTTP status code `200`.
  - Used by:
    - You (for debugging).
    - Kubernetes liveness/readiness probes.

```python
    @app.route("/llm", methods=["POST"])
    def llm() -> tuple:
        data = request.get_json(silent=True) or {}
        prompt = (data.get("prompt") or "").strip()
```

- Define the main LLM endpoint:
  - URL: `/llm`, method: `POST`.
  - `request.get_json(silent=True)` – tries to decode JSON, returns `None` instead of raising an error if invalid; we fall back to `{}`.
  - `data.get("prompt")` – read the `"prompt"` field.
  - `or ""` – if the key is missing or `None`, convert to empty string.
  - `.strip()` – remove surrounding whitespace.

```python
        if not prompt:
            return jsonify({"error": "prompt is required"}), 400
```

- Basic validation:
  - If the prompt is empty after stripping whitespace, respond with error JSON and HTTP `400 Bad Request`.

```python
        try:
            response_text = call_bedrock(prompt)
        except Exception as exc:  # noqa: BLE001
            app.logger.exception("Error calling Bedrock: %s", exc)
            return jsonify({"error": "internal server error"}), 500
```

- Try to call Bedrock:
  - `call_bedrock(prompt)` – our helper in `bedrock_client.py`.
  - If **anything** goes wrong:
    - `logger.exception` logs full stack trace (super useful in logs).
    - Return generic error with HTTP `500`.
  - We intentionally **do not** send the real Python exception to the user for security.

```python
        try:
            save_llm_request(prompt, response_text, app.logger)
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("Failed to save LLM request: %s", exc)
```

- Try to save prompt + response in Postgres:
  - If DB is down, we **don’t want to break the LLM response**.
  - So we catch errors, log a **warning**, but still return the LLM answer.

```python
        return jsonify({"response": response_text}), 200
```

- If everything is fine:
  - Return JSON with `"response"` field and HTTP `200`.

```python
    return app
```

- End of `create_app`.

```python
app = create_app()
```

- Create a **global Flask app object** used by Gunicorn and by `flask run`.

```python
if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
```

- This block only runs if you execute `python app.py` directly.
- `BACKEND_PORT` comes from environment; default is `5000`.
- `host="0.0.0.0"` – listen on all interfaces inside container.
- `debug=True` – convenient for local runs (in production we use Gunicorn, not this).

---

### File: `backend/db.py`

```python
import logging
import os
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
```

- `logging`, `os` – same idea as before.
- `Optional` from `typing` – type hint that a parameter can be `None`.
- `psycopg2` – the main Postgres driver.
- `RealDictCursor` – returns rows as dictionaries (`{"column": value}`).

```python
def get_db_connection():
    host = os.getenv("POSTGRES_HOST", "db")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DB", "llm_app")
    user = os.getenv("POSTGRES_USER", "llm_user")
    password = os.getenv("POSTGRES_PASSWORD", "llm_password")
```

- Read database settings from environment variables.
- The **defaults** match your local Docker Compose config:
  - host `db`, port `5432`, db `llm_app`, user `llm_user`, password `llm_password`.

```python
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        cursor_factory=RealDictCursor,
    )
```

- Open a new DB connection.
- Important:
  - **Do not** keep a global connection around in simple apps – just open, use, close.
  - In real production you might use a connection pool library.

```python
def init_db(logger: Optional[logging.Logger] = None) -> None:
    try:
        conn = get_db_connection()
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.warning("Could not connect to Postgres on startup: %s", exc)
        return
```

- Try to open a connection.
- If it fails:
  - Log a warning (if logger was passed).
  - Return early (we don’t crash the whole app).

```python
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_requests (
                        id SERIAL PRIMARY KEY,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
    finally:
        conn.close()
```

- Use a context manager `with conn:` – automatically commits/rolls back.
- `CREATE TABLE IF NOT EXISTS` – safe to run on every startup.
- The table:
  - `id SERIAL PRIMARY KEY` – auto‑increment integer.
  - `prompt TEXT NOT NULL` – what you sent to the LLM.
  - `response TEXT NOT NULL` – what the LLM replied.
  - `created_at TIMESTAMPTZ` – timestamp with time zone, default now.
- `finally: conn.close()` – always close the connection.

```python
def save_llm_request(prompt: str, response: str, logger: Optional[logging.Logger] = None) -> None:
    try:
        conn = get_db_connection()
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.warning("Could not connect to Postgres to save LLM request: %s", exc)
        return
```

- Function called by the Flask route to store one row.
- Again: try to connect, log warning and return if connection fails.

```python
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_requests (prompt, response)
                    VALUES (%s, %s);
                    """,
                    (prompt, response),
                )
    finally:
        conn.close()
```

- Open a transaction (`with conn:`).
- Execute parameterized SQL:
  - `%s` placeholders, and values in a tuple `(prompt, response)`.
  - This prevents SQL injection.
- Close connection at the end.

---

### File: `backend/bedrock_client.py`

```python
import json
import os
from typing import Any

import boto3
```

- `json` – to convert Python dicts to JSON string and back.
- `os` – read environment variables (`AWS_REGION`, `BEDROCK_MODEL_ID`).
- `Any` – type hint placeholder (not strictly needed, but common).
- `boto3` – AWS SDK for Python.

```python
_client = None
```

- Module‑level variable to store a **single Boto3 client**.
- This avoids re‑creating the Bedrock client on every request.

```python
def get_bedrock_client():
    global _client  # noqa: PLW0603
    if _client is None:
        region = os.getenv("AWS_REGION", "us-east-1")
        _client = boto3.client("bedrock-runtime", region_name=region)
    return _client
```

- Lazy initialization:
  - First time the function is called, it reads `AWS_REGION` (default `us-east-1`).
  - Creates a client for the **`bedrock-runtime`** service.
  - On later calls, reuses the same `_client`.
- `boto3` will automatically pick up AWS credentials from:
  - Environment variables.
  - `~/.aws/credentials`.
  - IAM role (if running in EKS with IRSA).

```python
def call_bedrock(prompt: str) -> str:
    model_id = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-haiku-20240307-v1:0",
    )
```

- Main function to call the model.
- Reads `BEDROCK_MODEL_ID` from env, defaulting to **Claude 3 Haiku**.

```python
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 256,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }
```

- This is the **request body** for Anthropic‑style models on Bedrock:
  - `anthropic_version` – required version string.
  - `max_tokens` – maximum tokens in the reply.
  - `temperature` – higher is more random, lower is more deterministic.
  - `messages` – chat style interface:
    - role `"user"` and text is your `prompt`.

```python
    client = get_bedrock_client()
```

- Get (or create) the Bedrock client we defined above.

```python
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
    )
```

- Call the Bedrock **runtime API**:
  - `modelId` – which model to use (e.g. Claude 3 Haiku).
  - `body` – JSON string of our request payload.
- `invoke_model` returns a response object whose `"body"` is a stream.

```python
    response_body = json.loads(response["body"].read())

    return response_body["content"][0]["text"]
```

- Read the body stream and `json.loads` it into a Python dict.
- For Anthropic responses on Bedrock:
  - The reply text is usually at `["content"][0]["text"]`.
- Return that string back to the caller (your Flask route).

---

Next steps:

- Open `docs/03_frontend.md` to learn how the Streamlit UI works.
- Then open `docs/04_docker_and_k8s.md` for Docker, Kubernetes, EKS, and secrets.

