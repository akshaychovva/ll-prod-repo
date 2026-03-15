import os
import logging
from flask import Flask, jsonify, request

from db import init_db, save_llm_request
from bedrock_client import call_bedrock


def create_app() -> Flask:
    app = Flask(__name__)

    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    init_db(app.logger)

    @app.route("/health", methods=["GET"])
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.route("/llm", methods=["POST"])
    def llm() -> tuple:
        data = request.get_json(silent=True) or {}
        prompt = (data.get("prompt") or "").strip()

        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        try:
            response_text = call_bedrock(prompt, app.logger)
        except Exception as exc:  # noqa: BLE001
            app.logger.exception("Error calling Bedrock: %s", exc)
            return jsonify({"error": "internal server error"}), 500

        try:
            save_llm_request(prompt, response_text, app.logger)
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("Failed to save LLM request: %s", exc)

        return jsonify({"response": response_text}), 200

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

