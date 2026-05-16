"""Structured memory schemas for cross-chapter continuity."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FactRecord(BaseModel):
    fact_id: str
    fact: str
    source: str = "retrieved_docs"
    used_in: list[int] = Field(default_factory=list)


class CharacterRecord(BaseModel):
    name: str
    traits: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    notes: str = ""


class CallbackRecord(BaseModel):
    callback_id: str
    callback_text: str
    introduced_in: int
    used_in: list[int] = Field(default_factory=list)


class GlossaryTerm(BaseModel):
    term: str
    definition: str
    introduced_in: int
    chapter_refs: list[int] = Field(default_factory=list)


class ToneFingerprint(BaseModel):
    tone: str
    rules: list[str] = Field(default_factory=list)
    exemplar_snippets: list[str] = Field(default_factory=list)


class DecisionLogEntry(BaseModel):
    agent: str
    decision: str
    rationale: str
    chapter_ref: int | None = None


class BookMemory(BaseModel):
    fact_registry: list[FactRecord] = Field(default_factory=list)
    character_bible: list[CharacterRecord] = Field(default_factory=list)
    callback_index: list[CallbackRecord] = Field(default_factory=list)
    glossary_terms: list[GlossaryTerm] = Field(default_factory=list)
    tone_fingerprint: ToneFingerprint | None = None
    decision_log: list[DecisionLogEntry] = Field(default_factory=list)

    def model_dump_json_safe(self) -> dict[str, Any]:
        return self.model_dump()


class MemorySnapshot(BaseModel):
    run_id: str
    memory: BookMemory
    outline: dict[str, Any] | None = None
    chapters: list[dict[str, Any]] = Field(default_factory=list)
    brief: dict[str, Any] | None = None


class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    summary: str
    target_words: int = 2500


class BookOutline(BaseModel):
    title: str
    subtitle: str = ""
    genre: str = "non-fiction"
    chapters: list[ChapterOutline]
    front_matter_plan: list[str] = Field(default_factory=list)
    back_matter_plan: list[str] = Field(default_factory=list)


class ChapterResearch(BaseModel):
    chapter_number: int
    facts: list[dict[str, str]] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    glossary_candidates: list[dict[str, str]] = Field(default_factory=list)


class ChapterContent(BaseModel):
    chapter_number: int
    title: str
    raw_text: str = ""
    humanized_text: str = ""
    edited_text: str = ""
    verified_text: str = ""
    word_count: int = 0


class BookManifest(BaseModel):
    title: str
    half_title: str = ""
    copyright_block: str = ""
    dedication: str = ""
    epigraph: str = ""
    foreword: str = ""
    preface: str = ""
    acknowledgments: str = ""
    introduction: str = ""
    chapters: list[dict[str, Any]] = Field(default_factory=list)
    afterword: str = ""
    appendix: str = ""
    glossary: dict[str, str] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)
    about_author: str = ""
    back_cover_copy: str = ""


class IntentResult(BaseModel):
    task_type: str
    topic: str = ""
    reader: str = ""
    tone: str = "Conversational"
    genre: str = "non-fiction"
    num_chapters: int = 10
    words_per_chapter: int = 2500
    target_chapter: int | None = None
    insert_after: int | None = None
    source_run_id: str | None = None
    character_names: list[str] = Field(default_factory=list)
    length: str = ""
