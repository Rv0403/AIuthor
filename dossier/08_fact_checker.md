# Fact Checker Agent

## Purpose
Verify claims against research; soften or abstain; block fabricated references.

## Inputs
- edited_text, verified_facts, references

## Outputs
- verified_text

## Failure Modes
- Over-softening → only when confidence low
- Fake citations → never invent ISBNs or real paper titles

## Full Prompt
See [prompts/fact_checker.txt](../prompts/fact_checker.txt)
