.PHONY: run install setup clean

run:
	uv run streamlit run app.py

install:
	uv sync

setup: install
	ollama pull qwen2.5:14b
	ollama pull nomic-embed-text

clean:
	rm -rf data/ .venv/ __pycache__/ src/**/__pycache__/
