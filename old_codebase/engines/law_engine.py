"""
Law Engine - Manages permanent decrees and their propagation through history
Ensures major player decisions (laws, holy mandates, constitutional changes) persist and evolve realistically
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class LawEngine:
    """Handles permanent decrees, their enforcement, and historical evolution"""

    DECREE_TYPES = {
        'holy_law': 'Divine mandate backed by religious authority',
        'constitutional': 'Fundamental governance structure change',
        'cultural': 'Major cultural or social restructuring',
        'military': 'Permanent military doctrine or organization',
        'economic': 'Foundational economic policy or structure',
        'religious': 'Religious practice or structure (non-divine)',
    }

    ENFORCEMENT_LEVELS = ['absolute', 'strong', 'moderate', 'weakening', 'nominal', 'defunct']

    IMPORTANCE_LEVELS = ['civilization_defining', 'major', 'significant', 'minor']

    def __init__(self, game_state):
        """Initialize the law engine with current game state"""
        self.game_state = game_state
        self.civilization = game_state.civilization
        self.religion = game_state.religion
        self.culture = game_state.culture
        self.current_year = game_state.current_year

    def create_decree(self,
                     decree_type: str,
                     title: str,
                     declaration_text: str,
                     declared_by: str,
                     effects: Dict[str, Any],
                     importance: str = 'major') -> Dict[str, Any]:
        """
        Create a new permanent decree

        Args:
            decree_type: Type of decree (holy_law, constitutional, cultural, etc.)
            title: Short title of the decree
            declaration_text: Full text of the declaration
            declared_by: Name/title of the character who declared it
            effects: Dictionary of specific effects this decree has
            importance: How important this decree is (civilization_defining, major, significant, minor)

        Returns:
            The created decree object
        """
        if decree_type not in self.DECREE_TYPES:
            decree_type = 'cultural'  # Default fallback

        if importance not in self.IMPORTANCE_LEVELS:
            importance = 'major'

        # Generate unique ID
        decree_id = f"decree_{self.current_year}_{len(self.civilization.get('permanent_decrees', []))}"

        decree = {
            'id': decree_id,
            'type': decree_type,
            'title': title,
            'declared_year': self.current_year,
            'declared_by': declared_by,
            'declaration_text': declaration_text,
            'importance': importance,
            'enforcement_level': 'absolute',  # Start at maximum enforcement
            'effects': effects,
            'historical_impact': [
                {
                    'year': self.current_year,
                    'event': f"Decree declared by {declared_by}",
                    'enforcement_level': 'absolute'
                }
            ],
            'resistance_level': 0,  # 0-100 scale of societal resistance
            'support_level': 100,   # 0-100 scale of societal support
            'schisms_caused': [],
            'modified_years': []
        }

        return decree

    def add_decree_to_state(self, decree: Dict[str, Any]) -> str:
        """
        Add a decree to the civilization state and apply its immediate effects

        Returns:
            Narrative description of the decree's immediate impact
        """
        # Initialize permanent_decrees if it doesn't exist
        if 'permanent_decrees' not in self.civilization:
            self.civilization['permanent_decrees'] = []

        self.civilization['permanent_decrees'].append(decree)

        # Apply immediate effects
        narrative = self._apply_decree_effects(decree, is_initial=True)

        return narrative

    def _apply_decree_effects(self, decree: Dict[str, Any], is_initial: bool = False) -> str:
        """
        Apply a decree's effects to the current game state

        Args:
            decree: The decree to apply
            is_initial: Whether this is the initial declaration (True) or ongoing enforcement (False)

        Returns:
            Narrative describing the effects
        """
        effects = decree.get('effects', {})
        narratives = []

        # Social structure changes
        if 'social_structure' in effects:
            old_structure = self.civilization.get('social_structure', 'tribal')
            new_structure = effects['social_structure']
            self.civilization['social_structure'] = new_structure

            if is_initial:
                narratives.append(f"The social structure transforms from {old_structure} to {new_structure}")
            else:
                narratives.append(f"The {new_structure} system remains firmly in place")

        # Cultural values
        if 'cultural_values' in effects:
            current_values = self.culture.get('values', [])
            for value in effects['cultural_values']:
                if value not in current_values:
                    current_values.append(value)
                    if is_initial:
                        narratives.append(f"'{value}' becomes a core cultural value")
            self.culture['values'] = current_values

        # Taboos
        if 'taboos' in effects:
            current_taboos = self.culture.get('taboos', [])
            for taboo in effects['taboos']:
                if taboo not in current_taboos:
                    current_taboos.append(taboo)
                    if is_initial:
                        narratives.append(f"'{taboo}' is now forbidden by law")
            self.culture['taboos'] = current_taboos

        # Traditions
        if 'traditions' in effects:
            current_traditions = self.culture.get('traditions', [])
            for tradition in effects['traditions']:
                if tradition not in current_traditions:
                    current_traditions.append(tradition)
                    if is_initial:
                        narratives.append(f"'{tradition}' becomes an enforced tradition")
            self.culture['traditions'] = current_traditions

        # Military composition
        if 'military_composition' in effects:
            # This would affect military units, but we'll store it as metadata
            self.civilization['military_doctrine'] = effects['military_composition']
            if is_initial:
                narratives.append(f"Military organization changes to: {effects['military_composition']}")

        # Property rights
        if 'property_rights' in effects:
            self.civilization['property_system'] = effects['property_rights']
            if is_initial:
                narratives.append(f"Property rights restructured: {effects['property_rights']}")

        # Governance changes
        if 'governance_structure' in effects:
            old_gov = self.civilization.get('government_type', 'chiefdom')
            self.civilization['government_type'] = effects['governance_structure']
            if is_initial:
                narratives.append(f"Government transforms from {old_gov} to {effects['governance_structure']}")

        # Religious effects (for holy laws)
        if decree['type'] == 'holy_law' and 'religious_effects' in effects:
            self._apply_religious_effects(decree, effects['religious_effects'], is_initial)
            if is_initial:
                narratives.append(f"Religious doctrine permanently altered by divine mandate")

        if not narratives:
            narratives.append("The decree's influence permeates society")

        return ". ".join(narratives) + "."

    def _apply_religious_effects(self, decree: Dict[str, Any], religious_effects: Dict[str, Any], is_initial: bool):
        """Apply effects specific to religious decrees"""
        # Add to holy laws in religion
        if 'holy_laws' not in self.religion:
            self.religion['holy_laws'] = []

        holy_law = {
            'law': decree['title'],
            'divine_authority': religious_effects.get('divine_authority', self.religion.get('primary_deity', 'The Divine')),
            'declared_year': decree['declared_year'],
            'sacred_status': 'absolute' if decree['enforcement_level'] == 'absolute' else 'revered',
            'decree_id': decree['id']
        }

        # Check if already exists
        existing = next((hl for hl in self.religion['holy_laws'] if hl.get('decree_id') == decree['id']), None)
        if not existing:
            self.religion['holy_laws'].append(holy_law)

        # Add core tenets
        if 'core_tenets' in religious_effects:
            current_tenets = self.religion.get('core_tenets', [])
            for tenet in religious_effects['core_tenets']:
                if tenet not in current_tenets:
                    current_tenets.append(tenet)
            self.religion['core_tenets'] = current_tenets

        # Modify practices
        if 'practices' in religious_effects:
            current_practices = self.religion.get('practices', [])
            for practice in religious_effects['practices']:
                if practice not in current_practices:
                    current_practices.append(practice)
            self.religion['practices'] = current_practices

    def enforce_active_decrees(self) -> List[str]:
        """
        Enforce all active decrees, ensuring their effects are reflected in current state
        Returns list of enforcement narratives
        """
        decrees = self.civilization.get('permanent_decrees', [])
        if not decrees:
            return []

        narratives = []

        for decree in decrees:
            # Skip defunct decrees
            if decree.get('enforcement_level') == 'defunct':
                continue

            # Re-apply effects based on enforcement level
            if decree.get('enforcement_level') in ['absolute', 'strong', 'moderate']:
                # Full enforcement
                self._apply_decree_effects(decree, is_initial=False)
            elif decree.get('enforcement_level') == 'weakening':
                # Partial enforcement - might be fading
                narratives.append(f"The decree '{decree['title']}' is weakening but still influences society")
            elif decree.get('enforcement_level') == 'nominal':
                # Barely enforced - mostly cultural memory
                narratives.append(f"The ancient decree '{decree['title']}' exists only in tradition")

        return narratives

    def evolve_decree(self, decree: Dict[str, Any], years_passed: int) -> str:
        """
        Evolve a decree over time based on cultural fit and resistance

        Args:
            decree: The decree to evolve
            years_passed: How many years have passed since last evolution

        Returns:
            Narrative describing how the decree evolved
        """
        current_enforcement = decree.get('enforcement_level', 'absolute')
        resistance = decree.get('resistance_level', 0)
        support = decree.get('support_level', 100)

        # Calculate cultural fit based on decree effects vs current culture
        cultural_fit = self._calculate_cultural_fit(decree)

        # Determine evolution direction
        if cultural_fit > 70 and support > 70:
            # Decree strengthens
            if current_enforcement == 'moderate':
                decree['enforcement_level'] = 'strong'
                return f"The decree '{decree['title']}' has become deeply rooted in society, enforcement strengthening"
            elif current_enforcement == 'weakening':
                decree['enforcement_level'] = 'moderate'
                return f"The decree '{decree['title']}' sees renewed support and enforcement"
        elif cultural_fit < 30 or resistance > 70:
            # Decree weakens
            enforcement_progression = ['absolute', 'strong', 'moderate', 'weakening', 'nominal', 'defunct']
            current_index = enforcement_progression.index(current_enforcement)
            if current_index < len(enforcement_progression) - 1:
                new_enforcement = enforcement_progression[current_index + 1]
                decree['enforcement_level'] = new_enforcement

                if new_enforcement == 'defunct':
                    return f"The decree '{decree['title']}' has fallen completely out of practice, now defunct"
                elif new_enforcement == 'nominal':
                    return f"The decree '{decree['title']}' is barely enforced, existing only in name"
                else:
                    return f"The decree '{decree['title']}' faces growing resistance, enforcement weakening"

        # Stable - minor adjustments
        decree['resistance_level'] = max(0, min(100, resistance + (50 - cultural_fit) // 10))
        decree['support_level'] = max(0, min(100, support + (cultural_fit - 50) // 10))

        return f"The decree '{decree['title']}' remains {current_enforcement} in enforcement"

    def _calculate_cultural_fit(self, decree: Dict[str, Any]) -> int:
        """
        Calculate how well a decree fits current cultural values (0-100)
        Higher = better fit = more likely to persist
        """
        fit_score = 50  # Neutral baseline

        effects = decree.get('effects', {})

        # Check if decree's cultural values match current culture
        if 'cultural_values' in effects:
            current_values = self.culture.get('values', [])
            matching_values = sum(1 for v in effects['cultural_values'] if v in current_values)
            fit_score += matching_values * 10

        # Check if decree's taboos are still taboo
        if 'taboos' in effects:
            current_taboos = self.culture.get('taboos', [])
            matching_taboos = sum(1 for t in effects['taboos'] if t in current_taboos)
            fit_score += matching_taboos * 10

        # Holy laws have inherent staying power if religion is strong
        if decree['type'] == 'holy_law':
            religious_influence = self.religion.get('influence', 'moderate')
            if religious_influence == 'dominant':
                fit_score += 20
            elif religious_influence == 'significant':
                fit_score += 10
            elif religious_influence == 'waning':
                fit_score -= 20

        # Importance affects staying power
        importance = decree.get('importance', 'major')
        if importance == 'civilization_defining':
            fit_score += 15
        elif importance == 'major':
            fit_score += 10

        return max(0, min(100, fit_score))

    def generate_resistance_events(self, decree: Dict[str, Any]) -> Optional[str]:
        """
        Generate events showing resistance or support for a decree
        Returns None if no significant events, or a narrative string
        """
        resistance = decree.get('resistance_level', 0)
        support = decree.get('support_level', 100)
        enforcement = decree.get('enforcement_level', 'absolute')

        # High resistance + strong enforcement = conflict events
        if resistance > 60 and enforcement in ['absolute', 'strong']:
            events = [
                f"Underground movements form to resist the '{decree['title']}' decree",
                f"Open protests erupt against the enforcement of '{decree['title']}'",
                f"Factions splinter over disagreement with '{decree['title']}'",
                f"A rebellion is brewing among those opposed to '{decree['title']}'"
            ]
            import random
            return random.choice(events)

        # High support + weakening enforcement = calls for renewal
        if support > 70 and enforcement in ['weakening', 'nominal']:
            events = [
                f"Religious leaders call for renewed enforcement of '{decree['title']}'",
                f"Traditionalists demand the ancient decree '{decree['title']}' be upheld",
                f"A movement forms to restore the sacred law '{decree['title']}'"
            ]
            import random
            return random.choice(events)

        return None

    def get_active_decrees(self, min_enforcement: str = 'weakening') -> List[Dict[str, Any]]:
        """
        Get all decrees that are still actively enforced

        Args:
            min_enforcement: Minimum enforcement level to include

        Returns:
            List of active decree objects
        """
        enforcement_hierarchy = ['absolute', 'strong', 'moderate', 'weakening', 'nominal', 'defunct']
        min_index = enforcement_hierarchy.index(min_enforcement)

        decrees = self.civilization.get('permanent_decrees', [])
        active = []

        for decree in decrees:
            enforcement = decree.get('enforcement_level', 'absolute')
            if enforcement_hierarchy.index(enforcement) <= min_index:
                active.append(decree)

        return active

    def get_decree_summary(self, decree: Dict[str, Any]) -> str:
        """Generate a concise summary of a decree for AI prompts"""
        return (
            f"{decree['title']} ({decree['type']}, {decree['declared_year']}): "
            f"{decree['declaration_text'][:100]}... "
            f"[Enforcement: {decree['enforcement_level']}, "
            f"Support: {decree.get('support_level', 100)}%, "
            f"Resistance: {decree.get('resistance_level', 0)}%]"
        )

    def get_all_decrees_summary(self) -> str:
        """Get a formatted summary of all active decrees for AI context"""
        active_decrees = self.get_active_decrees(min_enforcement='nominal')

        if not active_decrees:
            return "No permanent decrees currently in effect."

        summary_lines = ["=== PERMANENT DECREES IN EFFECT ==="]

        for decree in active_decrees:
            summary_lines.append(f"\n• {self.get_decree_summary(decree)}")

        return "\n".join(summary_lines)

    def process_timeskip(self, years_passed: int) -> Dict[str, Any]:
        """
        Process all decrees through a timeskip, evolving them realistically

        Args:
            years_passed: How many years have passed

        Returns:
            Dictionary containing:
                - evolved_decrees: List of how each decree changed
                - major_events: List of significant events caused by decrees
                - defunct_decrees: List of decrees that became defunct
                - new_schisms: List of religious schisms caused
        """
        decrees = self.civilization.get('permanent_decrees', [])

        result = {
            'evolved_decrees': [],
            'major_events': [],
            'defunct_decrees': [],
            'new_schisms': [],
            'decree_narratives': []
        }

        for decree in decrees:
            # Skip already defunct
            if decree.get('enforcement_level') == 'defunct':
                continue

            # Evolve the decree
            evolution_narrative = self.evolve_decree(decree, years_passed)
            result['evolved_decrees'].append({
                'decree': decree['title'],
                'narrative': evolution_narrative
            })

            # Check if it became defunct
            if decree.get('enforcement_level') == 'defunct':
                result['defunct_decrees'].append(decree['title'])

            # Generate resistance/support events
            event = self.generate_resistance_events(decree)
            if event:
                result['major_events'].append(event)

            # Check for schisms (especially for holy laws)
            if decree['type'] == 'holy_law' and decree.get('resistance_level', 0) > 50:
                schism_name = f"Reformist opposition to {decree['title']}"
                if schism_name not in decree.get('schisms_caused', []):
                    decree.setdefault('schisms_caused', []).append(schism_name)
                    result['new_schisms'].append(schism_name)

            # Add to historical impact
            decree.setdefault('historical_impact', []).append({
                'year': self.current_year,
                'event': evolution_narrative,
                'enforcement_level': decree.get('enforcement_level')
            })

            # Create summary for timeskip narrative
            if decree.get('enforcement_level') in ['absolute', 'strong', 'moderate']:
                result['decree_narratives'].append(
                    f"The {decree['type']} '{decree['title']}' (declared {decree['declared_year']}) "
                    f"continues to shape society with {decree['enforcement_level']} enforcement"
                )

        return result

