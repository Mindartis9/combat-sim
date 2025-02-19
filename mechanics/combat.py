from __future__ import annotations  
import random
from mechanics.position import Position
from mechanics.position import closest_enemy, distance
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from characters.party_member import PartyMember
    from characters.enemy import Enemy

### ---- COMBAT SETUP ---- ###

def roll_initiative(entities):
    """ Rolls initiative and sorts entities in turn order. """
    for entity in entities:
        entity.current_initiative = random.randint(1, 20) + entity.initiative
    return sorted(entities, key=lambda e: e.current_initiative, reverse=True)


def determine_surprise(entities, surprised_names):
    """ Marks surprised entities at the start of combat. """
    for entity in entities:
        entity.is_surprised = entity.name in surprised_names

### ---- TURN EXECUTION ---- ###
    
def execute_turn(entity, entities, stats):
    """Executes a single turn for an entity, ensuring valid targets."""
    
    if "falling" in entity.conditions:
        entity.apply_fall_damage(stats)
        return  # Falling takes priority
    
    if entity.hitpoints_current <= 0:
        return  # Skip dead entities

    checkTime(entity)
    stats["turns_survived"][entity.name] += 1
            
    if isinstance(entity, PartyMember):
        valid_targets = [e for e in entities if isinstance(e, Enemy) and e.hitpoints_current > 0]
    elif isinstance(entity, Enemy):
        valid_targets = [e for e in entities if isinstance(e, PartyMember) and e.hitpoints_current > 0]
    else:
        valid_targets = []

    prev_position = Position(entity.position.x, entity.position.y, entity.position.z)
    has_moved = False
    
    
    if isinstance(entity, PartyMember) & valid_targets != []:
        if entity.combat_style == "melee":
            target = closest_enemy(entity, valid_targets)
            entity.move_towards(entity, target)
        else:
            target = closest_enemy(entity, valid_targets)
            entity.move_away(entity, target)
        has_moved = True
    elif isinstance(entity, Enemy) & valid_targets != []:
        if entity.combat_style == "melee":
            target = closest_enemy(entity, valid_targets)
            entity.move_towards(entity, target)
        else:
            target = closest_enemy(entity, valid_targets)
            entity.move_away(entity, target)
        has_moved = True
    
    if has_moved:
        if isinstance(entity, PartyMember):    
            process_reactions(entity, Enemy in entities, stats, prev_position)
        else:
            process_reactions(entity, PartyMember in entities, stats, prev_position)
            
    action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
    
    # Perform action
    triggerstop = False
    while triggerstop == False:
        triggerstop = True
        if action["name"] == "Attack" & valid_targets != []:
            attack(entity, target, stats)
        elif action["name"] == "Dodge":
            dodge(entity, stats)
        elif action["name"] == "Disengage":
            disengage(entity, stats)
        elif action["name"] == "Dash":
            dash(entity, stats)
        else:
            action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
            triggerstop = False

    # Ensure actions are properly tracked
    if entity.name not in stats["actions_used"]:
        stats["actions_used"][entity.name] = {}
    if action["name"] not in stats["actions_used"][entity.name]:
        stats["actions_used"][entity.name][action["name"]] = 0
    stats["actions_used"][entity.name][action["name"]] += 1
    
    entity.has_used_reaction = False  # Reset reaction usage
    checkTime(entity)


def simulate_combat(entities):
    """ Runs combat simulation until one side is eliminated and collects statistical data. """
    from characters.party_member import PartyMember  
    from characters.enemy import Enemy  
    
    stats = {
        "winner": None,
        "damage_dealt": {e.name: 0 for e in entities},
        "damage_per_round": {e.name: [] for e in entities},
        "turns_survived": {e.name: 0 for e in entities},
        "actions_used": {e.name: {} for e in entities},
        "reactions_used": {e.name: {} for e in entities},
        "rounds": 0,
    }
    
    while True:
        stats["rounds"] += 1
        entities = [e for e in entities if e.hitpoints_current > 0]  # Remove dead entities

        if not entities:
            break  # If no entities left, combat ends

        for entity in entities:
            execute_turn(entity, entities, stats)

        alive_party = [e for e in entities if isinstance(e, PartyMember) and e.hitpoints_current > 0]
        alive_enemies = [e for e in entities if isinstance(e, Enemy) and e.hitpoints_current > 0]

        if not alive_party:
            return {**stats, "winner": "enemies"}
        if not alive_enemies:
            return {**stats, "winner": "party"}


### ---- COMBAT ACTIONS ---- ###

