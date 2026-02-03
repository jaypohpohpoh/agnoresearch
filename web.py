"""Flask webapp for Agno Research - SME Research & Outreach Tool."""

import asyncio
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "agno-research-secret-key"

# Knowledge base directory
KNOWLEDGE_DIR = Path("data/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# Store research results in memory (in production, use a database)
research_cache = {}


def get_knowledge():
    """Initialize knowledge base."""
    from src.agnoresearch.knowledge import create_knowledge_base, add_document_sync

    knowledge = create_knowledge_base()

    # Load existing knowledge files
    for file_path in KNOWLEDGE_DIR.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
            try:
                add_document_sync(knowledge, file_path)
            except Exception:
                pass

    return knowledge


# Routes
@app.route("/")
def dashboard():
    """Dashboard with recent research and quick stats."""
    recent_research = list(research_cache.values())[-5:]
    return render_template(
        "dashboard.html",
        recent_research=recent_research,
        total_research=len(research_cache),
        knowledge_count=len(list(KNOWLEDGE_DIR.glob("*"))),
    )


@app.route("/research", methods=["GET", "POST"])
def research():
    """Research form and results."""
    if request.method == "POST":
        website_url = request.form.get("website_url")
        instagram_url = request.form.get("instagram_url") or None
        facebook_url = request.form.get("facebook_url") or None

        if not website_url:
            return render_template("research.html", error="Website URL is required")

        try:
            from src.agnoresearch.pipeline import run_pipeline

            report = run_pipeline(
                website_url=website_url,
                instagram_url=instagram_url,
                facebook_url=facebook_url,
            )

            # Cache the result
            if report and report.company_name:
                research_cache[report.company_name] = {
                    "company_name": report.company_name,
                    "industry": report.industry,
                    "overview": report.overview,
                    "ai_opportunities": [
                        {
                            "area": opp.area,
                            "opportunity": opp.opportunity,
                            "complexity": opp.complexity,
                            "rationale": opp.rationale,
                        }
                        for opp in (report.ai_opportunities or [])
                    ],
                    "outreach_drafts": {
                        "whatsapp": [
                            {"body": d.body, "personalization": d.personalization_used}
                            for d in (report.outreach_drafts.whatsapp_drafts if report.outreach_drafts else [])
                        ],
                        "email": [
                            {"subject": d.subject, "body": d.body, "personalization": d.personalization_used}
                            for d in (report.outreach_drafts.email_drafts if report.outreach_drafts else [])
                        ],
                    },
                    "sources": report.sources or [],
                }

            return render_template("research.html", report=report)

        except Exception as e:
            return render_template("research.html", error=str(e))

    return render_template("research.html")


@app.route("/api/research", methods=["POST"])
def api_research():
    """API endpoint for AJAX research requests."""
    data = request.json
    website_url = data.get("website_url")
    instagram_url = data.get("instagram_url") or None
    facebook_url = data.get("facebook_url") or None

    if not website_url:
        return jsonify({"error": "Website URL is required"}), 400

    try:
        from src.agnoresearch.pipeline import run_pipeline

        report = run_pipeline(
            website_url=website_url,
            instagram_url=instagram_url,
            facebook_url=facebook_url,
        )

        if report and report.company_name:
            result = {
                "company_name": report.company_name,
                "industry": report.industry,
                "overview": report.overview,
                "products_services": report.products_services or [],
                "ai_opportunities": [
                    {
                        "area": opp.area,
                        "opportunity": opp.opportunity,
                        "complexity": opp.complexity,
                        "rationale": opp.rationale,
                    }
                    for opp in (report.ai_opportunities or [])
                ],
                "outreach_drafts": {
                    "whatsapp": [
                        {"body": d.body, "personalization": d.personalization_used}
                        for d in (report.outreach_drafts.whatsapp_drafts if report.outreach_drafts else [])
                    ],
                    "email": [
                        {"subject": d.subject, "body": d.body, "personalization": d.personalization_used}
                        for d in (report.outreach_drafts.email_drafts if report.outreach_drafts else [])
                    ],
                },
                "sources": report.sources or [],
                "research_notes": report.research_notes,
            }
            research_cache[report.company_name] = result
            return jsonify(result)

        return jsonify({"error": "No data returned from research"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/drafts")
def drafts():
    """View and edit outreach drafts."""
    all_drafts = []
    for company, data in research_cache.items():
        if "outreach_drafts" in data:
            for wa in data["outreach_drafts"].get("whatsapp", []):
                all_drafts.append({"type": "whatsapp", "company": company, **wa})
            for em in data["outreach_drafts"].get("email", []):
                all_drafts.append({"type": "email", "company": company, **em})
    return render_template("drafts.html", drafts=all_drafts)


@app.route("/knowledge", methods=["GET", "POST"])
def knowledge():
    """Knowledge base management."""
    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = KNOWLEDGE_DIR / filename
                file.save(file_path)

                try:
                    from src.agnoresearch.knowledge import add_document_sync

                    knowledge_base = get_knowledge()
                    add_document_sync(knowledge_base, file_path)
                    return redirect(url_for("knowledge", success=filename))
                except Exception as e:
                    return redirect(url_for("knowledge", error=str(e)))

    files = [
        {"name": f.name, "size": f.stat().st_size, "type": f.suffix}
        for f in KNOWLEDGE_DIR.glob("*")
        if f.suffix.lower() in [".pdf", ".txt", ".md"]
    ]
    return render_template(
        "knowledge.html",
        files=files,
        success=request.args.get("success"),
        error=request.args.get("error"),
    )


@app.route("/knowledge/delete/<filename>", methods=["POST"])
def delete_knowledge(filename):
    """Delete a knowledge base file."""
    file_path = KNOWLEDGE_DIR / secure_filename(filename)
    if file_path.exists():
        file_path.unlink()
    return redirect(url_for("knowledge"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
