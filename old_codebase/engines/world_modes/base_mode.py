"""
Base World Mode Abstract Class

This module defines the abstract base class for all world generation modes.
Each mode must implement specific methods for generating civilizations, factions,
geography, and other world elements.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple


class WorldMode(ABC):
    """Abstract base class for world generation modes."""

    @abstractmethod
    def get_era_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Return era configurations for this mode.

        Returns:
            Dict mapping era names to configuration dictionaries
        """
        pass

    @abstractmethod
    def get_terrain_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Return terrain configurations for this mode.

        Returns:
            Dict mapping terrain types to configuration dictionaries
        """
        pass

    @abstractmethod
    def get_culture_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Return culture templates for this mode.

        Returns:
            Dict mapping culture types to template dictionaries
        """
        pass

    @abstractmethod
    def get_religion_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Return religion configurations for this mode.

        Returns:
            Dict mapping religion types to configuration dictionaries
        """
        pass

    @abstractmethod
    def get_social_structures(self) -> Dict[str, Dict[str, Any]]:
        """
        Return social structure configurations for this mode.

        Returns:
            Dict mapping social structure types to configuration dictionaries
        """
        pass

    @abstractmethod
    def generate_factions(self, era: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate appropriate factions for this mode based on era and config.

        Args:
            era: The current era (e.g., 'stone_age', 'classical')
            config: Configuration dictionary with user choices

        Returns:
            List of faction dictionaries
        """
        pass

    @abstractmethod
    def generate_geography(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate world geography for this mode.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Dictionary with geography details
        """
        pass

    @abstractmethod
    def get_starting_year(self, era: str) -> int:
        """
        Get appropriate starting year for the given era.

        Args:
            era: The era name

        Returns:
            Starting year (negative for BCE)
        """
        pass

    @abstractmethod
    def generate_civilization(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the player's civilization data.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Civilization data dictionary
        """
        pass

    @abstractmethod
    def generate_culture(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate culture data.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Culture data dictionary
        """
        pass

    @abstractmethod
    def generate_religion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate religion data.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Religion data dictionary
        """
        pass

    @abstractmethod
    def generate_technology(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate technology data.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Technology data dictionary
        """
        pass

    @abstractmethod
    def generate_world_context(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate world context data.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            World context dictionary
        """
        pass

    @abstractmethod
    def generate_inner_circle(self, config: Dict[str, Any], factions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate inner circle advisors.

        Args:
            config: Configuration dictionary with user choices
            factions: List of faction dictionaries

        Returns:
            List of inner circle member dictionaries
        """
        pass

    def generate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main generation method that coordinates all world generation.

        Args:
            config: Configuration dictionary with user choices

        Returns:
            Complete world data dictionary
        """
        # Generate all components
        civilization = self.generate_civilization(config)
        culture = self.generate_culture(config)
        religion = self.generate_religion(config)
        technology = self.generate_technology(config)
        world_context = self.generate_world_context(config)
        factions = self.generate_factions(config.get('starting_era', 'stone_age'), config)
        inner_circle = self.generate_inner_circle(config, factions)

        return {
            'civilization': civilization,
            'culture': culture,
            'religion': religion,
            'technology': technology,
            'world_context': world_context,
            'factions': factions,
            'inner_circle': inner_circle
        }

