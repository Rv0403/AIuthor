# Editor

## Purpose
Polish chapter prose for readability, pacing, and tonal consistency without altering factual claims.

## Inputs
| Field | Source |
|-------|--------|
| `chapter_text` | Humanizer `humanized_text` |
| `book_title`, `chapter_number` | Outline / state |

## Outputs
| Field | Use |
|-------|-----|
| `edited_text` | Fact checker input |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Fact alteration | “Do not change factual claims” |
| Over-cutting voice | Humanizer already set voice; editor focuses transitions/pacing |
| Generic smoothing | “Remove awkward phrasing” not “simplify to bland” |

## Why this prompt
- **Separation of concerns**: Humanizer owns voice; editor owns structure—mirrors editorial workflow in publishing.
- **Lightweight template**: Short prompt reduces tokens in split mode where five agents run per chapter.
- **Book-level consistency**: `book_title` + chapter number anchor cross-chapter tone.

## Full prompt
See [prompts/editor.txt](../prompts/editor.txt)
