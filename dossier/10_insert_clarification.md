# Insert Chapter Clarification

## Purpose
Ensure Test D–style inserts never guess `insert_after=4` when the user omits or invalidates insert position. **No LLM prompt**—deterministic parsing and validation in code.

## Inputs
| Field | Source |
|-------|--------|
| User chat reply or API `insert_after` | Streamlit / `POST /execute` |
| `pending_insert` | Prior `needs_clarification` response |
| `source_run_id`, chapter count | Snapshot |

## Outputs
| Field | Use |
|-------|-----|
| Valid `insert_after` (1 ≤ n < total_chapters) | `prepare_insert` → repair → chapter pipeline |
| `needs_clarification` + `clarification_message` | END until resolved |

## Flow
1. Intent Analyzer sets `insert_chapter` and `insert_after` (integer or null).
2. `load_source` validates range.
3. If invalid → `status: needs_clarification`, graph END.
4. User supplies position; workflow resumes with preset `insert_after` / `source_run_id` (intent pass-through).

## Accepted user replies (regex)
- `4` · `after chapter 4` · `between chapter 4 and 5`

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Silent default to chapter 4 | No default in code; clarification required |
| Insert at last chapter | Validation rejects; user must pick valid gap |
| Stale chat thread | Streamlit **New chat** = new `run_id` / trace folder |

## Why no prompt
Clarification is **structured user input**, not generation. Regex + validation are faster, cheaper, and auditable than an LLM guessing chapter numbers.

## Implementation
- [agents/insert_clarification.py](../agents/insert_clarification.py)
- [graph/nodes.py](../graph/nodes.py) (`node_load_source`, intent pass-through)
- [ui/streamlit_app.py](../ui/streamlit_app.py) · [api/main.py](../api/main.py)
