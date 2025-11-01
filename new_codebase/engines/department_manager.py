# engines/department_manager.py
"""
DepartmentManager for Corporate Decision Simulator

Provides a centralized way to access and manage department data. It supports
lookups by department ID or name and includes methods for updating department
morale and tracking historical changes.
"""

class DepartmentManager:
    def __init__(self, departments_data):
        """
        Initializes the DepartmentManager.

        Args:
            departments_data (dict or list): Can be a dictionary with a 'departments' key
                                           or a direct list of department dictionaries.
        """
        if isinstance(departments_data, dict):
            self._departments = departments_data.get('departments', [])
        elif isinstance(departments_data, list):
            self._departments = departments_data
        else:
            self._departments = []

        self._id_index = {}
        self._name_index = {}
        for dept in self._departments:
            if 'id' in dept:
                self._id_index[dept['id']] = dept
            if 'name' in dept:
                self._name_index[dept['name']] = dept

    def get_by_id(self, department_id):
        """Retrieves a department by its unique ID."""
        return self._id_index.get(department_id)

    def get_by_name(self, department_name):
        """Retrieves a department by its name (for legacy or display purposes)."""
        return self._name_index.get(department_name)

    def get_all(self):
        """Returns a list of all department dictionaries."""
        return self._departments

    def to_dict(self):
        """Serializes the manager's data to a dictionary for saving."""
        return {"departments": self._departments}

    def update_morale(self, department_id_or_name, change):
        """
        Updates the morale of a specified department.

        Args:
            department_id_or_name (str): The ID or name of the department.
            change (int): The amount to change the morale by (positive or negative).

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        department = self.get_by_id(department_id_or_name) or self.get_by_name(department_id_or_name)
        if department:
            current_morale = department.get('morale', 60)
            department['morale'] = max(0, min(100, current_morale + change))
            return True
        return False

    def __len__(self):
        return len(self._departments)

    def __iter__(self):
        return iter(self._departments)

    def get_department_bonuses(self, game_state):
        """
        Calculates passive mechanical effects based on the morale of key departments.
        High morale in certain departments can provide company-wide bonuses, while
        low morale can introduce penalties.

        Returns:
            dict: A dictionary of calculated bonuses/penalties.
        """
        bonuses = {
            'budget_multiplier': 1.0, # Affects revenue generation
            'innovation_points': 0,   # Affects R&D/product development
            'morale_modifier': 0      # Affects overall company morale
        }

        for dept in self._departments:
            dept_name = dept.get('name', '').lower()
            morale = dept.get('morale', 60)

            # Sales department's impact on revenue
            if 'sales' in dept_name:
                if morale >= 80:
                    bonuses['budget_multiplier'] *= 1.15  # +15% revenue
                elif morale < 40:
                    bonuses['budget_multiplier'] *= 0.85  # -15% revenue

            # Engineering department's impact on innovation
            if 'engineering' in dept_name or 'r&d' in dept_name:
                if morale >= 80:
                    bonuses['innovation_points'] += 10
                elif morale < 40:
                    bonuses['innovation_points'] -= 10

            # HR department's impact on company morale
            if 'human resources' in dept_name or 'hr' in dept_name:
                if morale >= 80:
                    bonuses['morale_modifier'] += 5
                elif morale < 40:
                    bonuses['morale_modifier'] -= 10

        return bonuses

    def add_history_entry(self, department_id_or_name, reason, change, turn_number):
        """
        Adds a historical entry to a department's record to track morale changes.

        Args:
            department_id_or_name (str): The ID or name of the department.
            reason (str): A human-readable reason for the morale change.
            change (int): The amount the morale changed.
            turn_number (int): The current turn number.

        Returns:
            bool: True if the entry was added, False otherwise.
        """
        department = self.get_by_id(department_id_or_name) or self.get_by_name(department_id_or_name)
        if department:
            history = department.setdefault('history', [])
            entry = f"Quarter {turn_number}: {reason} ({change:+d} morale)"
            history.append(entry)
            # Keep the last 10 entries for brevity
            department['history'] = history[-10:]
            return True
        return False
