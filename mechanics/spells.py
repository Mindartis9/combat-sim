import json
import os
import random
from typing import Dict, List, Optional, Any
from characters.base_character import Character

# Class spell lists (simplified for common spells)
CLASS_SPELL_LISTS = {
    'Wizard': [
        'Fire Bolt', 'Magic Missile', 'Fireball', 'Lightning Bolt', 'Cone of Cold',
        'Chain Lightning', 'Disintegrate', 'Power Word Kill', 'Wish',
        'Cure Wounds', 'Healing Word', 'Revivify'
    ],
    'Ranger': [
        'Hunter\'s Mark', 'Goodberry', 'Cure Wounds', 'Entangle', 'Pass Without Trace',
        'Conjure Animals', 'Polymorph', 'Healing Word'
    ],
    'Cleric': [
        'Cure Wounds', 'Healing Word', 'Heal', 'Mass Heal', 'Revivify', 'Raise Dead',
        'Spiritual Weapon', 'Inflict Wounds', 'Guiding Bolt', 'Spirit Guardians'
    ],
    # Add more classes as needed
}

# Spell slot table by level (full caster)
SPELL_SLOTS = {
    1: [2],
    2: [3],
    3: [4, 2],
    4: [4, 3],
    5: [4, 3, 2],
    6: [4, 3, 3],
    7: [4, 3, 3, 1],
    8: [4, 3, 3, 2],
    9: [4, 3, 3, 3, 1],
    10: [4, 3, 3, 3, 2],
    11: [4, 3, 3, 3, 2, 1],
    12: [4, 3, 3, 3, 2, 1],
    13: [4, 3, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 2, 1, 1, 1, 1, 1],
    20: [4, 3, 3, 3, 2, 1, 1, 1, 1, 1]
}

# Half caster spell slots
HALF_SPELL_SLOTS = {
    1: [],
    2: [2],
    3: [3],
    4: [3],
    5: [4, 2],
    6: [4, 2],
    7: [4, 3],
    8: [4, 3],
    9: [4, 3, 2],
    10: [4, 3, 2],
    11: [4, 3, 3],
    12: [4, 3, 3],
    13: [4, 3, 3, 1],
    14: [4, 3, 3, 1],
    15: [4, 3, 3, 2],
    16: [4, 3, 3, 2],
    17: [4, 3, 3, 2, 1],
    18: [4, 3, 3, 2, 1],
    19: [4, 3, 3, 2, 1],
    20: [4, 3, 3, 2, 1]
}

# Third caster spell slots (e.g., artificer)
THIRD_SPELL_SLOTS = {
    1: [],
    2: [2],
    3: [3],
    4: [3],
    5: [4, 2],
    6: [4, 2],
    7: [4, 3],
    8: [4, 3],
    9: [4, 3, 2],
    10: [4, 3, 2],
    11: [4, 3, 3],
    12: [4, 3, 3],
    13: [4, 3, 3, 1],
    14: [4, 3, 3, 1],
    15: [4, 3, 3, 2],
    16: [4, 3, 3, 2],
    17: [4, 3, 3, 2, 1],
    18: [4, 3, 3, 2, 1],
    19: [4, 3, 3, 2, 1],
    20: [4, 3, 3, 2, 1]
}

# Pact magic spell slots (warlock)
PACT_SPELL_SLOTS = {
    1: [1],
    2: [2],
    3: [2],
    4: [2],
    5: [2, 1],
    6: [2, 1],
    7: [2, 1],
    8: [2, 1],
    9: [2, 1],
    10: [2, 1],
    11: [3, 1],
    12: [3, 1],
    13: [3, 1],
    14: [3, 1],
    15: [3, 1],
    16: [3, 1],
    17: [4, 1],
    18: [4, 1],
    19: [4, 1],
    20: [4, 1]
}

# Half caster progression (paladin, ranger)
HALF_SPELL_SLOTS = {
    1: [],
    2: [2],
    3: [3],
    4: [3],
    5: [4, 2],
    6: [4, 2],
    7: [4, 3, 1],
    8: [4, 3, 2],
    9: [4, 3, 3, 1],
    10: [4, 3, 3, 2],
    11: [4, 3, 3, 2, 1],
    12: [4, 3, 3, 2, 1],
    13: [4, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 2, 1, 1, 1, 1],
    19: [4, 3, 3, 2, 1, 1, 1, 1, 1],
    20: [4, 3, 3, 2, 1, 1, 1, 1, 1]
}

