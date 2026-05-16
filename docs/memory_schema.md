# Memory Schema

## FactRecord

```json
{
  "fact_id": "F001",
  "fact": "Emergency funds should cover 3-6 months of expenses",
  "source": "personal_finance_basics.txt",
  "used_in": [1, 2]
}
```

## CharacterRecord

```json
{
  "name": "Arjun",
  "traits": ["introverted", "curious"],
  "relationships": ["Maya"],
  "notes": "Protagonist; carries coffee metaphor from Ch.2"
}
```

## CallbackRecord

```json
{
  "callback_id": "CB002",
  "callback_text": "remember the coffee analogy — small daily savings add up",
  "introduced_in": 2,
  "used_in": [5, 7]
}
```

## GlossaryTerm

```json
{
  "term": "Emergency fund",
  "definition": "Cash you keep untouched for surprises — think of it as your financial airbag.",
  "introduced_in": 1,
  "chapter_refs": [1, 4]
}
```

## ToneFingerprint

```json
{
  "tone": "Conversational",
  "rules": [
    "Speak directly to the reader using you",
    "Use simple, everyday language"
  ],
  "exemplar_snippets": []
}
```

## DecisionLogEntry

```json
{
  "agent": "memory_keeper",
  "decision": "chapter_memory_commit",
  "rationale": "Stored facts and callbacks for chapter 3",
  "chapter_ref": 3
}
```

## BookMemory (aggregate)

All stores live in `outputs/{run_id}/memory.json` and are read/written by Memory Keeper each chapter.