def attack(attacker, target, stats):
    """Executes an attack, considering hit chance, damage, and resistances."""
    weapon = attacker.weapon
    ability_mod = attacker.calculate_modifier(weapon["modifier"])
    proficiency_bonus = attacker.proficiency_bonus
    num_attacks = attacker.get_attack_count() if hasattr(attacker, "get_attack_count") else 1

    for _ in range(num_attacks):
              
        # Determine attack roll based on advantage/disadvantage system
        advantage_score = attacker.attack_advantage + target.defense_advantage

        if advantage_score > 0:
            attack_roll = max(random.randint(1, 20), random.randint(1, 20))  # Advantage
        elif advantage_score < 0:
            attack_roll = min(random.randint(1, 20), random.randint(1, 20))  # Disadvantage
        else:
            attack_roll = random.randint(1, 20)  # Normal roll

        attack_roll += ability_mod + proficiency_bonus

        hit = attack_roll >= target.ac
        critical_hit = attack_roll == 20
        damage = calculate_damage(weapon["damage_dice"]) * (2 if critical_hit else 1) if hit else 0

        apply_damage(target, damage, weapon["damage_type"], stats, attacker.name)
        
def dodge(character, stats):
    """ Performs the Dodge action, imposing disadvantage on attacks. """
    if 'dodge' not in character.dicoTemporalite:
        character.dicoTemporalite['dodge':[0,0,-1]]
    character.defense_advantage += -1
    character.dicoTemporalite['dodge'][0] = 2

def dash(character, stats):
    """ Performs the Dash action, doubling movement speed. """
    if 'dash' not in character.dicoTemporalite:
        character.dicoTemporalite['dash':[0,0,0]]
    character.speed += character.base_speed
    character.dicoTemporalite['dash'][0] = 1

def disengage(character, stats):
    """ Performs the Disengage action, avoiding opportunity attacks. """
    if 'disengage' not in character.dicoTemporalite:
        character.dicoTemporalite['disengage':[0,0,0]]    
    character.can_be_opportunity_attacked = False
    character.dicoTemporalite['disengage'][0] = 1

def opportunity_attack(attacker, target, stats):
    """Executes an opportunity attack when a target moves out of melee range."""
    if attacker.combat_style != "melee" or attacker.has_used_reaction:
        return  # Only melee attackers can make opportunity attacks and must have a reaction available

    attack(attacker, target, stats)
    
    # Mark reaction as used
    attacker.has_used_reaction = True

    # Log reaction usage
    stats["reactions_used"].setdefault(attacker.name, {}).setdefault("Opportunity Attack", 0)
    stats["reactions_used"][attacker.name]["Opportunity Attack"] += 1


### ---- UTILITY FUNCTIONS ---- ###

def assign_default_actions(character):
    """ Assigns default combat actions to a character. """
    character.actions = [
        {"name": "Attack", "mechanic": attack, "parameters": {}, "weight": 10, "target_required": True},
        {"name": "Dodge", "mechanic": dodge, "parameters": {}, "weight": 1},
        {"name": "Disengage", "mechanic": disengage, "parameters": {}, "weight": 1},
        {"name": "Dash", "mechanic": dash, "parameters": {}, "weight": 1},
    ]

def process_reactions(moving_entity, entities, stats, previous_position):
    """ Checks and triggers opportunity attacks."""
    for entity in entities:
        if entity == moving_entity or entity.hitpoints_current <= 0:
            continue
        
        if entity.can_take_reaction() and distance(previous_position, entity.position) <= entity.weapon["range"] and distance(moving_entity.position, entity.position) > entity.weapon["range"]:
            if "Opportunity Attack" in entity.reactions:
                entity.reactions["Opportunity Attack"](entity, moving_entity, stats)
                entity.has_used_reaction = True


def calculate_damage(damage_dice):
    """ Rolls damage dice. """
    num, die = map(int, damage_dice.split('d'))
    return sum(random.randint(1, die) for _ in range(num))

def apply_damage(target, damage, damage_type, stats, attacker_name):
    """Applies damage, considering resistances and immunities."""
    if damage_type in target.immunities:
        damage = 0
    elif damage_type in target.resistances:
        damage = max(1, damage // 2)
    else:
        damage = max(1, damage)

    # Subtract HP and track stats
    target.hitpoints_current = max(target.hitpoints_current - damage, 0)

    # Ensure stats tracking works
    if attacker_name not in stats["damage_dealt"]:
        stats["damage_dealt"][attacker_name] = 0
    stats["damage_dealt"][attacker_name] += damage

    # Track damage per round
    stats["damage_per_round"].setdefault(attacker_name, []).append(damage)

def checkTime(characters):
    
    for mecha in characters.dicoTemporalite:
        if mecha[0] > 0:
            mecha[0] -= 1

        if mecha[0] == 0:
            characters.attack_advantage -= mecha[1]
            characters.defense_advantage -= mecha[2]
        
        if (mecha == 'dash' and mecha[0] == 0):
            characters.speed -= characters.base_speed
            
        if (mecha == 'disengage' and mecha[0] == 0):
            characters.can_be_opportunity_attacked = True
    
