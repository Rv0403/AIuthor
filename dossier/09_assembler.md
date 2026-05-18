# Assembler

## Purpose
Generate all front and back matter in the book’s tone, merge with chapter bodies, and export PDF/DOCX plus `manifest.json`.

## Inputs
| Field | Source |
|-------|--------|
| `title`, `topic`, `reader` | Outline / brief |
| `tone_block` | Memory tone fingerprint |
| `chapter_titles` | Completed chapters |
| `glossary_preview` | Memory glossary terms |

## Outputs
| Field | Use |
|-------|-----|
| `BookManifest` JSON | `file_generator` → PDF, DOCX |
| Half-title, copyright, dedication, epigraph, foreword, preface, acknowledgments, introduction, afterword, appendix, glossary, references, about_author, back_cover_copy | Publication surfaces |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Generic back matter ignoring tone | “Tone MUST cascade to every surface” |
| Invented real ISBNs | Placeholder `978-0-000000-00-0` in prompt example only |
| JSON schema drift | `invoke_structured` + manifest schema |
| Glossary mismatch | `glossary_preview` from memory |

## Why this prompt
- **Tonality beyond chapters**: Assessment requires tone on preface, glossary, back cover—not just chapter bodies.
- **Structured manifest**: One JSON blob drives deterministic PDF/DOCX layout.
- **Explicit surface list**: Mirrors `front_matter_plan` / `back_matter_plan` from planner.
- **Glossary in voice**: Definitions must match tone (Conversational friend vs Academic precision).

## Full prompt
See [prompts/assembler.txt](../prompts/assembler.txt)
