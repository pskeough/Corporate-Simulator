"""
Historical Earth Mode

This mode provides historical Earth simulation with realistic geography, cultures,
and the ability to diverge from history through player actions (butterfly effects).

Features:
- Stone Age/Bronze Age/Iron Age starts: Butterfly effect mode with proto-civilizations
- Classical+ era starts: Historical factions (Rome, Greece, etc.) in proper regions
- All player actions tracked against historical expectations
- Timeline divergence scoring and alternate timeline naming
"""

import random
from typing import Dict, List, Any, Optional
from engines.world_modes.base_mode import WorldMode


class ButterflyEffectTracker:
    """Tracks divergences from historical timeline and measures impact."""

    def __init__(self, starting_era: str, starting_year: int):
        """
        Initialize the butterfly effect tracker.

        Args:
            starting_era: The era the game starts in
            starting_year: The specific year the game starts
        """
        self.starting_era = starting_era
        self.starting_year = starting_year
        self.divergence_score = 0  # 0 = historical, 100 = completely altered
        self.key_divergences = []
        self.timeline_altered = False

    def track_action(self, year: int, action: str, historical_expected: Optional[str] = None, impact: int = 5):
        """
        Track a player action and its divergence from history.

        Args:
            year: The year the action occurred
            action: Description of the action taken
            historical_expected: What historically should have happened (if known)
            impact: Divergence impact score (1-20, default 5)
        """
        divergence_entry = {
            "year": year,
            "action": action,
            "historical_path": historical_expected,
            "impact": impact
        }

        self.divergence_score = min(100, self.divergence_score + impact)
        self.key_divergences.append(divergence_entry)
        self.timeline_altered = True

    def get_timeline_name(self) -> str:
        """
        Generate a name for the current timeline based on divergence level.

        Returns:
            Timeline classification string
        """
        if self.divergence_score < 10:
            return "Historical Timeline (Minor Variations)"
        elif self.divergence_score < 30:
            return "Slightly Divergent Timeline"
        elif self.divergence_score < 50:
            return "Alternate History Timeline"
        elif self.divergence_score < 75:
            return "Radically Divergent Timeline"
        else:
            return "Unrecognizable Future"

    def get_divergence_summary(self) -> Dict[str, Any]:
        """
        Get a summary of timeline divergence.

        Returns:
            Dictionary with divergence statistics
        """
        return {
            "divergence_score": self.divergence_score,
            "timeline_name": self.get_timeline_name(),
            "key_divergences": self.key_divergences[-5:],  # Last 5 major divergences
            "total_divergences": len(self.key_divergences),
            "timeline_altered": self.timeline_altered
        }


