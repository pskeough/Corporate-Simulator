"""
History Compression Engine - Archives important historical events and decrees
Compresses long-term history while preserving civilization-defining moments
"""

import json
from typing import List, Dict, Any


class HistoryCompressionEngine:
    """Manages compression and archival of historical events"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.current_year = game_state.current_year

    def compress_history(self, events: List[Dict[str, Any]], current_era: str) -> Dict[str, Any]:
        """
        Compress a list of historical events into era-based archives

        Args:
            events: List of event dicts with year, title, action, narrative
            current_era: Current game era

        Returns:
            Compressed history structure
        """
        if not events:
            return self._get_empty_compressed_history()

        # Load existing compressed history
        compressed = self._load_compressed_history()

        # Categorize events by importance
        categorized = self._categorize_events(events)

        # Group into eras (50-year periods for now, 500-year for timeskips)
        era_groups = self._group_by_era(categorized)

        # Add to compressed history
        for era_data in era_groups:
            compressed['eras'].append(era_data)

        # Update metadata
        compressed['last_compression_year'] = self.current_year
        compressed['total_events_compressed'] = compressed.get('total_events_compressed', 0) + len(events)

        return compressed

    def _load_compressed_history(self) -> Dict[str, Any]:
        """Load existing compressed history or create empty structure"""
        try:
            import os
            context_path = self.game_state.context_path
            compressed_path = os.path.join(context_path, 'history_compressed.json')

            if os.path.exists(compressed_path):
                with open(compressed_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Could not load compressed history: {e}")

        return self._get_empty_compressed_history()

    def _get_empty_compressed_history(self) -> Dict[str, Any]:
        """Create empty compressed history structure"""
        return {
            'eras': [],
            'last_compression_year': 0,
            'total_events_compressed': 0,
            'civilization_defining_moments': []
        }

    def _categorize_events(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize events by importance level

        Returns dict with keys: civilization_defining, major, significant, minor
        """
        categorized = {
            'civilization_defining': [],
            'major': [],
            'significant': [],
            'minor': []
        }

        for event in events:
            importance = self._assess_event_importance(event)
            categorized[importance].append({
                **event,
                'importance': importance
            })

        return categorized

    def _assess_event_importance(self, event: Dict[str, Any]) -> str:
        """
        Assess the importance of a historical event

        Returns: 'civilization_defining', 'major', 'significant', or 'minor'
        """
        action = event.get('action', '').lower()
        title = event.get('title', '').lower()
        narrative = event.get('narrative', '').lower()
        combined = action + ' ' + title + ' ' + narrative

        score = 0

        # Check for permanent decree indicators
        decree_keywords = ['forever', 'eternal', 'holy law', 'decree', 'mandate', 'constitution']
        score += sum(5 for keyword in decree_keywords if keyword in combined)

        # Check for major structural changes
        structural_keywords = ['reform', 'revolution', 'new era', 'fundamental', 'transformation']
        score += sum(4 for keyword in structural_keywords if keyword in combined)

        # Check for war/peace
        conflict_keywords = ['war', 'peace treaty', 'alliance', 'conquest', 'defeat']
        score += sum(3 for keyword in conflict_keywords if keyword in combined)

        # Check for cultural/religious changes
        cultural_keywords = ['tradition', 'belief', 'religion', 'culture', 'values']
        score += sum(3 for keyword in cultural_keywords if keyword in combined)

        # Check for technological breakthroughs
        tech_keywords = ['discover', 'invent', 'breakthrough', 'advancement', 'innovation']
        score += sum(3 for keyword in tech_keywords if keyword in combined)

        # Length indicates substantive action
        if len(action) > 200:
            score += 5
        elif len(action) > 100:
            score += 2

        # Categorize based on score
        if score >= 20:
            return 'civilization_defining'
        elif score >= 12:
            return 'major'
        elif score >= 6:
            return 'significant'
        else:
            return 'minor'

    def _group_by_era(self, categorized: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Group categorized events into era structures

        Returns list of era dicts
        """
        all_events = []
        for importance, events in categorized.items():
            all_events.extend(events)

        if not all_events:
            return []

        # Sort by year
        all_events.sort(key=lambda e: e.get('year', 0))

        # Group into eras (we'll define eras by 50-year spans for regular play)
        eras = []
        current_era_events = []
        era_start = None

        for event in all_events:
            year = event.get('year', 0)

            if era_start is None:
                era_start = year

            # Check if we need to start a new era (50 year spans)
            if year - era_start > 50 and current_era_events:
                # Close current era
                eras.append(self._create_era_summary(era_start, year - 1, current_era_events))
                current_era_events = []
                era_start = year

            current_era_events.append(event)

        # Add final era
        if current_era_events:
            final_year = current_era_events[-1].get('year', era_start)
            eras.append(self._create_era_summary(era_start, final_year, current_era_events))

        return eras

    def _create_era_summary(self, start_year: int, end_year: int, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary for an era"""
        # Extract only the most important events for the summary
        civ_defining = [e for e in events if e.get('importance') == 'civilization_defining']
        major = [e for e in events if e.get('importance') == 'major']
        significant = [e for e in events if e.get('importance') == 'significant']

        # Generate era name based on most important event
        era_name = self._generate_era_name(civ_defining + major, start_year, end_year)

        defining_events = []

        # Always include civilization-defining events
        for event in civ_defining:
            defining_events.append({
                'year': event['year'],
                'importance': event['importance'],
                'type': self._classify_event_type(event),
                'title': event['title'],
                'summary': event.get('action', '')[:200] + '...' if len(event.get('action', '')) > 200 else event.get('action', ''),
                'lasting_effects': True
            })

        # Include major events (up to 3)
        for event in major[:3]:
            defining_events.append({
                'year': event['year'],
                'importance': event['importance'],
                'type': self._classify_event_type(event),
                'title': event['title'],
                'summary': event.get('action', '')[:150] + '...' if len(event.get('action', '')) > 150 else event.get('action', ''),
                'lasting_effects': self._has_lasting_effects(event)
            })

        return {
            'name': era_name,
            'start_year': start_year,
            'end_year': end_year,
            'total_events': len(events),
            'defining_events': defining_events,
            'era_character': self._describe_era_character(events)
        }

    def _generate_era_name(self, important_events: List[Dict[str, Any]], start_year: int, end_year: int) -> str:
        """Generate a descriptive name for the era"""
        if not important_events:
            return f"The Years {start_year}-{end_year}"

        # Use the most important event to name the era
        first_event = important_events[0]
        title = first_event.get('title', '')

        # Extract key themes
        action = first_event.get('action', '').lower()

        if 'divine' in action or 'holy' in action or 'sacred' in action:
            return f"The Age of Divine Decree (Years {start_year}-{end_year})"
        elif 'war' in action or 'conquest' in action or 'battle' in action:
            return f"The Age of Conflict (Years {start_year}-{end_year})"
        elif 'peace' in action or 'harmony' in action:
            return f"The Age of Peace (Years {start_year}-{end_year})"
        elif 'reform' in action or 'change' in action:
            return f"The Age of Transformation (Years {start_year}-{end_year})"
        else:
            # Use part of the title
            short_title = ' '.join(title.split()[:3])
            return f"The Era of {short_title} (Years {start_year}-{end_year})"

    def _classify_event_type(self, event: Dict[str, Any]) -> str:
        """Classify the type of event"""
        combined = (event.get('action', '') + ' ' + event.get('title', '')).lower()

        if any(k in combined for k in ['holy law', 'divine', 'sacred mandate']):
            return 'holy_law'
        elif any(k in combined for k in ['constitution', 'government reform']):
            return 'constitutional'
        elif any(k in combined for k in ['war', 'battle', 'conquest']):
            return 'military'
        elif any(k in combined for k in ['peace', 'treaty', 'alliance']):
            return 'diplomatic'
        elif any(k in combined for k in ['tradition', 'culture', 'belief']):
            return 'cultural'
        elif any(k in combined for k in ['discover', 'invent', 'technology']):
            return 'technological'
        elif any(k in combined for k in ['religion', 'temple', 'priest']):
            return 'religious'
        else:
            return 'general'

    def _has_lasting_effects(self, event: Dict[str, Any]) -> bool:
        """Determine if an event has lasting effects"""
        action = event.get('action', '').lower()
        permanence_keywords = ['forever', 'eternal', 'always', 'permanently', 'established', 'decree', 'law']
        return any(keyword in action for keyword in permanence_keywords)

    def _describe_era_character(self, events: List[Dict[str, Any]]) -> str:
        """Generate a brief description of the era's overall character"""
        if not events:
            return "A quiet period in history"

        # Count event types
        type_counts = {}
        for event in events:
            event_type = self._classify_event_type(event)
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        # Find dominant theme
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else 'general'

        descriptions = {
            'holy_law': "An era of religious transformation and divine mandate",
            'constitutional': "A period of governmental reform and structural change",
            'military': "A time marked by warfare and military expansion",
            'diplomatic': "An age of diplomacy, alliances, and political maneuvering",
            'cultural': "A flourishing of cultural development and tradition",
            'technological': "An era of innovation and technological advancement",
            'religious': "A time of spiritual growth and religious devotion",
            'general': "A period of varied developments and general growth"
        }

        return descriptions.get(dominant_type, "A dynamic period in civilization's history")

    def archive_decree(self, decree: Dict[str, Any]) -> None:
        """
        Immediately archive a civilization-defining decree

        Args:
            decree: The permanent decree to archive
        """
        compressed = self._load_compressed_history()

        # Add to civilization-defining moments
        if 'civilization_defining_moments' not in compressed:
            compressed['civilization_defining_moments'] = []

        moment = {
            'year': decree['declared_year'],
            'type': decree['type'],
            'title': decree['title'],
            'declared_by': decree['declared_by'],
            'summary': decree['declaration_text'][:300] + '...' if len(decree['declaration_text']) > 300 else decree['declaration_text'],
            'decree_id': decree['id'],
            'importance': decree['importance'],
            'archived_year': self.current_year
        }

        compressed['civilization_defining_moments'].append(moment)

        # Save compressed history
        self._save_compressed_history(compressed)

    def _save_compressed_history(self, compressed: Dict[str, Any]) -> None:
        """Save compressed history to disk"""
        try:
            import os
            context_path = self.game_state.context_path
            compressed_path = os.path.join(context_path, 'history_compressed.json')

            with open(compressed_path, 'w', encoding='utf-8') as f:
                json.dump(compressed, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving compressed history: {e}")

    def get_compressed_summary(self, max_eras: int = 5) -> str:
        """
        Get a formatted summary of compressed history for AI context

        Args:
            max_eras: Maximum number of recent eras to include

        Returns:
            Formatted string summarizing compressed history
        """
        compressed = self._load_compressed_history()

        if not compressed.get('eras') and not compressed.get('civilization_defining_moments'):
            return "No compressed history available."

        lines = ["=== COMPRESSED HISTORICAL ARCHIVE ===\n"]

        # Include civilization-defining moments first
        if compressed.get('civilization_defining_moments'):
            lines.append("CIVILIZATION-DEFINING MOMENTS:")
            for moment in compressed['civilization_defining_moments'][-5:]:  # Last 5
                lines.append(f"  • Year {moment['year']}: {moment['title']}")
                lines.append(f"    ({moment['type']}, declared by {moment['declared_by']})")
            lines.append("")

        # Include recent eras
        if compressed.get('eras'):
            recent_eras = compressed['eras'][-max_eras:]
            lines.append("RECENT HISTORICAL ERAS:")
            for era in recent_eras:
                lines.append(f"\n  {era['name']}")
                lines.append(f"  Character: {era['era_character']}")
                if era.get('defining_events'):
                    lines.append("  Key Events:")
                    for event in era['defining_events'][:3]:  # Top 3 per era
                        lines.append(f"    - Year {event['year']}: {event['title']} ({event['type']})")

        return "\n".join(lines)