# Third caster progression (artificer)
THIRD_SPELL_SLOTS = {
    1: [2],
    2: [2],
    3: [3],
    4: [3],
    5: [4, 2],
    6: [4, 2],
    7: [4, 3, 1],
    8: [4, 3, 2],
    9: [4, 3, 3, 1],
    10: [4, 3, 3, 2],
    11: [4, 3, 3, 2, 1],
    12: [4, 3, 3, 2, 1],
    13: [4, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 2, 1, 1, 1, 1],
    19: [4, 3, 3, 2, 1, 1, 1, 1, 1],
    20: [4, 3, 3, 2, 1, 1, 1, 1, 1]
}

# Pact magic (warlock)
PACT_SPELL_SLOTS = {
    1: [1],
    2: [2],
    3: [3],
    4: [3],
    5: [4, 2],
    6: [4, 2],
    7: [4, 3, 1],
    8: [4, 3, 2],
    9: [4, 3, 3, 1],
    10: [4, 3, 3, 2],
    11: [4, 3, 3, 2, 1],
    12: [4, 3, 3, 2, 1],
    13: [4, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 2, 1, 1, 1, 1],
    19: [4, 3, 3, 2, 1, 1, 1, 1, 1],
    20: [4, 3, 3, 2, 1, 1, 1, 1, 1]
}

# Cantrip progression for full casters
CANTRIP_PROGRESSION = [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

# Global spell database
SPELL_DATA = []

def load_spells():
    """Load all spells from JSON files into the global database."""
    global SPELL_DATA
    if SPELL_DATA:
        return SPELL_DATA  # Already loaded

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'spells')
    index_file = os.path.join(data_dir, 'index.json')

    with open(index_file, 'r') as f:
        index = json.load(f)

    for source, filename in index.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                if 'spell' in data:
                    SPELL_DATA.extend(data['spell'])

    return SPELL_DATA

def get_spell(spell_name: str) -> Optional[Dict]:
    """Get a spell by name from the database."""
    load_spells()
    for spell in SPELL_DATA:
        if spell['name'].lower() == spell_name.lower():
            return spell
    return None

def get_spell_range(spell: Dict) -> int:
    """Extract range from spell data."""
    if 'range' in spell:
        range_data = spell['range']
        if range_data.get('type') == 'point' and 'distance' in range_data:
            dist = range_data['distance']
            if dist.get('type') == 'feet':
                return dist.get('amount', 0)
            elif dist.get('type') == 'touch':
                return 5  # Touch range
            elif dist.get('type') == 'self':
                return 0  # Self range
    return 0

def get_spell_area(spell: Dict) -> Optional[Dict]:
    """Extract area of effect from spell data."""
    if 'area' in spell:
        return spell['area']
    return None

def get_spell_damage(spell: Dict, caster_level: int = 1) -> Optional[Dict]:
    """Extract damage information from spell."""
    damage_info = {}

    # Check scalingLevelDice for level-based damage
    if 'scalingLevelDice' in spell:
        scaling = spell['scalingLevelDice']
        label = scaling.get('label', '')
        scale_dict = scaling.get('scaling', {})

        # Find the appropriate level
        levels = sorted([int(k) for k in scale_dict.keys()])
        applicable_level = max([l for l in levels if l <= caster_level], default=levels[0] if levels else 1)
        damage_info['dice'] = scale_dict.get(str(applicable_level), '1d6')
        damage_info['type'] = label.split()[0] if ' ' in label else label  # Extract damage type

    # Check entries for damage mentions
    elif 'entries' in spell:
        for entry in spell['entries']:
            if isinstance(entry, str) and '{@damage' in entry:
                # Simple parsing for damage
                import re
                damage_match = re.search(r'\{@damage ([^}]+)\}', entry)
                if damage_match:
                    damage_info['dice'] = damage_match.group(1)
                    # Try to find damage type
                    if 'acid' in entry.lower():
                        damage_info['type'] = 'acid'
                    elif 'fire' in entry.lower():
                        damage_info['type'] = 'fire'
                    elif 'cold' in entry.lower():
                        damage_info['type'] = 'cold'
                    elif 'lightning' in entry.lower():
                        damage_info['type'] = 'lightning'
                    elif 'poison' in entry.lower():
                        damage_info['type'] = 'poison'
                    elif 'necrotic' in entry.lower():
                        damage_info['type'] = 'necrotic'
                    elif 'radiant' in entry.lower():
                        damage_info['type'] = 'radiant'
                    elif 'psychic' in entry.lower():
                        damage_info['type'] = 'psychic'
                    elif 'force' in entry.lower():
                        damage_info['type'] = 'force'
                    elif 'thunder' in entry.lower():
                        damage_info['type'] = 'thunder'
                    break

    return damage_info if damage_info else None

