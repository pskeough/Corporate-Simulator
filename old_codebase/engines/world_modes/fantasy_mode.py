"""
Fantasy World Mode

This mode provides randomized fantasy world generation with fictional civilizations,
cultures, and geography. This is the original world generation behavior.
"""

import random
from typing import Dict, List, Any
from engines.world_modes.base_mode import WorldMode


class FantasyWorldMode(WorldMode):
    """Fantasy world generation mode with random mythical elements."""

    # Configuration mappings (preserving original fantasy behavior)
    ERA_CONFIGS = {
        "stone_age": {
            "era": "stone_age",
            "year_range": (-50000, -10000),
            "tech_tier": "stone_age",
            "base_discoveries": ["Fire", "Basic Stone Tools", "Spears"],
            "base_infrastructure": ["Central Campfire", "Temporary Shelters"],
            "population_multiplier": 0.5
        },
        "bronze_age": {
            "era": "bronze_age",
            "year_range": (-3000, -1200),
            "tech_tier": "bronze_age",
            "base_discoveries": ["Fire", "Basic Stone Tools", "Spears", "Improved Stone Tools", "Basic Pottery", "Bronze Casting"],
            "base_infrastructure": ["Central Campfire", "Permanent Huts", "Storage Pits"],
            "population_multiplier": 1.0
        },
        "iron_age": {
            "era": "iron_age",
            "year_range": (-1200, -500),
            "tech_tier": "iron_age",
            "base_discoveries": ["Fire", "Basic Stone Tools", "Spears", "Improved Stone Tools", "Basic Pottery", "Bronze Casting", "Iron Smelting", "Advanced Metalwork"],
            "base_infrastructure": ["Central Campfire", "Permanent Huts", "Storage Pits", "Stone Walls", "Watchtowers"],
            "population_multiplier": 1.5
        },
        "classical": {
            "era": "classical",
            "year_range": (-500, 500),
            "tech_tier": "classical",
            "base_discoveries": ["Fire", "Basic Stone Tools", "Spears", "Improved Stone Tools", "Basic Pottery", "Bronze Casting", "Iron Smelting", "Advanced Metalwork", "Writing Systems", "Advanced Architecture"],
            "base_infrastructure": ["Central Campfire", "Permanent Huts", "Storage Pits", "Stone Walls", "Watchtowers", "Marketplace", "Temple"],
            "population_multiplier": 2.0
        }
    }

    TERRAIN_CONFIGS = {
        "coastal": {
            "terrain": "Coastal cliffs with beaches and tide pools",
            "climate": "Temperate maritime",
            "resources": ["Fish", "Shellfish", "Seaweed", "Salt", "Driftwood"],
            "threats": ["Storms", "Tides", "Sea raiders"]
        },
        "forest": {
            "terrain": "Dense forest with clearings",
            "climate": "Temperate",
            "resources": ["Wild game", "Berries", "Timber", "Fresh water"],
            "threats": ["Wild beasts", "Harsh winters", "Forest fires"]
        },
        "mountain": {
            "terrain": "Rocky highlands with valleys",
            "climate": "Alpine",
            "resources": ["Stone", "Mountain herbs", "Game birds", "Snow melt water"],
            "threats": ["Avalanches", "Cold", "Mountain predators", "Difficult terrain"]
        },
        "desert": {
            "terrain": "Arid dunes with scattered oases",
            "climate": "Arid",
            "resources": ["Date palms", "Cacti", "Underground water", "Salt"],
            "threats": ["Sandstorms", "Extreme heat", "Scarce water", "Desert raiders"]
        },
        "plains": {
            "terrain": "Rolling grasslands",
            "climate": "Continental",
            "resources": ["Wild grains", "Grazing animals", "Rivers", "Clay"],
            "threats": ["Wildfires", "Nomadic raiders", "Droughts", "Floods"]
        },
        "river_valley": {
            "terrain": "Fertile valley along a great river",
            "climate": "Temperate",
            "resources": ["Fresh water", "Fertile soil", "Fish", "Reeds", "Wild game"],
            "threats": ["Flooding", "Waterborne diseases", "Rival settlements"]
        },
        "island": {
            "terrain": "Volcanic island with lush vegetation",
            "climate": "Tropical",
            "resources": ["Coconuts", "Fish", "Tropical fruits", "Obsidian"],
            "threats": ["Isolation", "Volcanic activity", "Hurricanes", "Limited resources"]
        }
    }

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
        "monotheism": {
            "name": "Monotheism",
            "type": "Single Deity",
            "tenets": ["There is one supreme divine power", "Faith brings salvation", "The divine law must be followed"],
            "practices": ["Prayer rituals", "Sacred texts recitation", "Pilgrimage"]
        },
        "ancestor_worship": {
            "name": "Ancestor Veneration",
            "type": "Ancestor Worship",
            "tenets": ["The ancestors watch over us", "Honor the dead to prosper", "Lineage is sacred"],
            "practices": ["Ancestral offerings", "Tomb maintenance", "Genealogy keeping"]
        },
        "nature_worship": {
            "name": "Nature Reverence",
            "type": "Nature Worship",
            "tenets": ["Nature is the source of all life", "Harmony with the land brings prosperity", "Sacred groves must be protected"],
            "practices": ["Seasonal ceremonies", "Sacred grove pilgrimages", "Natural offerings"]
        },
        "none": {
            "name": "No Dominant Religion",
            "type": "Secular/Mixed Beliefs",
            "tenets": ["Practical wisdom guides us", "Diversity of belief is accepted"],
            "practices": ["Personal rituals", "Community gatherings"]
        }
    }

    SOCIAL_STRUCTURES = {
        "egalitarian": "Egalitarian tribe where decisions are made collectively",
        "hierarchical": "Hierarchical society with clear social ranks",
        "tribal_council": "Tribal council of elders and skilled leaders",
        "monarchy": "Hereditary monarchy with a ruling family",
        "theocracy": "Religious leaders hold temporal power"
    }

    def get_era_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.ERA_CONFIGS

    def get_terrain_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.TERRAIN_CONFIGS

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
        civ_name = config.get("civilization_name", "The People")
        population_size = config.get("population_size", "medium")
        leader_name = config.get("leader_name", "")

        era_config = self.ERA_CONFIGS[era]

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

        # Leader generation
        if not leader_name:
            leader_name = self._generate_leader_name()

        leader_traits = random.sample([
            "Wise", "Brave", "Diplomatic", "Strategic", "Charismatic",
            "Cautious", "Bold", "Spiritual", "Pragmatic", "Visionary"
        ], 3)

        return {
            "meta": {
                "name": civ_name,
                "year": year,
                "era": era_config["era"],
                "founding_date": year,
                "world_mode": "fantasy"
            },
            "leader": {
                "name": leader_name,
                "age": random.randint(25, 45),
                "life_expectancy": random.randint(60, 80),
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
        cultural_focus = config.get("cultural_focus", "spiritual")
        social_structure = config.get("social_structure", "egalitarian")

        culture_template = self.CULTURE_TEMPLATES[cultural_focus]

        # Select values
        values = culture_template["values"].copy()
        values.extend(random.sample([
            "Survival", "Community", "Respect for Elders", "Adaptation",
            "Craftsmanship", "Generosity", "Resilience"
        ], 3))

        # Select traditions
        traditions = culture_template["sample_traditions"].copy()
        traditions.extend(random.sample([
            "Oral Storytelling", "Seasonal Celebrations", "Coming of Age Ceremonies",
            "Ancestral Veneration", "Crafting Competitions"
        ], 2))

        return {
            "values": values[:8],
            "traditions": traditions[:6],
            "taboos": ["Harming Kin", random.choice(["Oath Breaking", "Sacrilege", "Betrayal", "Waste"])],
            "social_structure": self.SOCIAL_STRUCTURES[social_structure],
            "recent_changes": []
        }

    def generate_religion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        religion_type = config.get("religion_type", "animism")

        if religion_type not in self.RELIGION_CONFIGS:
            religion_type = "animism"

        religion_config = self.RELIGION_CONFIGS[religion_type]

        # Generate deity name based on type
        deity_names = {
            "animism": ["The Great Spirit", "The Wild Soul", "The Earth Mother"],
            "polytheism": ["The Pantheon of Stars", "The Divine Court", "The Ancient Gods"],
            "monotheism": ["The Eternal One", "The Supreme Creator", "The Divine Light"],
            "ancestor_worship": ["The First Ancestor", "The Ancient Fathers", "The Founding Lineage"],
            "nature_worship": ["The Forest Spirit", "The Mountain Guardian", "The River Mother"],
            "none": ["Various Spirits", "Personal Beliefs", "Folk Traditions"]
        }

        primary_deity = random.choice(deity_names.get(religion_type, ["The Unknown"]))

        # Generate holy sites
        holy_sites = [
            random.choice(["The Sacred Grove", "The Great Oak", "The Ancient Cave", "The Stone Circle"]),
            random.choice(["The Mountain Peak", "The River Source", "The Ancestor's Tomb", "The First Settlement"])
        ]

        return {
            "name": religion_config["name"],
            "type": religion_config["type"],
            "primary_deity": primary_deity,
            "core_tenets": religion_config["tenets"],
            "practices": religion_config["practices"],
            "holy_sites": holy_sites,
            "influence": random.choice(["dominant", "significant", "moderate"]),
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
        terrain = config.get("terrain", "forest")
        difficulty = config.get("difficulty", "balanced")
        neighbor_count = config.get("neighbor_count", "few")
        resource_abundance = config.get("resource_abundance", "moderate")

        terrain_config = self.TERRAIN_CONFIGS[terrain]

        # Adjust resources based on abundance
        resources = terrain_config["resources"].copy()
        if resource_abundance == "abundant":
            resources.extend(random.sample(["Medicinal Herbs", "Precious Stones", "Rare Woods", "Exotic Spices"], 2))
        elif resource_abundance == "scarce":
            resources = resources[:max(2, len(resources) - 2)]

        # Adjust threats based on difficulty
        threats = terrain_config["threats"].copy()
        if difficulty == "challenging":
            threats.extend(random.sample(["Hostile Neighbors", "Natural Disasters", "Resource Scarcity", "Disease"], 2))
        elif difficulty == "peaceful":
            threats = threats[:max(1, len(threats) - 1)]

        # Generate neighbors
        neighbor_counts = {
            "none": 0,
            "few": random.randint(1, 2),
            "several": random.randint(3, 4)
        }

        num_neighbors = neighbor_counts.get(neighbor_count, 1)
        neighbors = []

        neighbor_names = [
            "The River Clan", "The Mountain Folk", "The Desert Wanderers",
            "The Forest Tribes", "The Sea People", "The Plains Riders",
            "The Stone Circle Clans", "The Sun Worshippers"
        ]

        for i in range(num_neighbors):
            relationship = random.choice(["allied", "neutral", "wary", "hostile"]) if difficulty != "peaceful" else random.choice(["allied", "neutral", "friendly"])

            neighbors.append({
                "name": random.choice(neighbor_names),
                "relationship": relationship,
                "strength": "unknown",
                "distance": random.choice(["nearby", "several days journey", "distant"]),
                "history": "Recently discovered" if i == 0 else "Known through tales and occasional contact"
            })

        return {
            "known_peoples": neighbors,
            "geography": {
                "terrain": terrain_config["terrain"],
                "climate": terrain_config["climate"],
                "resources": resources,
                "threats": threats
            }
        }

    def generate_factions(self, era: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fantasy factions."""
        return [
            {
                "name": "The Merchant's Guild",
                "leader": "Lysander the Wealthy",
                "approval": 60,
                "support_percentage": 25,
                "status": "Neutral",
                "goals": ["Establish new trade routes", "Increase city wealth by 20%", "Reduce tariffs on luxury goods"]
            },
            {
                "name": "The Elder Council",
                "leader": "Elder Maeve",
                "approval": 60,
                "support_percentage": 20,
                "status": "Neutral",
                "goals": ["Preserve ancient traditions", "Maintain social stability", "Construct a monument to the founders"]
            },
            {
                "name": "The Warrior's Caste",
                "leader": "Warlord Gorok",
                "approval": 60,
                "support_percentage": 30,
                "status": "Neutral",
                "goals": ["Expand our borders", "Recruit and train more soldiers", "Vanquish our rivals"]
            },
            {
                "name": "The Priesthood of the Sun",
                "leader": "High Priestess Elara",
                "approval": 60,
                "support_percentage": 25,
                "status": "Neutral",
                "goals": ["Spread the faith to new lands", "Build a Grand Temple", "Achieve spiritual enlightenment for the people"]
            }
        ]

    def generate_inner_circle(self, config: Dict[str, Any], factions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate culturally grounded inner circle members."""
        cultural_focus = config.get("cultural_focus", "spiritual")
        era = config.get("starting_era", config.get("era", "bronze_age"))

        # Define role templates with cultural variations
        role_templates = [
            {
                "role_key": "military",
                "roles": {
                    "stone_age": "War Chief",
                    "bronze_age": "Commander",
                    "iron_age": "Grand Marshal",
                    "classical": "Strategos",
                    "medieval": "Lord Commander",
                    "renaissance": "Marshal General"
                },
                "base_traits": ["Disciplined", "Direct", "Stern"],
                "cultural_traits": {
                    "martial": ["Aggressive", "Tactical"],
                    "spiritual": ["Devoted", "Honorable"],
                    "agricultural": ["Protective", "Patient"],
                    "mercantile": ["Strategic", "Pragmatic"],
                    "scholarly": ["Analytical", "Methodical"],
                    "artistic": ["Charismatic", "Inspiring"]
                },
                "faction_preference": "warrior"
            },
            {
                "role_key": "intelligence",
                "roles": {
                    "stone_age": "Scout Master",
                    "bronze_age": "Eyes of the Throne",
                    "iron_age": "Spymaster",
                    "classical": "Master of Whispers",
                    "medieval": "Lord of Secrets",
                    "renaissance": "Intelligence Minister"
                },
                "base_traits": ["Cunning", "Discreet", "Observant"],
                "cultural_traits": {
                    "martial": ["Ruthless", "Efficient"],
                    "spiritual": ["Mysterious", "Intuitive"],
                    "agricultural": ["Patient", "Meticulous"],
                    "mercantile": ["Pragmatic", "Shrewd"],
                    "scholarly": ["Analytical", "Insightful"],
                    "artistic": ["Subtle", "Persuasive"]
                },
                "faction_preference": "merchant"
            },
            {
                "role_key": "spiritual",
                "roles": {
                    "stone_age": "Shaman",
                    "bronze_age": "High Priest",
                    "iron_age": "High Priestess",
                    "classical": "Hierophant",
                    "medieval": "Grand Cleric",
                    "renaissance": "Archbishop"
                },
                "base_traits": ["Pious", "Serene", "Compassionate"],
                "cultural_traits": {
                    "martial": ["Militant", "Resolute"],
                    "spiritual": ["Mystic", "Devoted"],
                    "agricultural": ["Nurturing", "Harmonious"],
                    "mercantile": ["Diplomatic", "Wise"],
                    "scholarly": ["Philosophical", "Learned"],
                    "artistic": ["Expressive", "Inspiring"]
                },
                "faction_preference": "priest"
            }
        ]

        characters = []

        for template in role_templates:
            # Get era-appropriate role title
            role = template["roles"].get(era, template["roles"]["bronze_age"])

            # Build personality traits
            traits = template["base_traits"].copy()
            cultural_traits = template["cultural_traits"].get(cultural_focus, [])
            if cultural_traits:
                traits.extend(random.sample(cultural_traits, min(2, len(cultural_traits))))

            # Randomly shuffle and pick 4 unique traits
            random.shuffle(traits)
            traits = traits[:4]

            # Find matching faction
            faction_link = None
            faction_pref = template["faction_preference"]
            for faction in factions:
                if faction_pref in faction["name"].lower():
                    faction_link = faction["name"]
                    break

            # If no match, use a random faction or None
            if not faction_link and factions:
                faction_link = factions[random.randint(0, len(factions) - 1)]["name"]

            # Generate a culturally appropriate name
            name = self._generate_advisor_name(cultural_focus, era, template["role_key"])

            # Generate dialogue sample based on role and culture
            dialogue = self._generate_advisor_dialogue(role, cultural_focus, traits)

            character = {
                "name": name,
                "role": role,
                "faction_link": faction_link,
                "personality_traits": traits,
                "dialogue_sample": dialogue,
                "history": [f"Appointed to the council as {role}."],
                "metrics": {
                    "relationship": random.randint(45, 55),
                    "influence": random.randint(40, 70),
                    "loyalty": random.randint(55, 75)
                },
                "portrait": "placeholder.png"
            }
            characters.append(character)

        return characters

    def _generate_advisor_name(self, cultural_focus, era, role_key):
        """Generate a culturally appropriate advisor name."""
        # Name pools based on cultural focus
        name_pools = {
            "martial": {
                "male": ["Theron", "Kaelen", "Marcus", "Gorak", "Brutus", "Ragnar", "Sigurd", "Ajax"],
                "female": ["Athena", "Valeria", "Brienne", "Astrid", "Cassandra", "Freya", "Hippolyta"]
            },
            "spiritual": {
                "male": ["Zephyr", "Elias", "Aurelius", "Soren", "Alaric", "Caelum", "Thaddeus"],
                "female": ["Seraphina", "Lyra", "Celestia", "Miriam", "Isolde", "Vesta", "Aria"]
            },
            "agricultural": {
                "male": ["Gareth", "Alden", "Borin", "Cedric", "Ewan", "Jasper", "Thorne"],
                "female": ["Ceres", "Flora", "Autumn", "Gaia", "Hazel", "Ivy", "Rowan"]
            },
            "mercantile": {
                "male": ["Lorenzo", "Darius", "Cassius", "Lucien", "Marcellus", "Silvio", "Titus"],
                "female": ["Portia", "Octavia", "Lavinia", "Aurelia", "Livia", "Cordelia", "Emilia"]
            },
            "scholarly": {
                "male": ["Ptolemy", "Archimedes", "Cyrus", "Thales", "Plato", "Solon", "Pytheas"],
                "female": ["Hypatia", "Minerva", "Aspasia", "Diotima", "Eudocia", "Theano", "Arete"]
            },
            "artistic": {
                "male": ["Apollo", "Orpheus", "Lysander", "Thalia", "Perseus", "Damon", "Leander"],
                "female": ["Calliope", "Clio", "Erato", "Melpomene", "Sappho", "Terpsichore", "Urania"]
            }
        }

        # Get appropriate name pool
        pool = name_pools.get(cultural_focus, name_pools["spiritual"])

        # Determine gender based on role (mix of male/female)
        gender = random.choice(["male", "female"])

        # Select name
        first_name = random.choice(pool[gender])

        # Add title based on role
        titles_by_role = {
            "military": ["the Valiant", "the Shield", "Ironfist", "the Unyielding", "Stormborn", "the Defender"],
            "intelligence": ["the Shadow", "the Whisper", "Silvertongue", "the Watcher", "the Veiled", "Nighteye"],
            "spiritual": ["the Blessed", "the Seer", "Lightbearer", "the Faithful", "Stargazer", "the Pure"]
        }

        title_pool = titles_by_role.get(role_key, ["the Wise"])
        title = random.choice(title_pool)

        return f"{first_name} {title}"

    def _generate_advisor_dialogue(self, role, cultural_focus, traits):
        """Generate a sample dialogue line that reflects the advisor's role and personality."""
        # Dialogue templates based on role and culture
        dialogue_templates = {
            "military": {
                "martial": [
                    "Strength is the only currency that matters on the battlefield.",
                    "A sharp blade and sharper mind win wars.",
                    "Our warriors must be ready to strike at a moment's notice."
                ],
                "spiritual": [
                    "The gods favor those who fight with honor.",
                    "Our armies must be blessed before they march.",
                    "Victory comes to the righteous, not merely the strong."
                ],
                "agricultural": [
                    "Protect the harvest, protect the people.",
                    "A strong defense ensures our fields remain fertile.",
                    "Our warriors are shepherds of peace, not wolves of war."
                ],
                "mercantile": [
                    "Military might secures profitable trade routes.",
                    "A merchant's coin is worth nothing without a soldier's sword.",
                    "Strategic positioning is as valuable as gold."
                ],
                "scholarly": [
                    "Knowledge of terrain and tactics wins battles.",
                    "Study our enemies before we engage them.",
                    "Military science is an art form unto itself."
                ],
                "artistic": [
                    "There is beauty in the perfect formation.",
                    "War is a terrible art, but art nonetheless.",
                    "Our banners shall inspire both fear and awe."
                ]
            },
            "intelligence": {
                "martial": [
                    "Information is the first casualty of war—and our greatest weapon.",
                    "Know your enemy before they know themselves.",
                    "Every secret is a dagger waiting to be wielded."
                ],
                "spiritual": [
                    "The spirits reveal truths to those who listen.",
                    "Not all battles are fought with steel, my lord.",
                    "Hidden knowledge is sacred knowledge."
                ],
                "agricultural": [
                    "Even the smallest rumor can blight a harvest.",
                    "Patience and observation yield the ripest fruit.",
                    "Trust must be cultivated like any crop."
                ],
                "mercantile": [
                    "Information is a currency more valuable than gold.",
                    "Every transaction reveals something about the buyer.",
                    "The market whispers secrets to those who listen."
                ],
                "scholarly": [
                    "Knowledge without discretion is dangerous.",
                    "I study what others dare not speak aloud.",
                    "The archive of secrets grows daily."
                ],
                "artistic": [
                    "Deception is an art, and I am its master.",
                    "Every lie must be beautiful to be believed.",
                    "The truth is canvas; manipulation is the brush."
                ]
            },
            "spiritual": {
                "martial": [
                    "The gods demand strength in body and spirit.",
                    "Pray for victory, prepare for battle.",
                    "Our faith is our armor."
                ],
                "spiritual": [
                    "May the divine light guide your path.",
                    "The spirits speak—we must listen.",
                    "Faith is the foundation of all things."
                ],
                "agricultural": [
                    "As we sow, so shall we reap—in this life and the next.",
                    "The earth is sacred, and we its humble stewards.",
                    "Give thanks for the harvest, for it is blessed."
                ],
                "mercantile": [
                    "Prosperity flows from divine favor.",
                    "The gods smile upon fair trade and honest dealings.",
                    "Wealth without virtue is worthless."
                ],
                "scholarly": [
                    "Wisdom and faith are two paths to the same truth.",
                    "The divine mysteries are written in ancient texts.",
                    "Knowledge of the sacred is the highest knowledge."
                ],
                "artistic": [
                    "Beauty is the divine made manifest.",
                    "Our ceremonies are poems written in ritual.",
                    "The gods appreciate elegance as much as devotion."
                ]
            }
        }

        # Determine role category
        role_category = "military"
        if "spy" in role.lower() or "whisper" in role.lower() or "eyes" in role.lower() or "secret" in role.lower() or "scout" in role.lower():
            role_category = "intelligence"
        elif "priest" in role.lower() or "shaman" in role.lower() or "cleric" in role.lower() or "hierophant" in role.lower():
            role_category = "spiritual"

        # Get appropriate dialogue pool
        dialogue_pool = dialogue_templates.get(role_category, {}).get(cultural_focus, [])

        # If no specific dialogue, use generic
        if not dialogue_pool:
            dialogue_pool = [
                "I serve at your pleasure, my lord.",
                "My counsel is yours to consider.",
                "Together, we shall guide our people to greatness."
            ]

        return random.choice(dialogue_pool)

    def _generate_leader_name(self):
        """Generate a random leader name."""
        first_names = [
            "Anya", "Kael", "Theron", "Lyra", "Darius", "Mira", "Orin", "Sera",
            "Aldric", "Elara", "Bran", "Nyx", "Finn", "Rhea", "Cassius", "Aria"
        ]
        titles = [
            "the Wise", "the Bold", "the Just", "the Strong", "the Seer",
            "the Builder", "the Diplomat", "the Warrior", "the Keeper", "the Guide"
        ]

        return f"{random.choice(first_names)}, {random.choice(titles)}"

    def generate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete fantasy world."""
        # Generate all components
        civilization = self.generate_civilization(config)
        culture = self.generate_culture(config)
        religion = self.generate_religion(config)
        technology = self.generate_technology(config)
        world_context = self.generate_world_context(config)
        factions = self.generate_factions(config.get('starting_era', 'bronze_age'), config)
        inner_circle = self.generate_inner_circle(config, factions)

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

