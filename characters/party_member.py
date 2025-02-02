from __future__ import annotations
from characters.base_character import Character
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from mechanics.combat import opportunity_attack 

class PartyMember(Character):
    def __init__(self, name, char_class, subclass, level, ability_scores, ac, initiative, speed, hitpoints, 
                 saving_throws, proficiency_bonus, features_traits=None, actions=None, size="Medium", 
                 weapon=None, combat_style="melee", flying_speed=0):
        """Initializes a PartyMember with class-specific attributes."""
        super().__init__(name, ability_scores, ac, initiative, speed, hitpoints, size, weapon, combat_style, flying_speed)
        
        self.char_class = char_class
        self.subclass = subclass
        self.level = level
        self.saving_throws = saving_throws
        self.proficiency_bonus = proficiency_bonus
        self.features_traits = features_traits if features_traits else []
        self.actions = actions if actions else []
    
    def get_class_info(self) -> str:
        """Returns a formatted string of the character's class and subclass."""
        return f"{self.char_class} ({self.subclass}) - Level {self.level}"
