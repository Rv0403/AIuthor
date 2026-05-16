"""Build prompts dossier PDF for submission."""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_pdf(output_path: Path | None = None) -> Path:
    root = Path(__file__).parent.parent
    dossier_dir = root / "dossier"
    out = output_path or (root / "dossier" / "AIuthor_Prompts_Dossier.pdf")

    doc = SimpleDocTemplate(str(out), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AIuthor — Prompts Dossier", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Gateway Digital AI Engineer Assessment", styles["Normal"]))
    story.append(Spacer(1, 24))

    for md_file in sorted(dossier_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            safe = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            if line.startswith("# "):
                story.append(Paragraph(safe[2:], styles["Heading1"]))
            elif line.startswith("## "):
                story.append(Paragraph(safe[3:], styles["Heading2"]))
            elif line.startswith("- "):
                story.append(Paragraph(f"• {safe[2:]}", styles["Normal"]))
            else:
                story.append(Paragraph(safe, styles["Normal"]))
        story.append(Spacer(1, 18))

    prompts_dir = root / "prompts"
    story.append(Paragraph("Appendix: Full Prompt Files", styles["Heading1"]))
    for prompt_file in sorted(prompts_dir.rglob("*.txt")):
        rel = prompt_file.relative_to(root)
        story.append(Paragraph(str(rel), styles["Heading2"]))
        content = prompt_file.read_text(encoding="utf-8")[:4000]
        for chunk in content.split("\n"):
            if chunk.strip():
                safe = chunk.replace("&", "&amp;").replace("<", "&lt;")
                story.append(Paragraph(safe, styles["Code"] if "Code" in styles else styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"Wrote {out}")
    return out


if __name__ == "__main__":
    build_pdf()