class HistoricalEarthMode(WorldMode):
    """Historical Earth world generation mode with realistic geography and factions."""

    # Historical ERA configurations with accurate dates
    ERA_CONFIGS = {
        "stone_age": {
            "era": "stone_age",
            "year_range": (-10000, -3000),
            "tech_tier": "stone_age",
            "base_discoveries": ["Fire", "Stone Tools", "Spears", "Basic Agriculture", "Pottery"],
            "base_infrastructure": ["Central Hearth", "Temporary Shelters", "Food Storage"],
            "population_multiplier": 0.5,
            "historical_context": "Neolithic Revolution - transition from hunter-gatherers to agricultural settlements",
            "butterfly_effects_enabled": True
        },
        "bronze_age": {
            "era": "bronze_age",
            "year_range": (-3000, -1200),
            "tech_tier": "bronze_age",
            "base_discoveries": ["Fire", "Stone Tools", "Spears", "Basic Agriculture", "Pottery", "Bronze Casting", "Writing", "Wheel"],
            "base_infrastructure": ["Central Hearth", "Permanent Dwellings", "Granaries", "Defensive Walls"],
            "population_multiplier": 1.0,
            "historical_context": "Rise of early civilizations (Sumer, Egypt, Indus Valley, Early China)",
            "butterfly_effects_enabled": True
        },
        "iron_age": {
            "era": "iron_age",
            "year_range": (-1200, -500),
            "tech_tier": "iron_age",
            "base_discoveries": ["Fire", "Stone Tools", "Bronze Casting", "Writing", "Wheel", "Iron Smelting", "Advanced Agriculture", "Sea Navigation"],
            "base_infrastructure": ["Permanent Dwellings", "Granaries", "Stone Walls", "Watchtowers", "Workshop"],
            "population_multiplier": 1.5,
            "historical_context": "Bronze Age Collapse, rise of iron-using civilizations, Phoenician trade networks",
            "butterfly_effects_enabled": True
        },
        "classical": {
            "era": "classical",
            "year_range": (-500, 500),
            "tech_tier": "classical",
            "base_discoveries": ["Fire", "Bronze Casting", "Writing", "Wheel", "Iron Smelting", "Advanced Agriculture", "Philosophy", "Engineering", "Currency"],
            "base_infrastructure": ["Urban Centers", "Aqueducts", "Roads", "Temples", "Marketplace", "Fortifications"],
            "population_multiplier": 2.0,
            "historical_context": "Height of Classical civilizations: Greece, Rome, Han China, Maurya India",
            "historical_factions_enabled": True
        }
    }

    # Earth geographic regions with realistic details
    EARTH_REGIONS = {
        "mediterranean": {
            "region_name": "Mediterranean Basin",
            "terrain": "Coastal regions with rolling hills, fertile valleys, and rugged mountains",
            "climate": "Mediterranean - hot dry summers, mild wet winters",
            "resources": ["Fish", "Olive oil", "Grain", "Wine", "Marble", "Timber", "Copper", "Tin"],
            "threats": ["Rival city-states", "Pirates", "Earthquakes", "Periodic droughts"],
            "historical_neighbors": {
                "stone_age": ["Proto-European tribes", "Early Anatolian peoples"],
                "bronze_age": ["Minoan traders", "Early Helladic peoples", "Anatolian tribes"],
                "iron_age": ["Phoenician merchants", "Early Greek colonies", "Etruscan traders"],
                "classical": ["Greek City-States", "Roman Republic", "Carthaginian Empire", "Hellenistic Kingdoms"]
            },
            "lat_long": (40, 15),  # Approximate center
            "description": "The cradle of Western civilization, where empires rise and fall like the tides"
        },
        "mesopotamia": {
            "region_name": "Mesopotamia",
            "terrain": "Fertile river valleys between the Tigris and Euphrates, surrounded by arid steppes",
            "climate": "Arid subtropical - extremely hot summers, seasonal floods",
            "resources": ["Grain", "Date palms", "Clay", "Fish", "Reeds", "Limited timber"],
            "threats": ["Unpredictable flooding", "Summertime heat", "Invasions from the north", "Resource scarcity"],
            "historical_neighbors": {
                "stone_age": ["Early Ubaid people", "Proto-Sumerian tribes"],
                "bronze_age": ["Sumerian city-states", "Akkadian Empire", "Babylonian Kingdom"],
                "iron_age": ["Assyrian Empire", "Babylonian Empire", "Median tribes"],
                "classical": ["Persian Empire", "Parthian Empire", "Seleucid Dynasty"]
            },
            "lat_long": (33, 44),
            "description": "The fertile crescent, birthplace of writing, law, and urban civilization"
        },
        "nile_valley": {
            "region_name": "Nile River Valley",
            "terrain": "Narrow fertile corridor along the Nile, surrounded by vast deserts",
            "climate": "Hot desert - scorching summers, predictable annual floods",
            "resources": ["Grain", "Papyrus", "Fish", "Gold", "Stone", "Natron", "Linen"],
            "threats": ["Desert raiders", "Flooding extremes", "Scorching heat", "Limited arable land"],
            "historical_neighbors": {
                "stone_age": ["Early Saharan peoples", "Proto-Egyptians"],
                "bronze_age": ["Nubian kingdoms", "Libyan tribes", "Canaanite traders"],
                "iron_age": ["Nubian Kingdom of Kush", "Libyan dynasties", "Sea Peoples"],
                "classical": ["Ptolemaic Egypt", "Nubian Meroitic Kingdom", "Roman Egypt"]
            },
            "lat_long": (26, 32),
            "description": "The gift of the Nile, where pharaohs reign and monuments touch eternity"
        },
        "yellow_river": {
            "region_name": "Yellow River Valley",
            "terrain": "Loess plateau with fertile river valley, surrounded by mountains and steppes",
            "climate": "Continental - harsh cold winters, hot humid summers",
            "resources": ["Millet", "Rice", "Silk", "Jade", "Bronze", "Bamboo", "Tea"],
            "threats": ["Devastating floods", "Droughts", "Nomadic invasions from the north", "Earthquakes"],
            "historical_neighbors": {
                "stone_age": ["Yangshao culture tribes", "Early agricultural communities"],
                "bronze_age": ["Shang Dynasty", "Various Neolithic cultures"],
                "iron_age": ["Zhou Dynasty states", "Nomadic Xiongnu"],
                "classical": ["Warring States", "Qin Dynasty", "Han Dynasty", "Xiongnu Confederation"]
            },
            "lat_long": (35, 110),
            "description": "Cradle of Chinese civilization, where dynasties rise under the Mandate of Heaven"
        },
        "indus_valley": {
            "region_name": "Indus River Valley",
            "terrain": "Broad river valley with fertile plains, bordered by mountains and desert",
            "climate": "Subtropical - monsoon rains, hot dry season",
            "resources": ["Grain", "Cotton", "Precious stones", "Timber", "Copper", "Carnelian"],
            "threats": ["Monsoon flooding", "River course changes", "Periodic droughts", "Mountain tribes"],
            "historical_neighbors": {
                "stone_age": ["Mehrgarh culture peoples", "Early pastoralists"],
                "bronze_age": ["Harappan civilization", "Indo-Aryan migrants"],
                "iron_age": ["Mahajanapadas", "Indo-Aryan kingdoms"],
                "classical": ["Maurya Empire", "Indo-Greek Kingdoms", "Kushan Empire", "Gupta Dynasty"]
            },
            "lat_long": (27, 70),
            "description": "Land of ancient cities and sacred rivers, where philosophy and trade flourish"
        }
    }

    # Historical faction templates for Classical era
    HISTORICAL_FACTIONS = {
        "classical_rome": {
            "civilization_name": "Roman Republic",
            "leader_name": "Consul Marcus Aurelius Cato",
            "factions": [
                {
                    "name": "The Senate",
                    "leader": "Senator Lucius Cornelius",
                    "approval": 60,
                    "support_percentage": 30,
                    "status": "Neutral",
                    "goals": ["Maintain patrician privileges", "Expand Roman territory", "Preserve republican institutions"],
                    "description": "The aristocratic body that has guided Rome since its founding"
                },
                {
                    "name": "The Plebeian Assembly",
                    "leader": "Tribune Gaius Gracchus",
                    "approval": 55,
                    "support_percentage": 35,
                    "status": "Neutral",
                    "goals": ["Land redistribution for veterans", "Debt relief", "Greater political representation"],
                    "description": "Representatives of the common people, demanding reform and equality"
                },
                {
                    "name": "The Legates",
                    "leader": "General Scipio Africanus",
                    "approval": 65,
                    "support_percentage": 25,
                    "status": "Supportive",
                    "goals": ["Military expansion", "Glory in battle", "Veterans' settlements"],
                    "description": "Military commanders who have conquered distant lands for Rome"
                },
                {
                    "name": "The College of Pontiffs",
                    "leader": "Pontifex Maximus Quintus",
                    "approval": 60,
                    "support_percentage": 10,
                    "status": "Neutral",
                    "goals": ["Maintain traditional Roman religion", "Interpret divine omens", "Preserve sacred rituals"],
                    "description": "Keepers of Roman religious tradition and sacred law"
                }
            ]
        },
        "classical_greece": {
            "civilization_name": "Athenian Polis",
            "leader_name": "Archon Pericles",
            "factions": [
                {
                    "name": "The Ecclesia",
                    "leader": "Citizen Demosthenes",
                    "approval": 60,
                    "support_percentage": 40,
                    "status": "Neutral",
                    "goals": ["Strengthen democracy", "Naval supremacy", "Cultural excellence"],
                    "description": "The democratic assembly of all citizens, voice of the people"
                },
                {
                    "name": "The Strategoi",
                    "leader": "General Themistocles",
                    "approval": 65,
                    "support_percentage": 25,
                    "status": "Supportive",
                    "goals": ["Defeat Persian threats", "Train hoplites", "Build the navy"],
                    "description": "Military leaders elected to defend Athens and lead her armies"
                },
                {
                    "name": "The Oracle of Delphi",
                    "leader": "Pythia Cassandra",
                    "approval": 60,
                    "support_percentage": 15,
                    "status": "Neutral",
                    "goals": ["Interpret divine will", "Maintain sacred sites", "Guide policy through prophecy"],
                    "description": "Priestesses who channel the wisdom of Apollo himself"
                },
                {
                    "name": "The Merchant League",
                    "leader": "Lysias of Piraeus",
                    "approval": 55,
                    "support_percentage": 20,
                    "status": "Neutral",
                    "goals": ["Expand trade networks", "Establish colonies", "Protect shipping lanes"],
                    "description": "Wealthy traders who bring prosperity from across the Mediterranean"
                }
            ]
        },
        "classical_carthage": {
            "civilization_name": "Carthaginian Republic",
            "leader_name": "Suffete Hamilcar Barca",
            "factions": [
                {
                    "name": "The Council of Elders",
                    "leader": "Elder Hanno the Great",
                    "approval": 60,
                    "support_percentage": 30,
                    "status": "Neutral",
                    "goals": ["Maintain commercial dominance", "Avoid costly wars", "Preserve oligarchic rule"],
                    "description": "Wealthy merchant princes who have governed Carthage for generations"
                },
                {
                    "name": "The Barcid Faction",
                    "leader": "General Hannibal Barca",
                    "approval": 70,
                    "support_percentage": 35,
                    "status": "Supportive",
                    "goals": ["Defeat Rome", "Conquer Iberia", "Military glory"],
                    "description": "Military dynasty seeking to restore Carthaginian power through conquest"
                },
                {
                    "name": "The Sacred Band",
                    "leader": "Commander Mago",
                    "approval": 60,
                    "support_percentage": 20,
                    "status": "Neutral",
                    "goals": ["Defend the city", "Train elite warriors", "Maintain honor"],
                    "description": "Elite citizen soldiers sworn to defend Carthage to the death"
                },
                {
                    "name": "The Priesthood of Tanit",
                    "leader": "High Priestess Sophonisba",
                    "approval": 55,
                    "support_percentage": 15,
                    "status": "Neutral",
                    "goals": ["Maintain religious traditions", "Perform sacred rites", "Seek divine favor"],
                    "description": "Servants of the goddess Tanit, protector of Carthage"
                }
            ]
        }
    }

    # Cultural templates adapted for historical realism
    CULTURE_TEMPLATES = {
        "martial": {
            "values": ["Strength", "Courage", "Honor", "Discipline", "Loyalty"],
            "sample_traditions": ["Warrior Initiations", "Battle Commemorations", "Weapon Crafting Ceremonies"],
            "traits": ["Aggressive", "Disciplined", "Territorial"]
        },
        "spiritual": {
            "values": ["Wisdom", "Devotion", "Harmony", "Respect for Spirits", "Ritual"],
            "sample_traditions": ["Seasonal Rituals", "Spirit Offerings", "Sacred Pilgrimages"],
            "traits": ["Contemplative", "Mystical", "Ritualistic"]
        },
        "agricultural": {
            "values": ["Hard Work", "Community", "Harvest", "Patience", "Sustainability"],
            "sample_traditions": ["Planting Festivals", "Harvest Celebrations", "Crop Rotation Rituals"],
            "traits": ["Patient", "Cooperative", "Grounded"]
        },
        "mercantile": {
            "values": ["Trade", "Prosperity", "Diplomacy", "Innovation", "Fairness"],
            "sample_traditions": ["Market Days", "Trade Agreements", "Merchant Guilds"],
            "traits": ["Diplomatic", "Shrewd", "Cosmopolitan"]
        },
        "scholarly": {
            "values": ["Knowledge", "Curiosity", "Innovation", "Record-Keeping", "Teaching"],
            "sample_traditions": ["Oral Storytelling", "Star Gazing Ceremonies", "Knowledge Sharing Gatherings"],
            "traits": ["Inquisitive", "Methodical", "Inventive"]
        },
        "artistic": {
            "values": ["Beauty", "Expression", "Creativity", "Tradition", "Excellence"],
            "sample_traditions": ["Art Festivals", "Craftsmanship Competitions", "Performance Rituals"],
            "traits": ["Creative", "Expressive", "Detail-Oriented"]
        }
    }

    # Religion configurations for historical mode
    RELIGION_CONFIGS = {
        "animism": {
            "name": "Animism",
            "type": "Spirit Worship",
            "tenets": ["All things have a spirit", "The natural world must be respected", "Balance must be maintained"],
            "practices": ["Shamanic rituals", "Spirit offerings", "Nature veneration"]
        },
        "polytheism": {
            "name": "Polytheism",
            "type": "Multiple Deities",
            "tenets": ["The gods influence all aspects of life", "Each deity governs their domain", "Offerings bring favor"],
            "practices": ["Temple rituals", "Sacrificial offerings", "Divine festivals"]
        },
        "ancestor_worship": {
            "name": "Ancestor Veneration",
            "type": "Ancestor Worship",
            "tenets": ["The ancestors watch over us", "Honor the dead to prosper", "Lineage is sacred"],
            "practices": ["Ancestral offerings", "Tomb maintenance", "Genealogy keeping"]
        }
    }

    SOCIAL_STRUCTURES = {
        "egalitarian": "Egalitarian community where decisions are made collectively",
        "hierarchical": "Hierarchical society with clear social ranks",
        "tribal_council": "Tribal council of elders and skilled leaders",
        "city_state": "City-state with assembly and elected officials",
        "monarchy": "Hereditary monarchy with a ruling dynasty",
        "republic": "Republic with elected representatives",
        "theocracy": "Religious leaders hold temporal power"
    }

    def __init__(self):
        """Initialize the Historical Earth mode."""
        self.butterfly_tracker: Optional[ButterflyEffectTracker] = None

    def get_era_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.ERA_CONFIGS

    def get_terrain_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.EARTH_REGIONS

    def get_culture_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.CULTURE_TEMPLATES

    def get_religion_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.RELIGION_CONFIGS

    def get_social_structures(self) -> Dict[str, Dict[str, Any]]:
        return self.SOCIAL_STRUCTURES

    def get_starting_year(self, era: str) -> int:
        era_config = self.ERA_CONFIGS.get(era, self.ERA_CONFIGS["bronze_age"])
        year_min, year_max = era_config["year_range"]
        return random.randint(year_min, year_max)

    def generate_civilization(self, config: Dict[str, Any]) -> Dict[str, Any]:
        era = config.get("starting_era", config.get("era", "bronze_age"))
        region = config.get("earth_region", "mediterranean")
        population_size = config.get("population_size", "medium")

        era_config = self.ERA_CONFIGS[era]
        region_config = self.EARTH_REGIONS.get(region, self.EARTH_REGIONS["mediterranean"])

        # Check if we should use historical factions
        use_historical = era_config.get("historical_factions_enabled", False)

        if use_historical and era == "classical":
            # Use historical civilization name
            if region == "mediterranean":
                faction_template = random.choice(["classical_rome", "classical_greece"])
            else:
                faction_template = "classical_rome"  # Default for now

            historical_data = self.HISTORICAL_FACTIONS.get(faction_template, self.HISTORICAL_FACTIONS["classical_rome"])
            civ_name = historical_data["civilization_name"]
            leader_name = historical_data["leader_name"]
        else:
            # Proto-civilization for early eras
            civ_name = config.get("civilization_name", f"The {region_config['region_name']} People")
            leader_name = config.get("leader_name", self._generate_historical_name(region, era))

        # Population calculation
        pop_ranges = {
            "small": (100, 500),
            "medium": (500, 2000),
            "large": (2000, 5000)
        }
        pop_min, pop_max = pop_ranges[population_size]
        population = random.randint(
            int(pop_min * era_config["population_multiplier"]),
            int(pop_max * era_config["population_multiplier"])
        )

        # Year calculation
        year = self.get_starting_year(era)

        # Initialize butterfly tracker for early eras
        if era_config.get("butterfly_effects_enabled", False):
            self.butterfly_tracker = ButterflyEffectTracker(era, year)

        leader_traits = random.sample([
            "Wise", "Brave", "Diplomatic", "Strategic", "Charismatic",
            "Cautious", "Bold", "Pious", "Pragmatic", "Visionary"
        ], 3)

        return {
            "meta": {
                "name": civ_name,
                "year": year,
                "era": era_config["era"],
                "founding_date": year,
                "world_mode": "historical_earth",
                "earth_region": region,
                "butterfly_effects_enabled": era_config.get("butterfly_effects_enabled", False),
                "historical_factions_enabled": era_config.get("historical_factions_enabled", False)
            },
            "leader": {
                "name": leader_name,
                "age": random.randint(25, 45),
                "life_expectancy": random.randint(50, 70),  # Realistic for ancient times
                "role": "Leader",
                "traits": leader_traits,
                "years_ruled": 0
            },
            "population": population,
            "resources": {
                "food": population * random.randint(1, 3),
                "wealth": population * random.randint(1, 2),
                "tech_tier": era_config["tech_tier"]
            }
        }

    def generate_culture(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cultural_focus = config.get("cultural_focus", "agricultural")
        social_structure = config.get("social_structure", "tribal_council")
        era = config.get("starting_era", "bronze_age")
        region = config.get("earth_region", "mediterranean")

        culture_template = self.CULTURE_TEMPLATES[cultural_focus]

        # Historical cultural elements based on region
        regional_values = {
            "mediterranean": ["Maritime Trade", "Urban Life", "Political Discourse"],
            "mesopotamia": ["Law and Order", "Written Records", "Irrigation Management"],
            "nile_valley": ["Divine Kingship", "Monumental Architecture", "Eternal Life"],
            "yellow_river": ["Filial Piety", "Ancestor Reverence", "Bureaucratic Order"],
            "indus_valley": ["Urban Planning", "Trade Networks", "Spiritual Wisdom"]
        }

        values = culture_template["values"].copy()
        values.extend(regional_values.get(region, ["Community", "Tradition"]))

        traditions = culture_template["sample_traditions"].copy()
        traditions.extend(random.sample([
            "Oral Storytelling", "Seasonal Celebrations", "Coming of Age Ceremonies",
            "Ancestral Veneration", "Crafting Competitions"
        ], 2))

        return {
            "values": values[:8],
            "traditions": traditions[:6],
            "taboos": ["Harming Kin", random.choice(["Breaking Oaths", "Sacrilege", "Betraying Trust"])],
            "social_structure": self.SOCIAL_STRUCTURES[social_structure],
            "recent_changes": []
        }

    def generate_religion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        era = config.get("starting_era", "bronze_age")
        region = config.get("earth_region", "mediterranean")

        # Region-appropriate religions
        if era in ["stone_age", "bronze_age"]:
            religion_type = random.choice(["animism", "polytheism", "ancestor_worship"])
        else:
            religion_type = config.get("religion_type", "polytheism")

        religion_config = self.RELIGION_CONFIGS.get(religion_type, self.RELIGION_CONFIGS["polytheism"])

        # Region-specific deity names
        regional_deities = {
            "mediterranean": {
                "polytheism": ["The Olympian Gods", "The Divine Pantheon", "The Twelve Gods"],
                "animism": ["The Sea Spirits", "The Mountain Guardians"]
            },
            "mesopotamia": {
                "polytheism": ["The Anunnaki", "The Divine Assembly", "The Seven Who Decree Fate"],
                "animism": ["The River Spirits", "The Desert Gods"]
            },
            "nile_valley": {
                "polytheism": ["The Ennead of Heliopolis", "The Divine Order of Ra", "The Gods of the Two Lands"],
                "animism": ["The Nile Spirit", "The Desert Guardian"]
            },
            "yellow_river": {
                "polytheism": ["The Celestial Court", "The Heavenly Bureaucracy"],
                "ancestor_worship": ["The First Ancestors", "The Divine Emperors"]
            }
        }

        deity_options = regional_deities.get(region, {}).get(religion_type, ["The Great Spirit"])
        primary_deity = random.choice(deity_options)

        holy_sites = [
            f"The Sacred {random.choice(['Grove', 'Mountain', 'Temple', 'Spring'])}",
            f"The Ancient {random.choice(['Shrine', 'Monument', 'Altar', 'Cave'])}"
        ]

        return {
            "name": religion_config["name"],
            "type": religion_config["type"],
            "primary_deity": primary_deity,
            "core_tenets": religion_config["tenets"],
            "practices": religion_config["practices"],
            "holy_sites": holy_sites,
            "influence": random.choice(["dominant", "significant"]),
            "schisms": []
        }

    def generate_technology(self, config: Dict[str, Any]) -> Dict[str, Any]:
        era = config.get("starting_era", config.get("era", "bronze_age"))
        era_config = self.ERA_CONFIGS[era]

        return {
            "current_tier": era_config["tech_tier"],
            "discoveries": era_config["base_discoveries"].copy(),
            "in_progress": [],
            "infrastructure": era_config["base_infrastructure"].copy()
        }

    def generate_world_context(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return self.generate_geography(config)

    def generate_geography(self, config: Dict[str, Any]) -> Dict[str, Any]:
        region = config.get("earth_region", "mediterranean")
        era = config.get("starting_era", "bronze_age")
        difficulty = config.get("difficulty", "balanced")

        region_config = self.EARTH_REGIONS[region]

        # Get era-appropriate neighbors
        neighbors_list = region_config["historical_neighbors"].get(era, [])

        # Generate neighbor relationships
        neighbors = []
        for neighbor_name in neighbors_list[:3]:  # Limit to 3 neighbors
            if difficulty == "peaceful":
                relationship = random.choice(["allied", "neutral", "friendly"])
            elif difficulty == "challenging":
                relationship = random.choice(["neutral", "wary", "hostile"])
            else:
                relationship = random.choice(["allied", "neutral", "wary"])

            neighbors.append({
                "name": neighbor_name,
                "relationship": relationship,
                "strength": "unknown",
                "distance": random.choice(["nearby", "several days journey", "distant"]),
                "history": f"Historical presence in the {region_config['region_name']}"
            })

        return {
            "known_peoples": neighbors,
            "geography": {
                "region": region_config["region_name"],
                "terrain": region_config["terrain"],
                "climate": region_config["climate"],
                "resources": region_config["resources"],
                "threats": region_config["threats"]
            }
        }

    def generate_factions(self, era: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate appropriate factions based on era and region."""
        region = config.get("earth_region", "mediterranean")
        era_config = self.ERA_CONFIGS.get(era, self.ERA_CONFIGS["bronze_age"])

        # Use historical factions for Classical era
        if era_config.get("historical_factions_enabled", False) and era == "classical":
            if region == "mediterranean":
                faction_key = random.choice(["classical_rome", "classical_greece", "classical_carthage"])
            else:
                faction_key = "classical_rome"

            historical_data = self.HISTORICAL_FACTIONS.get(faction_key, self.HISTORICAL_FACTIONS["classical_rome"])
            return historical_data["factions"]

        # Generate proto-civilization factions for earlier eras
        return self._generate_proto_factions(era, region)

    def _generate_proto_factions(self, era: str, region: str) -> List[Dict[str, Any]]:
        """Generate factions for pre-classical eras."""
        # Era-appropriate faction types
        if era == "stone_age":
            faction_templates = [
                {"name": "The Hunter Band", "leader": "Chief Hunter", "focus": "hunting and gathering"},
                {"name": "The Elders' Circle", "leader": "Wise Elder", "focus": "tradition and wisdom"},
                {"name": "The Toolmakers", "leader": "Master Craftsman", "focus": "tool creation"},
                {"name": "The Spirit Speakers", "leader": "Shaman", "focus": "spiritual guidance"}
            ]
        elif era == "bronze_age":
            faction_templates = [
                {"name": "The Merchant Consortium", "leader": "Trade Master", "focus": "commerce"},
                {"name": "The Council of Elders", "leader": "High Elder", "focus": "tradition"},
                {"name": "The Warrior Lodge", "leader": "War Leader", "focus": "defense"},
                {"name": "The Temple Priests", "leader": "High Priest", "focus": "religion"}
            ]
        else:  # iron_age
            faction_templates = [
                {"name": "The Merchant Assembly", "leader": "Guild Master", "focus": "trade"},
                {"name": "The Senate of Elders", "leader": "First Senator", "focus": "governance"},
                {"name": "The Military Council", "leader": "General", "focus": "military"},
                {"name": "The Priesthood", "leader": "High Priest", "focus": "religion"}
            ]

        factions = []
        for template in faction_templates:
            factions.append({
                "name": template["name"],
                "leader": template["leader"],
                "approval": random.randint(55, 65),
                "support_percentage": random.randint(20, 30),
                "status": "Neutral",
                "goals": [
                    f"Advance {template['focus']}",
                    "Increase influence",
                    "Secure resources"
                ]
            })

        return factions

    def generate_inner_circle(self, config: Dict[str, Any], factions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate inner circle advisors appropriate for the era and region."""
        era = config.get("starting_era", "bronze_age")
        region = config.get("earth_region", "mediterranean")
        cultural_focus = config.get("cultural_focus", "agricultural")

        # Role templates adapted for historical context
        role_templates = [
            {
                "role_key": "military",
                "roles": {
                    "stone_age": "War Chief",
                    "bronze_age": "Commander",
                    "iron_age": "General",
                    "classical": "Strategos"
                },
                "base_traits": ["Disciplined", "Strategic", "Brave"],
                "faction_preference": "warrior"
            },
            {
                "role_key": "advisor",
                "roles": {
                    "stone_age": "Wise Elder",
                    "bronze_age": "Chief Advisor",
                    "iron_age": "Chancellor",
                    "classical": "Chief Minister"
                },
                "base_traits": ["Wise", "Diplomatic", "Cautious"],
                "faction_preference": "elder"
            },
            {
                "role_key": "spiritual",
                "roles": {
                    "stone_age": "Shaman",
                    "bronze_age": "High Priest",
                    "iron_age": "Chief Priest",
                    "classical": "Pontifex"
                },
                "base_traits": ["Pious", "Contemplative", "Influential"],
                "faction_preference": "priest"
            }
        ]

        characters = []
        for template in role_templates:
            role = template["roles"].get(era, template["roles"]["bronze_age"])
            traits = template["base_traits"].copy()

            # Find matching faction
            faction_link = None
            for faction in factions:
                if any(keyword in faction["name"].lower() for keyword in [template["faction_preference"], "warrior", "elder", "priest", "temple"]):
                    faction_link = faction["name"]
                    break

            if not faction_link and factions:
                faction_link = factions[0]["name"]

            name = self._generate_historical_name(region, era)

            character = {
                "name": name,
                "role": role,
                "faction_link": faction_link,
                "personality_traits": traits,
                "dialogue_sample": f"I serve our people with {traits[0].lower()} dedication.",
                "history": [f"Appointed as {role}."],
                "metrics": {
                    "relationship": random.randint(45, 60),
                    "influence": random.randint(40, 70),
                    "loyalty": random.randint(55, 75)
                },
                "portrait": "placeholder.png"
            }
            characters.append(character)

        return characters

    def _generate_historical_name(self, region: str, era: str) -> str:
        """Generate historically appropriate names based on region."""
        # Regional name pools
        names = {
            "mediterranean": {
                "male": ["Marcus", "Lucius", "Gaius", "Titus", "Pericles", "Themistocles", "Alcibiades"],
                "female": ["Julia", "Cornelia", "Livia", "Aspasia", "Artemisia"]
            },
            "mesopotamia": {
                "male": ["Hammurabi", "Sargon", "Gilgamesh", "Nabonidus", "Ashurbanipal"],
                "female": ["Enheduanna", "Semiramis", "Puabi"]
            },
            "nile_valley": {
                "male": ["Ramesses", "Thutmose", "Amenhotep", "Khufu", "Imhotep"],
                "female": ["Nefertiti", "Hatshepsut", "Cleopatra", "Nefertari"]
            },
            "yellow_river": {
                "male": ["Qin", "Liu", "Wang", "Zhang", "Chen"],
                "female": ["Wu", "Li", "Wang", "Chen"]
            },
            "indus_valley": {
                "male": ["Chandragupta", "Ashoka", "Vikramaditya"],
                "female": ["Draupadi", "Sita"]
            }
        }

        region_names = names.get(region, names["mediterranean"])
        gender = random.choice(["male", "female"])
        name = random.choice(region_names[gender])

        titles = ["the Great", "the Wise", "the Builder", "the Just", "the Bold"]
        return f"{name} {random.choice(titles)}"

    def generate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete historical Earth world."""
        civilization = self.generate_civilization(config)
        culture = self.generate_culture(config)
        religion = self.generate_religion(config)
        technology = self.generate_technology(config)
        world_context = self.generate_world_context(config)
        factions = self.generate_factions(config.get('starting_era', 'bronze_age'), config)
        inner_circle = self.generate_inner_circle(config, factions)

        # Store butterfly tracker reference if it exists
        if self.butterfly_tracker:
            civilization['meta']['butterfly_tracker'] = self.butterfly_tracker.get_divergence_summary()

        return {
            'civilization': civilization,
            'culture': culture,
            'religion': religion,
            'technology': technology,
            'world': world_context,
            'history_long': {"events": []},
            'history_compressed': {"eras": []},
            'factions': {"factions": factions},
            'inner_circle': {"characters": inner_circle}
        }

