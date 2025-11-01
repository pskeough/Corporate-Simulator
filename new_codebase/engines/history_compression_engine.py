# engines/history_compression_engine.py
"""
History Compression Engine for Corporate Decision Simulator

Archives major corporate events, policy changes, and milestones to create a
persistent company history, analogous to an annual report's historical summary.
"""

import json
from typing import List, Dict, Any

class HistoryCompressionEngine:
    """Manages the archival of major corporate events."""

    def __init__(self, game_state):
        self.game_state = game_state
        self.current_quarter = game_state.simulation.get('current_fiscal_quarter', 'Q1')

    def archive_policy(self, policy: Dict[str, Any]) -> None:
        """
        Immediately archives a company-defining policy change.
        """
        compressed = self._load_compressed_history()

        if 'company_defining_moments' not in compressed:
            compressed['company_defining_moments'] = []

        moment = {
            'quarter': policy['enacted_quarter'],
            'type': 'policy_change',
            'title': policy['title'],
            'enacted_by': policy['enacted_by'],
            'summary': policy['enactment_text'],
            'policy_id': policy['id'],
            'importance': policy['importance'],
            'archived_quarter': self.current_quarter
        }

        compressed['company_defining_moments'].append(moment)
        self._save_compressed_history(compressed)

    def _load_compressed_history(self) -> Dict[str, Any]:
        """Loads the compressed history file or returns an empty structure."""
        try:
            with open(self.game_state.paths['history_compressed'], 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'company_defining_moments': []}

    def _save_compressed_history(self, compressed: Dict[str, Any]) -> None:
        """Saves the compressed history to its JSON file."""
        try:
            with open(self.game_state.paths['history_compressed'], 'w', encoding='utf-8') as f:
                json.dump(compressed, f, indent=4)
        except Exception as e:
            print(f"Error saving compressed history: {e}")