def get_spell_saving_throw(spell: Dict) -> Optional[str]:
    """Extract saving throw from spell."""
    if 'savingThrow' in spell and spell['savingThrow']:
        return spell['savingThrow'][0]  # Take first saving throw
    return None

def get_spell_conditions(spell: Dict) -> List[str]:
    """Extract conditions inflicted by spell."""
    conditions = []
    if 'entries' in spell:
        entries_text = ' '.join([e if isinstance(e, str) else str(e) for e in spell['entries']]).lower()
        condition_keywords = ['stunned', 'paralyzed', 'poisoned', 'blinded', 'deafened', 'frightened', 'charmed', 'restrained', 'prone', 'grappled']
        for condition in condition_keywords:
            if condition in entries_text:
                conditions.append(condition)
    return conditions

def is_healing_spell(spell: Dict) -> bool:
    """Determine if a spell is a healing spell."""
    spell_name = spell.get('name', '').lower()
    healing_keywords = ['heal', 'cure', 'aid', 'regenerate', 'restoration', 'life']
    for keyword in healing_keywords:
        if keyword in spell_name:
            return True
    
    if 'entries' in spell:
        entries_text = ' '.join([e if isinstance(e, str) else str(e) for e in spell['entries']]).lower()
        if 'hit point' in entries_text and ('restore' in entries_text or 'regain' in entries_text or 'heal' in entries_text):
            return True
    return False

def is_resurrection_spell(spell: Dict) -> bool:
    """Determine if a spell is a resurrection spell."""
    spell_name = spell.get('name', '').lower()
    resurrection_keywords = ['resurrection', 'revify', 'revivify', 'true resurrection', 'raise dead']
    for keyword in resurrection_keywords:
        if keyword in spell_name:
            return True
    return False

def get_healing_amount(spell: Dict, caster_level: int = 1) -> int:
    """Extract healing amount from a healing spell."""
    # Similar to damage extraction, look for healing dice
    if 'scalingLevelDice' in spell:
        scaling = spell['scalingLevelDice']
        scale_dict = scaling.get('scaling', {})
        levels = sorted([int(k) for k in scale_dict.keys()])
        applicable_level = max([l for l in levels if l <= caster_level], default=levels[0] if levels else 1)
        dice_str = scale_dict.get(str(applicable_level), '1d6')
        return calculate_spell_damage(dice_str)
    
    # Parse from entries
    if 'entries' in spell:
        for entry in spell['entries']:
            if isinstance(entry, str) and '{@damage' in entry:
                import re
                heal_match = re.search(r'regain.*?({@damage ([^}]+)}|(\d+d\d+))', entry)
                if heal_match:
                    dice_str = heal_match.group(2) or heal_match.group(3)
                    if dice_str:
                        return calculate_spell_damage(dice_str)
            elif isinstance(entry, str) and any(word in entry.lower() for word in ['regain', 'restore']):
                import re
                heal_match = re.search(r'(\d+d\d+|\d+) hit point', entry.lower())
                if heal_match:
                    return calculate_spell_damage(heal_match.group(1))
    
    return 0

