import os
import gradio as gr
from pathlib import Path

print("0 - Starting lightweight imports")

KNOWLEDGE_BASE_PATH = Path(__file__).parent / "Knowledge-base" / "finance_reports"


# -----------------------------------------
# 1. INGESTION LOGIC
# -----------------------------------------
# -----------------------------------------
# 1. INGESTION LOGIC
# -----------------------------------------
def run_ingestion(company_name, year, log_box):
    """Runs the pipeline generator and accumulates logs for the UI."""
    current_log = ""
    clear_chat = []
    clear_sources = "*Sources will appear here after you ask a question.*"

    # 1. Yield immediate status and FORCE CLEAR the download button component.
    # By yielding a full gr.DownloadButton object with value=None, we destroy the old cached file.
    current_log = "⏳ Initializing pipeline modules (this might take a few seconds)...\n"
    yield current_log, gr.DownloadButton(value=None, label="📥 Download MD"), clear_chat, clear_sources

    import time
    time.sleep(0.5)

    from master_pipeline import build_knowledge_base
    from ticker_extractor import get_ticker

    ticker = get_ticker(company_name)
    if ticker == "UNKNOWN":
        ticker = company_name.strip().upper().replace(" ", "_")
    expected_md_path = KNOWLEDGE_BASE_PATH / f"{ticker}_{int(year)}_10k.md"

    # 2. Run the pipeline
    for status in build_knowledge_base(company_name, int(year)):
        current_log += status + "\n"

        # If the file exists on disk, yield a NEW DownloadButton object with the file path.
        # This forces Gradio to register the new file and bypass the cache.
        if expected_md_path.exists():
            downloadable_file = gr.DownloadButton(value=str(expected_md_path), label="📥 Download MD (Ready)")
        else:
            downloadable_file = gr.DownloadButton(value=None, label="📥 Download MD")

        yield current_log, downloadable_file, clear_chat, clear_sources

# -----------------------------------------
# 2. CHAT + SOURCES LOGIC
# -----------------------------------------
def format_sources(sources):
    """Formats the sources with HTML to match the example's clean styling."""
    result = "<h2 style='color: #ff7800;'>📚 Sources & Evidence</h2>\n\n"

    if not sources:
        return result + "<i>No sources retrieved for this question.</i>"

    if isinstance(sources, list):
        for i, src in enumerate(sources, 1):
            if isinstance(src, dict):
                result += f"<span style='color: #ff7800; font-weight: bold;'>Source {i}</span><br>"
                result += f"<b>Item:</b> {src.get('item', 'N/A')}<br>"
                result += f"<b>Headline:</b> {src.get('headline', 'N/A')}<br>"
                result += f"<b>Text:</b> {src.get('text', 'N/A')[:300]}...<br><br>"
            else:
                result += f"<span style='color: #ff7800;'>Source {i}:</span> {str(src)}<br><br>"
    else:
        result += str(sources)

    return result


def put_message_in_chatbot(message, history):
    history = history or []
    return "", history + [{"role": "user", "content": message}]


def chat(history, company_name, year):
    """Processes the RAG pipeline and appends the assistant's response."""

    print("Loading heavy chat libraries...")
    from rag_orchestrator.pipeline import run_rag_pipeline
    from ticker_extractor import get_ticker

    last_message = history[-1]["content"]
    if isinstance(last_message, list):
        last_message = last_message[0]["text"]
    elif isinstance(last_message, dict):
        last_message = last_message.get("text", "")

    prior = history[:-1]
    if not year:
        history.append({"role": "assistant", "content": "⚠️ Please enter a year above."})
        return history, format_sources([])

    ticker = get_ticker(company_name)
    if ticker == "UNKNOWN":
        history.append(
            {"role": "assistant", "content": "⚠️ Could not identify the company ticker. Please check the name."})
        return history, format_sources([])

    answer, sources = run_rag_pipeline(
        question=last_message,
        ticker=ticker.strip().upper(),
        year=int(year),
        history=prior,
    )

    history.append({"role": "assistant", "content": answer})
    return history, format_sources(sources)


# -----------------------------------------
# 3. GRADIO UI LAYOUT
# -----------------------------------------
theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

print("1 - Building Gradio UI...")

with gr.Blocks(title="AlphaLens Finance RAG") as demo:
    gr.Markdown("# 🏢 AlphaLens: 10-K RAG System\nAsk me anything about corporate 10-K annual reports!")

    with gr.Row():
        company_input = gr.Textbox(
            label="Company Name",
            placeholder="e.g., jp morgan, microsoft",
            scale=3
        )
        year_input = gr.Number(
            label="Year",
            value=2024,
            minimum=2010,
            maximum=2025,
            precision=0,
            scale=1
        )

        md_download = gr.DownloadButton(
            label="📥 Download MD",
            scale=1,
            variant="secondary"
        )

    with gr.Row():
        build_btn = gr.Button("🚀 Build Knowledge Base", variant="primary")

    log_output = gr.Textbox(
        label="Pipeline Progress",
        lines=8,
        max_lines=20,
        interactive=False,
        autoscroll=True,
    )

    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(
                label="💬 Conversation",
                height=600,
            )
            chat_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask anything about the 10-K...",
                show_label=False,
            )

        with gr.Column(scale=1):
            sources_output = gr.Markdown(
                label="📚 Retrieved Context",
                value="*Sources will appear here after you ask a question.*",
                container=True,
                height=600,
            )

    # =====================================================================
    # EVENT LISTENERS MUST BE AT THE BOTTOM AFTER ALL UI COMPONENTS EXIST
    # =====================================================================

    build_btn.click(
        fn=run_ingestion,
        inputs=[company_input, year_input, log_output],
        outputs=[log_output, md_download, chatbot, sources_output]
    )

    chat_input.submit(
        put_message_in_chatbot,
        inputs=[chat_input, chatbot],
        outputs=[chat_input, chatbot]
    ).then(
        chat,
        inputs=[chatbot, company_input, year_input],
        outputs=[chatbot, sources_output]
    )

print("2 - UI Built Successfully!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))

    print(f"3 - Launching Gradio on port {port}...")
    demo.launch(

        theme=theme,
        inbrowser=False
    )