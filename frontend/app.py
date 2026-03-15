import os

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


def main() -> None:
    st.set_page_config(page_title="Bedrock LLM Demo", page_icon="🤖")

    st.title("Bedrock LLM Demo")
    st.write("Type a question or prompt and send it to the backend, which calls AWS Bedrock.")

    with st.sidebar:
        st.markdown("### Backend status")
        if st.button("Check health"):
            try:
                resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
                st.write(f"Status: {resp.status_code} {resp.text}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error contacting backend: {exc}")

        st.markdown("---")
        st.markdown(f"**Backend URL:** `{BACKEND_URL}`")

    prompt = st.text_area("Prompt", height=150, placeholder="Ask the model anything...")

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
                    if resp.status_code == 200:
                        data = resp.json()
                        st.subheader("Model response")
                        st.write(data.get("response", "No response field in JSON."))
                    else:
                        st.error(f"Backend returned {resp.status_code}: {resp.text}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error calling backend: {exc}")


if __name__ == "__main__":
    main()

