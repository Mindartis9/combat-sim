from __future__ import annotations  
import random
from mechanics.position import Position
from mechanics.position import closest_enemy, distance
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from characters.party_member import PartyMember
    from characters.enemy import Enemy

# runtime imports are placed inside functions to avoid circular import problems

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
    """Executes a single turn for an entity, ensuring valid targets.

    Movement now favors the closest foe while attack selection will ideally
    hit the lowest‑HP adversary in range.  Creatures with low health attempt to
    flee and use Disengage, and overlapping positions are prevented.
    """
    # import here to resolve circular reference issues
    from characters.party_member import PartyMember
    from characters.enemy import Enemy

    LOW_HP_RATIO = 0.3  # threshold for retreat behaviour

    # if a non-flying creature is above ground, it should start falling
    if entity.position.z > 0 and not getattr(entity, 'is_flying', False) and "falling" not in entity.conditions:
        entity.start_falling()

    if "falling" in entity.conditions:
        entity.apply_fall_damage(stats)
        return  # Falling takes priority

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

    # flee if low on HP: move away from nearest foe and force Disengage
    fled = False
    if entity.hitpoints_current <= entity.hitpoints_maximum * LOW_HP_RATIO and valid_targets:
        nearest = closest_enemy(entity, valid_targets)
        # retreat by full speed
        entity.position.move_away(nearest.position, entity.speed)
        has_moved = True
        fled = True
        # immediately take disengage action and finish turn
        disengage(entity)
        # track the action
        stats["actions_used"].setdefault(entity.name, {}).setdefault("Disengage", 0)
        stats["actions_used"][entity.name]["Disengage"] += 1
        entity.has_used_reaction = False
        checkTime(entity)
        return

    # choose a target if any are available
    target = None
    movement_target = None
    if valid_targets and not fled:
        # closest enemy determines movement
        movement_target = closest_enemy(entity, valid_targets)
        # attack preference: choose lowest hp among those in weapon range
        # look for any target already within weapon range
        in_range = [t for t in valid_targets if entity.position.distance_to(t.position) <= entity.weapon.get("range", 0)]
        if in_range:
            # prefer the one with lowest hit points
            target = min(in_range, key=lambda t: t.hitpoints_current)
        else:
            # fall back to closest foe for both movement and attack
            target = movement_target

        # movement logic based on combat style and distance to movement_target
        if movement_target:
            if entity.combat_style == "melee":
                if entity.position.distance_to(movement_target.position) > entity.weapon["range"]:
                    entity.move_towards_target(movement_target)
                    has_moved = True
            elif entity.combat_style == "ranged":
                # maintain at least weapon range
                if entity.position.distance_to(movement_target.position) < entity.weapon["range"]:
                    entity.move_away_from_target(movement_target)
                    has_moved = True

    # collision prevention: don't occupy the same square
    if has_moved:
        for other in entities:
            if other is not entity and other.position and entity.position and \
               other.position.x == entity.position.x and other.position.y == entity.position.y and other.position.z == entity.position.z:
                # undo move by restoring coordinates rather than replacing object
                entity.position.x = prev_position.x
                entity.position.y = prev_position.y
                entity.position.z = prev_position.z
                has_moved = False
                break

    if has_moved:
        # always check reactions from all other entities
        process_reactions(entity, entities, stats, prev_position)
    
    # if we fled we already chose action
    if not fled:
        action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
    
    # Perform action, ensure attack has a target
    while True:
        if action["name"] == "Attack":
            if target is not None:
                attack(entity, target, stats)
                break
            else:
                # pick another action if no valid target
                action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
                continue
        elif action["name"] == "Dodge":
            dodge(entity)
            break
        elif action["name"] == "Disengage":
            disengage(entity)
            break
        elif action["name"] == "Dash":
            dash(entity)
            break
        elif action["name"] == "Magic":
            if target is not None:
                magic(entity, target, stats)
                break
            else:
                # pick another action if no valid target
                action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
                continue
        else:
            action = random.choices(entity.actions, weights=[a.get("weight", 1) for a in entity.actions], k=1)[0]
            continue
    
    if has_moved:
        # always check reactions from all other entities
        process_reactions(entity, entities, stats, prev_position)
            
    # Ensure actions are properly tracked
    if entity.name not in stats["actions_used"]:
        stats["actions_used"][entity.name] = {}
    if action["name"] not in stats["actions_used"][entity.name]:
        stats["actions_used"][entity.name][action["name"]] = 0
    stats["actions_used"][entity.name][action["name"]] += 1
    
    entity.has_used_reaction = False  # Reset reaction usage
    checkTime(entity)


