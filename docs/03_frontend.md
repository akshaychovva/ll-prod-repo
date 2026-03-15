## 03 – Frontend (Streamlit) line‑by‑line

Here we explain `frontend/app.py`. This is the UI your users see.

---

### File: `frontend/app.py`

```python
import os

import requests
import streamlit as st
```

- `os` – to read the `BACKEND_URL` environment variable.
- `requests` – popular HTTP client library for Python.
- `streamlit` imported as `st` – main Streamlit API.

```python
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
```

- `BACKEND_URL` is the base URL for your Flask backend.
- Locally, when using Docker Compose:
  - The frontend container uses `http://backend:5000`.
  - On your host machine (for quick tests), `http://localhost:5000` works too.
- In Kubernetes:
  - It is set to `http://llm-backend:5000` using environment variables.

```python
def main() -> None:
    st.set_page_config(page_title="Bedrock LLM Demo", page_icon="🤖")
```

- `main` is the entry function Streamlit runs.
- `set_page_config` customizes page title and favicon emoji.

```python
    st.title("Bedrock LLM Demo")
    st.write("Type a question or prompt and send it to the backend, which calls AWS Bedrock.")
```

- Page title and short description text.

```python
    with st.sidebar:
        st.markdown("### Backend status")
        if st.button("Check health"):
            try:
                resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
                st.write(f"Status: {resp.status_code} {resp.text}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error contacting backend: {exc}")
```

- `with st.sidebar:` – everything inside appears in the left sidebar.
- `"Backend status"` section with a **button**.
- When you click **“Check health”**:
  - Sends a `GET` to `BACKEND_URL/health` with 5‑second timeout.
  - Displays the status code and raw text.
  - If something goes wrong (e.g. backend is down), shows a red error box.

```python
        st.markdown("---")
        st.markdown(f"**Backend URL:** `{BACKEND_URL}`")
```

- Horizontal line (`---`) for separation.
- Shows which backend URL is being used (very helpful when debugging env issues).

```python
    prompt = st.text_area("Prompt", height=150, placeholder="Ask the model anything...")
```

- Large text box for the user’s prompt.
- `placeholder` helps them understand what to do.

```python
    if st.button("Send to LLM"):
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Calling backend and Bedrock..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/llm",
                        json={"prompt": prompt},
                        timeout=30,
                    )
```

- Button that triggers sending the prompt:
  - If the text box is empty or whitespace, show a yellow warning.
  - Otherwise, show a spinner while the request is being processed.
  - Send `POST` request to the backend:
    - URL: `BACKEND_URL/llm`
    - JSON body: `{"prompt": prompt}`
    - 30‑second timeout (to handle slower model responses).

```python
                    if resp.status_code == 200:
                        data = resp.json()
                        st.subheader("Model response")
                        st.write(data.get("response", "No response field in JSON."))
                    else:
                        st.error(f"Backend returned {resp.status_code}: {resp.text}")
```

- If backend status is `200 OK`:
  - Parse JSON with `resp.json()`.
  - Show subheader and display `data["response"]`.
  - If the key is missing, show a fallback message.
- If status is not `200`:
  - Display a red error box with status code and body.

```python
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error calling backend: {exc}")
```

- Catch network errors (e.g. DNS, connection refused, timeout):
  - Show them nicely to the user instead of crashing the app.

```python

if __name__ == "__main__":
    main()
```

- Allows you to run the file directly (`python app.py`) for quick local tests.
- In Docker and Kubernetes we usually call it via the `streamlit` CLI.

---

Next:

- Open `docs/04_docker_and_k8s.md` to understand:
  - How Dockerfiles and `docker-compose.yml` work.
  - How the Kubernetes/EKS manifests are structured.
  - How to manage secrets and common edge cases.

