from __future__ import annotations
from characters.base_character import Character
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from mechanics.combat import opportunity_attack  # Delayed import

class Enemy(Character):
    def __init__(self, name, ability_scores, ac, initiative, speed, hitpoints, saving_throws, proficiency_bonus, 
                 features_traits=None, actions=None, size="Medium", weapon=None, combat_style="melee", 
                 multiattack=False, attack_count=1, flying_speed=0):
        """Initializes an Enemy character with combat attributes."""
        super().__init__(name, ability_scores, ac, initiative, speed, hitpoints, size, weapon, combat_style, flying_speed)
        
        self.saving_throws = saving_throws
        self.proficiency_bonus = proficiency_bonus
        self.features_traits = features_traits if features_traits else []
        self.actions = actions if actions else []
        self.multiattack = multiattack
        self.attack_count = max(1, attack_count)  # Ensures at least 1 attack
        
    def get_attack_count(self) -> int:
        """Returns the number of attacks an enemy can make in one turn."""
        return self.attack_count if self.multiattack else 1