def simulate_combat(entities, stats):
    """ Runs combat simulation until one side is eliminated and collects statistical data. """
    from characters.party_member import PartyMember  
    from characters.enemy import Enemy  
    
    # keep original order/names to report hp_end
    original_names = [e.name for e in entities]

    for entity in entities:
        stats["initiative_order"][entity.name] = entities.index(entity)
    
    while True:
        stats["rounds"] += 1
        # reset per-round damage counter
        stats["damage_this_round"] = 0

        entities = [e for e in entities if e.hitpoints_current > 0]  # Remove dead entities

        # record survival at start of round (optional)
        for name in original_names:
            alive = any(e.name == name and e.hitpoints_current > 0 for e in entities)
            stats.setdefault("survival_sequence", {}).setdefault(name, []).append(alive)

        for entity in entities:
            execute_turn(entity, entities, stats)

        if stats.get("damage_this_round", 0) == 0:
            stats["turns_no_damage"] += 1

        alive_party = [e for e in entities if isinstance(e, PartyMember) and e.hitpoints_current > 0]
        alive_enemies = [e for e in entities if isinstance(e, Enemy) and e.hitpoints_current > 0]
        if not alive_party:
            # record hp_end for all
            for name in original_names:
                found = next((e for e in entities if e.name == name), None)
                stats["hp_end"][name] = found.hitpoints_current if found else 0
            return {**stats, "winner": "enemies"}
        if not alive_enemies:
            for name in original_names:
                found = next((e for e in entities if e.name == name), None)
                stats["hp_end"][name] = found.hitpoints_current if found else 0
            return {**stats, "winner": "party"}


### ---- COMBAT ACTIONS ---- ###

def attack(attacker, target, stats):
    """Executes an attack, considering hit chance, damage, and resistances.

    Also updates various combat statistics (attack counts, crits, round damage).
    """
    weapon = attacker.weapon
    ability_mod = attacker.calculate_modifier(weapon["modifier"])
    proficiency_bonus = attacker.proficiency_bonus
    num_attacks = attacker.get_attack_count() if hasattr(attacker, "get_attack_count") else 1

    # initialize counters for attacker if needed
    stats["attack_count"].setdefault(attacker.name, 0)
    stats["crit_count"].setdefault(attacker.name, 0)

    for _ in range(num_attacks):
        stats["attack_count"][attacker.name] += 1
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
        if critical_hit:
            stats["crit_count"][attacker.name] += 1
            stats["total_crits"] += 1
        damage = calculate_damage(weapon["damage_dice"]) * (2 if critical_hit else 1) if hit else 0

        apply_damage(target, damage, weapon["damage_type"], stats, attacker.name)

def dodge(character):
    """ Performs the Dodge action, imposing disadvantage on attacks. """
    if 'dodge' not in character.dicoTemporalite:
        character.dicoTemporalite['dodge'] = [0, 0, -1]
    character.defense_advantage -= 1
    character.dicoTemporalite['dodge'][0] = 2

def dash(character):
    """ Performs the Dash action, doubling movement speed. """
    if 'dash' not in character.dicoTemporalite:
        character.dicoTemporalite['dash'] = [0, 0, 0]
    character.speed += character.base_speed
    character.dicoTemporalite['dash'][0] = 1

def disengage(character):
    """ Performs the Disengage action, avoiding opportunity attacks. """
    if 'disengage' not in character.dicoTemporalite:
        character.dicoTemporalite['disengage'] = [0, 0, 0]
    character.can_be_opportunity_attacked = False
    character.dicoTemporalite['disengage'][0] = 1

def magic(character, target, stats):
    """ Performs the Magic action, casting a random spell at the target. """
    if not hasattr(character, 'can_cast_spells') or not character.can_cast_spells():
        return  # Not a spellcaster
    
    # Choose a random spell from known/prepared spells
    available_spells = getattr(character, 'prepared_spells', []) + getattr(character, 'known_spells', [])
    if not available_spells:
        # Default to a basic cantrip if no spells known
        available_spells = ['fire bolt', 'shocking grasp', 'acid splash']
    
    spell_name = random.choice(available_spells)
    
    # Import and cast spell
    from mechanics.spells import cast_spell
    cast_spell(character, spell_name, target, stats)

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
        {"name": "Attack", "mechanic": attack, "weight": 10, "target_required": True},
        {"name": "Dodge", "mechanic": dodge, "weight": 1},
        {"name": "Disengage", "mechanic": disengage, "weight": 1},
        {"name": "Dash", "mechanic": dash, "weight": 1},
    ]
    
    # Add Magic action for spellcasters
    if hasattr(character, 'can_cast_spells') and character.can_cast_spells():
        character.actions.append({"name": "Magic", "mechanic": magic, "weight": 50, "target_required": True})

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
    if damage <= 0:
        return  # no damage to apply

    if damage_type in target.immunities:
        damage = 0
    elif damage_type in target.resistances:
        # halved damage but at least 1 if original >0
        damage = max(1, damage // 2)

    # Subtract HP and track stats
    target.hitpoints_current = max(target.hitpoints_current - damage, 0)

    # global damage counter for the current round (set by simulate_combat)
    if "damage_this_round" in stats:
        stats["damage_this_round"] += damage

    # Ensure stats tracking works
    if attacker_name not in stats["damage_dealt"]:
        stats["damage_dealt"][attacker_name] = 0
    stats["damage_dealt"][attacker_name] += damage

def checkTime(characters):
    """Update temporal effects counters on a character."""
    # dicoTemporalite maps effect names to [duration, attk_adv, def_adv]
    for name, values in list(characters.dicoTemporalite.items()):
        duration, att_bonus, def_bonus = values
        if duration > 0:
            duration -= 1
            characters.dicoTemporalite[name][0] = duration

        if duration == 0:
            characters.attack_advantage -= att_bonus
            characters.defense_advantage -= def_bonus

            if name == 'dash':
                characters.speed -= characters.base_speed
            if name == 'disengage':
                characters.can_be_opportunity_attacked = True

            # effect expired, remove it
            del characters.dicoTemporalite[name]

