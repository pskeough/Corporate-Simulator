# engines/policy_engine.py
"""
Policy Engine for Corporate Decision Simulator

Manages the creation, enforcement, and evolution of corporate policies,
ensuring that major decisions have a lasting and realistic impact on the company.
"""

from typing import Dict, Any

class PolicyEngine:
    """Handles corporate policies, their enforcement, and cultural impact."""

    def __init__(self, game_state):
        self.game_state = game_state
        self.corporation = game_state.corporation
        self.company_culture = game_state.company_culture
        self.current_quarter = game_state.simulation.get('current_fiscal_quarter', 'Q1')

    def create_policy(self,
                     policy_type: str,
                     title: str,
                     enactment_text: str,
                     enacted_by: str,
                     effects: Dict[str, Any],
                     importance: str = 'major') -> Dict[str, Any]:
        """Creates a new corporate policy."""
        policy_id = f"policy_{self.current_quarter}_{len(self.corporation.get('policies', []))}"

        policy = {
            'id': policy_id,
            'type': policy_type,
            'title': title,
            'enacted_quarter': self.current_quarter,
            'enacted_by': enacted_by,
            'enactment_text': enactment_text,
            'importance': importance,
            'enforcement_level': 'fully_enforced',  # e.g., 'fully_enforced', 'partially_observed', 'largely_ignored'
            'effects': effects,
            'historical_impact': [],
            'employee_buy_in': 100,  # 0-100 scale
        }
        return policy

    def add_policy_to_state(self, policy: Dict[str, Any]) -> str:
        """Adds a policy to the state and applies its immediate effects."""
        if 'policies' not in self.corporation:
            self.corporation['policies'] = []
        self.corporation['policies'].append(policy)
        return self._apply_policy_effects(policy, is_initial=True)

    def _apply_policy_effects(self, policy: Dict[str, Any], is_initial: bool = False) -> str:
        """Applies a policy's effects to the current game state."""
        effects = policy.get('effects', {})
        narratives = []

        if 'hiring_status' in effects:
            self.corporation['hiring_status'] = effects['hiring_status']
            if is_initial:
                narratives.append(f"A company-wide {effects['hiring_status']} is now in effect.")

        if 'work_policy' in effects:
            self.company_culture['work_policy'] = effects['work_policy']
            if is_initial:
                narratives.append(f"The company has adopted a new '{effects['work_policy']}' work policy.")

        if 'unspoken_rules' in effects:
            current_rules = self.company_culture.get('unspoken_rules', [])
            for rule in effects['unspoken_rules']:
                if rule not in current_rules:
                    current_rules.append(rule)
                    if is_initial:
                        narratives.append(f"A new unspoken rule has emerged: '{rule}'.")
            self.company_culture['unspoken_rules'] = current_rules

        return ". ".join(narratives) + "." if narratives else "The new policy is now in effect."

    def evolve_policy(self, policy: Dict[str, Any]) -> str:
        """Evolves a policy over time based on employee buy-in and company culture."""
        buy_in = policy.get('employee_buy_in', 100)

        # Simulate decay of unpopular policies
        if buy_in < 40:
            if policy['enforcement_level'] == 'fully_enforced':
                policy['enforcement_level'] = 'partially_observed'
                return f"The '{policy['title']}' policy is now only partially observed as employee buy-in wanes."
            elif policy['enforcement_level'] == 'partially_observed':
                policy['enforcement_level'] = 'largely_ignored'
                return f"The '{policy['title']}' policy is now largely ignored by employees."

        return f"The '{policy['title']}' policy remains {policy['enforcement_level'].replace('_', ' ')}."
