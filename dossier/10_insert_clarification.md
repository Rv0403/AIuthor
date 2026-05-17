# Insert Chapter Clarification

## Purpose
Ensure Test D–style inserts never guess `insert_after=4` when the user omits or invalidates the insert position.

## Flow
1. Intent Analyzer sets `task_type: insert_chapter` and `insert_after` (integer or null).
2. `load_source` loads snapshot and validates `1 <= insert_after < total_chapters`.
3. If invalid → `status: needs_clarification`, `clarification_message`, `pending_insert` (source run, chapter count, intent, original user_input).
4. LangGraph routes to END (no `prepare_insert` until clarified).
5. User supplies chapter in Streamlit chat or API retry with `insert_after`.
6. Workflow resumes from intent with pass-through when `insert_after` and `source_run_id` are preset.

## Accepted user replies
- `4`
- `after chapter 4`
- `between chapter 4 and 5`

## Related code
- `agents/insert_clarification.py`
- `graph/nodes.py` (`node_load_source`, `node_intent` pass-through)
- `ui/streamlit_app.py` (chat thread)
- `api/main.py` (`clarification_message`, `pending_insert`)
