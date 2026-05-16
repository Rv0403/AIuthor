# Assembler Agent

## Purpose
Generate all front/back matter in tone; export PDF and DOCX.

## Inputs
- title, tone_block, chapter list, glossary preview

## Outputs
- BookManifest JSON → PDF + DOCX

## Failure Modes
- Generic back matter → tone MUST cascade to all surfaces in prompt

## Full Prompt
See [prompts/assembler.txt](../prompts/assembler.txt)
