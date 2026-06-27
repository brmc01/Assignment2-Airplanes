
import os
import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(ROOT, "Documentation.pdf")
SUMMARY = os.path.join(ROOT, "output", "summary.png")

summary_html = (
    f'<p class="cap">summary.png: clean -&gt; noisy -&gt; denoised, the template, '
    f'the Cr spectrum before/after the notch, the match heatmap, and the detections.</p>'
    f'<img src="summary.png" width="600">'
    if os.path.exists(SUMMARY) else
    '<p><i>Run main.py first to generate output/summary.png.</i></p>'
)

HTML = f"""
<html>
<head><style>
  body  {{ font-family: serif; font-size: 11pt; color: #000; line-height: 1.4; }}
  h1    {{ font-size: 19pt; margin-bottom: 1px; }}
  h2    {{ font-size: 13.5pt; margin-top: 20px; margin-bottom: 4px; }}
  h3    {{ font-size: 11.5pt; margin-top: 13px; margin-bottom: 2px; }}
  .sub  {{ font-size: 10.5pt; color: #444; margin-top: 0; }}
  code  {{ font-family: monospace; }}
  pre   {{ font-family: monospace; background: #f3f3f3; padding: 7px;
           font-size: 9pt; white-space: pre; }}
  table {{ border-collapse: collapse; font-size: 10pt; }}
  th, td {{ border: 1px solid #aaa; padding: 4px 7px; text-align: left;
           vertical-align: top; }}
  th    {{ font-weight: bold; }}
  .cap  {{ font-size: 9pt; color: #555; font-style: italic; margin-bottom: 3px; }}
</style></head>
<body>
{summary_html}
</body>
</html>
"""

def build():
    archive = fitz.Archive(os.path.join(ROOT, "output")) if os.path.exists(SUMMARY) else None
    story = fitz.Story(html=HTML, archive=archive)
    writer = fitz.DocumentWriter(OUT_PDF)

    mediabox = fitz.paper_rect("a4")
    where = mediabox + (48, 48, -48, -55)

    more = 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    build()