.PHONY: run run-streamlit run-web install setup clean

# Default: run the new Flask webapp
run: run-web

# Flask webapp (new playful UI)
run-web:
	uv run python web.py

# Streamlit app (original)
run-streamlit:
	uv run streamlit run app.py

install:
	uv sync

setup: install
	ollama pull qwen2.5:14b
	ollama pull nomic-embed-text

clean:
	rm -rf data/ .venv/ __pycache__/ src/**/__pycache__/
