# Fact Checker

## Purpose
Final chapter pass: verify claims against research, soften unverifiable statements, and block fabricated references.

## Inputs
| Field | Source |
|-------|--------|
| `chapter_text` | Editor `edited_text` |
| `verified_facts` | Researcher `facts` |
| `references` | Researcher `references` |

## Outputs
| Field | Use |
|-------|-----|
| `verified_text` | memory_keeper commit; assembler chapter body |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Over-softening accurate claims | Only soften when cannot verify |
| Invented ISBNs/papers | NEVER invent; abstain rule |
| New facts added in check | “Do not add new factual claims” |
| Empty research | Softens or removes bold claims |

## Why this prompt
- **Last line of defense**: Writer/humanizer may drift; checker aligned to research artifacts only.
- **Abstain over fabricate**: Matches researcher citation discipline for assessment trust.
- **Prose output**: Same contract as editor/humanizer for pipeline chaining.

## Full prompt
See [prompts/fact_checker.txt](../prompts/fact_checker.txt)
