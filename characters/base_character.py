from __future__ import annotations  
from mechanics.position import Position
import random

class Character:
    def __init__(self, name, ability_scores, ac, initiative, speed, hitpoints, size, weapon, combat_style, flying_speed=0):
        from mechanics.combat import opportunity_attack  # Delayed import to avoid circular import issues
        
        self.name = name
        self.ability_scores = ability_scores
        self.ac = ac
        self.initiative = initiative
        self.speed = speed
        self.base_speed = speed
        self.hitpoints = hitpoints
        self.size = size
        self.weapon = weapon
        self.combat_style = combat_style  # "melee" or "ranged"
        self.flying_speed = flying_speed  # Default to 0 if ground-bound
        self.is_flying = False  # Default ground state
        self.attack_advantage = 0  # Tracks if attacks made by this character have advantage/disadvantage
        self.defense_advantage = 0  # Tracks if attacks against this character have advantage/disadvantage
        
        # Status Tracking
        self.conditions = set()
        self.resistances = set()
        self.immunities = set()
        self.position = None  # Assigned later
        
        # Combat Mechanics
        self.is_surprised = False
        self.can_be_opportunity_attacked = True
        self.dicoTemporalite = {}

        
        # **Fix: Initialize self.reactions before assignment**
        self.reactions = {}  
        self.reactions["Opportunity Attack"] = opportunity_attack
        self.has_used_reaction = False
        
    def can_take_reaction(self) -> bool:
        """Determines if this character can take a reaction this round."""
        return not self.has_used_reaction and not self.is_surprised 
    
    def start_falling(self):
        """Starts falling if airborne without flying speed."""
        if self.position.z > 0 and self.flying_speed == 0:
            self.conditions.add("falling")
            self.fall_distance = 0  # Reset fall distance

    def apply_fall_damage(self, stats):
        """Applies fall damage upon hitting the ground."""
        if "falling" not in self.conditions:
            return
        
        self.fall_distance = min(self.fall_distance + 500, self.position.z)
        if self.position.z - self.fall_distance <= 0:
            fall_damage = (self.fall_distance // 10) * random.randint(1, 6)  # 1d6 per 10 ft
            self.hitpoints = max(self.hitpoints - fall_damage, 0)
            stats["damage_dealt"].setdefault(self.name, 0)
            stats["damage_dealt"][self.name] += fall_damage
            self.conditions.discard("falling")
            self.fall_distance = 0
            self.position.z = 0

    def move_towards_target(self, target):
        """Moves towards the target if out of melee range."""
        if self.combat_style == "melee" and self.position.distance_to(target.position) > self.weapon["range"]:
            self.position.move_towards(target.position, self.flying_speed if self.is_flying else self.speed)

    def move_away_from_target(self, target):
        """Moves away from the target if ranged."""
        if self.combat_style == "ranged":
            self.position.move_away(target.position, self.speed, max(self.weapon["range"] - self.speed, 5))

    def start_flying(self):
        """Enables flying movement if possible."""
        self.is_flying = self.flying_speed > 0
        if not self.is_flying:
            self.start_falling()

    def calculate_modifier(self, ability: str) -> int:
        """Returns the ability modifier based on ability scores."""
        if ability not in self.ability_scores:
            raise ValueError(f"Invalid ability: {ability}")
        return (self.ability_scores[ability] - 10) // 2
