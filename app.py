"""Streamlit UI for SME Research Agent with real-time activity visibility."""

import nest_asyncio
import streamlit as st
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Allow nested event loops (needed for Streamlit + asyncio)
nest_asyncio.apply()

st.set_page_config(page_title="SME Research Agent", page_icon="🔍", layout="wide")

st.title("🔍 SME Research Agent")
st.markdown("Research Singapore SME prospects for AI adoption opportunities")

# Knowledge base directory
KNOWLEDGE_DIR = Path("data/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


# Initialize knowledge base (cached) - pipeline doesn't need the full agent
@st.cache_resource
def get_knowledge():
    from src.agnoresearch.knowledge import create_knowledge_base, add_document_sync

    knowledge = create_knowledge_base()

    # Load existing knowledge files
    for file_path in KNOWLEDGE_DIR.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
            try:
                add_document_sync(knowledge, file_path)
            except Exception:
                pass  # Skip files that fail to load

    return knowledge


knowledge = get_knowledge()

# Sidebar: Knowledge Base Management
with st.sidebar:
    st.header("📚 Knowledge Base")
    st.markdown("Upload pitch decks, case studies, service offerings")

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        help="Upload PDFs, text files, or markdown files"
    )

    if uploaded_files:
        from src.agnoresearch.knowledge import add_document_sync

        for uploaded_file in uploaded_files:
            file_path = KNOWLEDGE_DIR / uploaded_file.name
            file_path.write_bytes(uploaded_file.getvalue())
            try:
                add_document_sync(knowledge, file_path)
                st.success(f"✅ Added: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ Failed: {uploaded_file.name} - {e}")

    # Show existing files
    st.subheader("Loaded Documents")
    existing_files = list(KNOWLEDGE_DIR.glob("*"))
    if existing_files:
        for f in existing_files:
            if f.suffix.lower() in [".pdf", ".txt", ".md"]:
                st.write(f"📄 {f.name}")
    else:
        st.info("No documents uploaded yet")


def run_research_pipeline(website_url: str, instagram_url: str = None, facebook_url: str = None):
    """Run the research pipeline."""
    from src.agnoresearch.pipeline import run_pipeline

    return run_pipeline(
        website_url=website_url,
        instagram_url=instagram_url if instagram_url else None,
        facebook_url=facebook_url if facebook_url else None,
    )


def display_report(report):
    """Display a research report."""
    st.success("✅ Research complete!")
    st.divider()

    # Check for empty/failed results
    if not report.company_name and not report.overview:
        st.warning("⚠️ Research returned limited data. This can happen when:")
        st.write("- Instagram/Facebook blocked the scraper (common)")
        st.write("- Website has anti-bot protection")
        st.write("- URLs were invalid or unreachable")
        st.write("\n**Tip:** Try with just the website URL first.")
        return

    # Header metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Company", report.company_name or "Unknown")
    with col2:
        st.metric("Industry", report.industry or "Unknown")
    with col3:
        st.metric("Data Quality", getattr(report, 'data_quality', 'Medium') or "Low")

    # Overview
    st.subheader("📋 Overview")
    st.write(report.overview)

    # Products/Services
    if report.products_services:
        st.subheader("🛍️ Products/Services")
        for item in report.products_services:
            st.write(f"- {item}")

    # AI Opportunities with Evidence
    if report.ai_opportunities:
        st.subheader("💡 AI Opportunities")
        for i, opp in enumerate(report.ai_opportunities, 1):
            with st.expander(f"{i}. {opp.area}: {opp.opportunity} ({opp.complexity} complexity)"):
                st.write(f"**Rationale:** {opp.rationale}")

                # Show evidence if available
                if hasattr(opp, 'evidence') and opp.evidence:
                    st.markdown("**Evidence:**")
                    for ev in opp.evidence:
                        st.markdown(f"- {ev.claim}")
                        st.caption(f"Source: [{ev.source_url}]({ev.source_url})")
                        if ev.excerpt:
                            st.info(f'"{ev.excerpt}"')

    # Outreach Drafts (new)
    if report.outreach_drafts:
        st.subheader("📱 WhatsApp Drafts")
        for i, draft in enumerate(report.outreach_drafts.whatsapp_drafts, 1):
            with st.expander(f"Draft {i}", expanded=(i == 1)):
                st.text_area(
                    "Message",
                    draft.body,
                    height=100,
                    key=f"wa_draft_{i}",
                    help="Copy this message to send via WhatsApp"
                )
                st.caption(f"✨ Personalized using: {draft.personalization_used}")

        st.subheader("📧 Email Drafts")
        for i, draft in enumerate(report.outreach_drafts.email_drafts, 1):
            subject = draft.subject or "AI Solutions for Your Business"
            with st.expander(f"Draft {i}: {subject}", expanded=(i == 1)):
                st.text_input("Subject", subject, key=f"email_subject_{i}")
                st.text_area(
                    "Body",
                    draft.body,
                    height=150,
                    key=f"email_body_{i}",
                    help="Copy this email to send"
                )
                st.caption(f"✨ Personalized using: {draft.personalization_used}")

    # Legacy: Outreach Hooks (if no drafts available)
    elif report.outreach_hooks:
        st.subheader("🎯 Outreach Hooks")
        for hook in report.outreach_hooks:
            st.write(f"- {hook}")

    # Research Notes
    if report.research_notes:
        st.subheader("📝 Research Notes")
        st.info(report.research_notes)

    # Sources
    if report.sources:
        st.subheader("🔗 Sources")
        for source in report.sources:
            st.write(f"- [{source}]({source})")

    # Research Quality Metrics
    if hasattr(report, 'research_quality') and report.research_quality:
        rq = report.research_quality
        st.subheader("📊 Research Quality")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Sources Found", rq.sources_found)
        with cols[1]:
            st.metric("URLs Scraped", rq.urls_successfully_scraped)
        with cols[2]:
            st.metric("Evidence Pieces", rq.evidence_pieces)
        with cols[3]:
            st.metric("Quality Score", rq.quality_score)


# Main: Research Form
with st.form("research_form"):
    st.subheader("Enter Company URLs")

    website_url = st.text_input(
        "Website URL *",
        placeholder="https://company.com.sg",
        help="Required - company's main website"
    )
    instagram_url = st.text_input(
        "Instagram URL",
        placeholder="https://instagram.com/company",
        help="Optional - company's Instagram profile"
    )
    facebook_url = st.text_input(
        "Facebook URL",
        placeholder="https://facebook.com/company",
        help="Optional - company's Facebook page"
    )

    submitted = st.form_submit_button("🔍 Research", type="primary", use_container_width=True)

if submitted:
    if not website_url:
        st.error("Website URL is required")
    else:
        # Show progress indicators for each pipeline stage
        progress_container = st.container()

        with progress_container:
            stage_status = st.empty()
            stage_status.info("🔍 Stage 1/4: Scraping URLs...")

        try:
            # Run the pipeline
            with st.spinner("Running research pipeline..."):
                stage_status.info("🔍 Stage 1/4: Scraping URLs...")
                report = run_research_pipeline(
                    website_url=website_url,
                    instagram_url=instagram_url if instagram_url else None,
                    facebook_url=facebook_url if facebook_url else None,
                )

            # Clear progress
            stage_status.empty()

            # Display results
            if report and hasattr(report, 'company_name'):
                display_report(report)
            else:
                st.warning("Research completed but no structured content returned")

        except Exception as e:
            st.error(f"❌ Research failed: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
