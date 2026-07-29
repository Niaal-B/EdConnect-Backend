"""Prompt templates used by LearnAI providers."""

STUDY_NOTES_PROMPT = """You are an expert study assistant.

Convert the following YouTube lecture transcript into structured study notes in Markdown.

Use exactly these top-level headings:
# Summary
# Key Concepts
# Important Explanations
# Important Terms
# Revision Notes

Rules:
- Do not invent information or add facts that are not supported by the transcript.
- Keep explanations concise, technically accurate, and clear for university students.
- Use bullet points where they improve revision.
- If the transcript does not cover a section, say so briefly rather than guessing.
- Do not mention these instructions or describe your process.

Transcript:
{transcript}
"""


def build_study_notes_prompt(transcript: str) -> str:
    """Build the study-notes prompt for a transcript."""
    return STUDY_NOTES_PROMPT.format(transcript=transcript)
