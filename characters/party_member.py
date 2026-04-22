from __future__ import annotations
from characters.base_character import Character
from typing import TYPE_CHECKING, List
import json
import os

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
        
        # Spellcasting data
        self.spellcasting_ability = None
        self.caster_progression = None
        self.spell_slots = []
        self.known_spells = []
        self.prepared_spells = []
        self.cantrips_known = 0
        
        self._initialize_spellcasting()
    
    def _initialize_spellcasting(self):
        """Initialize spellcasting based on class."""
        class_data = self._load_class_data()
        if not class_data:
            return
            
        # Set spellcasting ability
        if 'spellcastingAbility' in class_data:
            self.spellcasting_ability = class_data['spellcastingAbility']
        
        # Set caster progression
        if 'casterProgression' in class_data:
            self.caster_progression = class_data['casterProgression']
        
        # Initialize spell slots based on progression
        if self.caster_progression and self.level > 0:
            self._set_spell_slots()
        
        # Set cantrips known
        if 'cantripProgression' in class_data and len(class_data['cantripProgression']) >= self.level:
            self.cantrips_known = class_data['cantripProgression'][self.level - 1]
        
        # Initialize some default spells for testing
        self._initialize_default_spells()
    
    def _load_class_data(self):
        """Load class data from JSON files."""
        try:
            class_file = f"class-{self.char_class.lower()}.json"
            filepath = os.path.join(os.path.dirname(__file__), '..', 'data', 'class', class_file)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if 'class' in data and data['class']:
                        return data['class'][0]  # Take first class entry
        except:
            pass
        return None
    
    def _set_spell_slots(self):
        """Set spell slots based on caster progression."""
        from mechanics.spells import SPELL_SLOTS, HALF_SPELL_SLOTS, THIRD_SPELL_SLOTS, PACT_SPELL_SLOTS
        
        if self.caster_progression == 'full':
            slots = SPELL_SLOTS.get(self.level, [])
        elif self.caster_progression in ['half', '1/2']:
            slots = HALF_SPELL_SLOTS.get(self.level, [])
        elif self.caster_progression == 'third':
            slots = THIRD_SPELL_SLOTS.get(self.level, [])
        elif self.caster_progression == 'pact':
            slots = PACT_SPELL_SLOTS.get(self.level, [])
        else:
            slots = []
        
        self.spell_slots = slots
    
    def can_cast_spells(self) -> bool:
        """Check if character can cast spells."""
        return self.spellcasting_ability is not None and len(self.spell_slots) > 0
    
    def _initialize_default_spells(self):
        """Initialize some default spells for testing purposes."""
        from mechanics.spells import CLASS_SPELL_LISTS, SPELL_DATA
        max_spell_level = len(self.spell_slots) if self.spell_slots else 0
        class_spells = CLASS_SPELL_LISTS.get(self.char_class, [])
        self.known_spells = [spell['name'] for spell in SPELL_DATA if spell['name'] in class_spells and spell['level'] <= max_spell_level]
    
    def get_class_info(self) -> str:
        """Returns a formatted string of the character's class and subclass."""
        return f"{self.char_class} ({self.subclass}) - Level {self.level}"