def calculate_spell_damage(damage_dice: str) -> int:
    """Calculate damage from dice string like '2d6'."""
    if not damage_dice:
        return 0
    try:
        num, die = map(int, damage_dice.split('d'))
        return sum(random.randint(1, die) for _ in range(num))
    except:
        return 0

def cast_spell(caster: Character, spell_name: str, target: Character, stats: Dict):
    """Cast a spell at a target."""
    spell = get_spell(spell_name)
    if not spell:
        return False

    # Check range
    spell_range = get_spell_range(spell)
    if spell_range > 0 and caster.position.distance_to(target.position) > spell_range:
        return False  # Out of range

    # Get spell level and check slots
    spell_level = spell.get('level', 0)
    if hasattr(caster, 'spell_slots') and spell_level > 0:
        if spell_level >= len(caster.spell_slots) or caster.spell_slots[spell_level] <= 0:
            return False  # No slots available
        caster.spell_slots[spell_level] -= 1

    # Determine spell type
    is_healing = is_healing_spell(spell)
    is_resurrection = is_resurrection_spell(spell)

    # Check for spell attack
    spell_attack = spell.get('spellAttack', [])
    hit = True  # Default to hit
    if spell_attack and not is_healing:
        # Calculate spell attack modifier
        spell_mod = caster.ability_scores.get(caster.spellcasting_ability.upper(), 0) // 2 - 5
        attack_roll = random.randint(1, 20) + caster.proficiency_bonus + spell_mod
        if attack_roll < target.ac:
            hit = False

    # Get saving throw
    save_type = get_spell_saving_throw(spell)
    save_success = False
    if save_type and not is_healing:
        ability_key = save_type.upper()[:3]  # 'dex' for dexterity
        save_mod = target.ability_scores.get(ability_key, 10) // 2 - 5
        if ability_key in getattr(target, 'saving_throws', []):
            save_mod += getattr(target, 'proficiency_bonus', 0)
        save_roll = random.randint(1, 20) + save_mod
        save_dc = 8 + caster.proficiency_bonus + (caster.ability_scores.get(caster.spellcasting_ability.upper(), 0) // 2 - 5)
        save_success = save_roll >= save_dc

    # Apply effects based on spell type
    spell_effectiveness = {'spell': spell_name, 'target': target.name, 'success': False, 'effect_type': None, 'amount': 0}

    if is_healing:
        # Healing spells always succeed on allies
        healing = get_healing_amount(spell, getattr(caster, 'level', 1))
        if healing > 0:
            target.hit_points = min(target.max_hp, target.hit_points + healing)
            spell_effectiveness['success'] = True
            spell_effectiveness['effect_type'] = 'healing'
            spell_effectiveness['amount'] = healing
    elif is_resurrection:
        # Resurrection spell - restore dead character to life
        if target.hit_points <= 0:
            target.hit_points = max(1, target.max_hp // 2)  # Resurrect at half HP
            spell_effectiveness['success'] = True
            spell_effectiveness['effect_type'] = 'resurrection'
            spell_effectiveness['amount'] = target.hit_points
    else:
        # Damage spells
        effects_apply = hit and not (save_type and save_success)

        if effects_apply:
            # Apply damage
            damage_info = get_spell_damage(spell, getattr(caster, 'level', 1))
            if damage_info:
                damage = calculate_spell_damage(damage_info['dice'])
                damage_type = damage_info.get('type', 'force')
                from mechanics.combat import apply_damage
                apply_damage(target, damage, damage_type, stats, caster.name)
                spell_effectiveness['success'] = True
                spell_effectiveness['effect_type'] = 'damage'
                spell_effectiveness['amount'] = damage

            # Apply conditions
            conditions = get_spell_conditions(spell)
            for condition in conditions:
                target.conditions.add(condition)
                if conditions:
                    spell_effectiveness['effect_type'] = 'damage_and_condition'

    # Track spell usage and effectiveness
    stats["spells_cast"].setdefault(caster.name, {}).setdefault(spell_name, 0)
    stats["spells_cast"][caster.name][spell_name] += 1
    
    # Track spell effectiveness
    if 'spell_effectiveness' not in stats:
        stats['spell_effectiveness'] = []
    stats['spell_effectiveness'].append(spell_effectiveness)

    return True