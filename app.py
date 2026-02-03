"""Streamlit UI for SME Research Agent."""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="SME Research Agent", page_icon="🔍", layout="wide")

st.title("🔍 SME Research Agent")
st.markdown("Research Singapore SME prospects for AI adoption opportunities")

# Knowledge base directory
KNOWLEDGE_DIR = Path("data/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


# Initialize knowledge base and agent (cached)
@st.cache_resource
def get_knowledge_and_agent():
    from src.agnoresearch.agent import create_research_agent
    from src.agnoresearch.knowledge import create_knowledge_base, add_document_sync

    knowledge = create_knowledge_base()

    # Load existing knowledge files
    for file_path in KNOWLEDGE_DIR.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
            try:
                add_document_sync(knowledge, file_path)
            except Exception:
                pass  # Skip files that fail to load

    agent = create_research_agent(knowledge=knowledge)
    return knowledge, agent


knowledge, agent = get_knowledge_and_agent()

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
        # Build research prompt
        urls_text = f"Website: {website_url}"
        if instagram_url:
            urls_text += f"\nInstagram: {instagram_url}"
        if facebook_url:
            urls_text += f"\nFacebook: {facebook_url}"

        prompt = f"""Research this company using the provided URLs.
Also search the knowledge base for relevant Growth Foundry services that could help them.

URLs:
{urls_text}"""

        # Show progress
        with st.status("🔍 Researching...", expanded=True) as status:
            st.write("Browsing company URLs...")
            st.write("Searching knowledge base for relevant services...")

            try:
                response = agent.run(prompt)
                status.update(label="✅ Research complete!", state="complete")

            except Exception as e:
                status.update(label="❌ Research failed", state="error")
                st.error(f"Error: {str(e)}")
                st.stop()

        # Display results
        st.divider()

        if response.content:
            report = response.content

            # Check if it's a Pydantic model (has model_dump) or dict
            if hasattr(report, 'company_name'):
                # Check for empty/failed results
                if not report.company_name and not report.overview:
                    st.warning("⚠️ Research returned limited data. This can happen when:")
                    st.write("- Instagram/Facebook blocked the scraper (common)")
                    st.write("- Website has anti-bot protection")
                    st.write("- URLs were invalid or unreachable")
                    st.write("\n**Tip:** Try with just the website URL first.")
                    st.stop()

                # It's a Pydantic model - access attributes directly
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Company", report.company_name or "Unknown")
                with col2:
                    st.metric("Industry", report.industry or "Unknown")
                with col3:
                    st.metric("Data Quality", getattr(report, 'data_quality', 'Medium') or "Low")

                st.subheader("📋 Overview")
                st.write(report.overview)

                if report.products_services:
                    st.subheader("🛍️ Products/Services")
                    for item in report.products_services:
                        st.write(f"- {item}")

                if report.ai_opportunities:
                    st.subheader("💡 AI Opportunities")
                    for i, opp in enumerate(report.ai_opportunities, 1):
                        with st.expander(f"{i}. {opp.area}: {opp.opportunity} ({opp.complexity} complexity)"):
                            st.write(opp.rationale)

                if report.outreach_hooks:
                    st.subheader("🎯 Outreach Hooks")
                    for hook in report.outreach_hooks:
                        st.write(f"- {hook}")

                if report.research_notes:
                    st.subheader("📝 Research Notes")
                    st.info(report.research_notes)

                if report.sources:
                    st.subheader("🔗 Sources")
                    for source in report.sources:
                        st.write(f"- {source}")
            else:
                # Fallback to raw display
                st.markdown(str(response.content))
