"""KI-Prompt-Generator für Tasks.

Generates AI prompts with task context, PRD excerpts, and review comments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from v_flask.models import Config

if TYPE_CHECKING:
    from ..models import Task


class PromptGenerator:
    """Generate AI prompts for tasks with full context."""

    # Task type descriptions for prompt context
    TYP_BESCHREIBUNGEN = {
        "feature": "Neue Funktionalität implementieren",
        "bugfix": "Fehler beheben",
        "refactor": "Code-Struktur verbessern ohne Funktionsänderung",
        "docs": "Dokumentation erstellen oder aktualisieren",
        "test": "Tests schreiben oder verbessern",
        "chore": "Wartungsarbeit (Dependencies, Config, etc.)",
        "style": "Code-Formatierung ohne logische Änderungen",
        "perf": "Performance-Optimierung",
    }

    # Priority descriptions
    PRIORITAET_BESCHREIBUNGEN = {
        "niedrig": "Niedrige Priorität - kann warten",
        "mittel": "Normale Priorität",
        "hoch": "Hohe Priorität - bald erledigen",
        "kritisch": "Kritisch - sofort erledigen",
    }

    @classmethod
    def generate_task_prompt(cls, task: Task, include_prd: bool = True) -> str:
        """Generate a full AI prompt for a task.

        Args:
            task: The task to generate a prompt for
            include_prd: Whether to include PRD excerpt (default: True)

        Returns:
            Formatted prompt string ready for AI consumption
        """
        lines = []

        # Header
        lines.append(f"# Task: {task.task_nummer}")
        lines.append("")

        # Basic Info
        lines.append("## Übersicht")
        lines.append(f"- **Titel:** {task.titel}")
        lines.append(f"- **Komponente:** {task.komponente.name}")
        if task.komponente.prd_nummer:
            lines.append(f"- **PRD:** PRD-{task.komponente.prd_nummer}")

        # Type with description
        typ_beschreibung = cls.TYP_BESCHREIBUNGEN.get(task.typ, task.typ)
        lines.append(f"- **Typ:** {task.typ} ({typ_beschreibung})")

        # Priority with description
        prio_beschreibung = cls.PRIORITAET_BESCHREIBUNGEN.get(
            task.prioritaet, task.prioritaet
        )
        lines.append(f"- **Priorität:** {prio_beschreibung}")

        # Phase if set
        if task.phase:
            lines.append(f"- **Phase:** {task.phase.upper()}")

        lines.append("")

        # Task Description
        if task.beschreibung:
            lines.append("## Beschreibung")
            lines.append(task.beschreibung)
            lines.append("")

        # PRD Context (excerpt)
        if include_prd and task.komponente.prd_inhalt:
            prd_excerpt = cls._extract_prd_excerpt(task.komponente.prd_inhalt)
            if prd_excerpt:
                lines.append("## PRD-Kontext (Auszug)")
                lines.append(prd_excerpt)
                lines.append("")

        # Related task context
        if task.entstanden_aus:
            lines.append("## Kontext")
            lines.append(
                f"Dieser Task ist entstanden aus: {task.entstanden_aus_nummer}"
            )
            lines.append(f"Ursprünglicher Task: {task.entstanden_aus.titel}")
            lines.append("")

        # Suffix from settings
        suffix = cls._get_prompt_suffix(task.id)
        if suffix:
            lines.append("## Arbeitsanweisungen")
            lines.append(suffix)
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def generate_review_prompt(cls, task: Task) -> str:
        """Generate a review prompt for open review comments.

        Args:
            task: The task with review comments

        Returns:
            Formatted review prompt string
        """
        # Get open review comments
        offene_kommentare = [k for k in task.kommentare if not k.erledigt]

        if not offene_kommentare:
            return f"# Review: {task.task_nummer}\n\nKeine offenen Review-Kommentare."

        lines = []

        # Header
        lines.append(f"# Review: {task.task_nummer}")
        lines.append("")
        lines.append(f"**Task:** {task.titel}")
        lines.append(f"**Komponente:** {task.komponente.name}")
        lines.append("")

        # Open Comments
        lines.append(f"## Offene Kommentare ({len(offene_kommentare)})")
        lines.append("")

        for i, kommentar in enumerate(offene_kommentare, 1):
            typ_label = kommentar.typ.upper() if kommentar.typ else "KOMMENTAR"
            user_name = kommentar.user.vorname if kommentar.user else "System"

            lines.append(f"### {i}. [{typ_label}] von {user_name}")
            lines.append(kommentar.inhalt)
            lines.append("")

        # Instructions
        lines.append("## Anweisungen")
        lines.append("Bitte bearbeite die obigen Review-Kommentare und markiere sie ")
        lines.append("nach der Bearbeitung als erledigt.")
        lines.append("")

        # Task context
        if task.beschreibung:
            lines.append("## Ursprüngliche Task-Beschreibung")
            lines.append(task.beschreibung)
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _extract_prd_excerpt(cls, prd_inhalt: str, max_lines: int = 50) -> str:
        """Extract relevant excerpt from PRD content.

        Focuses on Übersicht and Features sections.

        Args:
            prd_inhalt: Full PRD markdown content
            max_lines: Maximum lines to include

        Returns:
            Extracted PRD excerpt
        """
        if not prd_inhalt:
            return ""

        lines = prd_inhalt.split("\n")
        excerpt_lines = []
        in_relevant_section = False
        section_count = 0

        for line in lines:
            # Check for relevant sections
            if line.startswith("## "):
                section_lower = line.lower()
                if any(
                    s in section_lower
                    for s in ["übersicht", "features", "anforderungen", "ziel"]
                ):
                    in_relevant_section = True
                    section_count += 1
                else:
                    if in_relevant_section and section_count >= 2:
                        break  # Stop after 2 relevant sections
                    in_relevant_section = False

            if in_relevant_section:
                excerpt_lines.append(line)

            if len(excerpt_lines) >= max_lines:
                excerpt_lines.append("...")
                break

        # If no relevant sections found, return first part
        if not excerpt_lines and lines:
            excerpt_lines = lines[:max_lines]
            if len(lines) > max_lines:
                excerpt_lines.append("...")

        return "\n".join(excerpt_lines)

    @classmethod
    def _get_prompt_suffix(cls, task_id: int) -> str:
        """Get prompt suffix from config, replacing placeholders.

        Args:
            task_id: Task ID for placeholder replacement

        Returns:
            Processed prompt suffix string
        """
        suffix = Config.get_value("projektverwaltung.ki_prompt_suffix", "")
        if suffix:
            suffix = suffix.replace("{task_id}", str(task_id))
        return suffix
