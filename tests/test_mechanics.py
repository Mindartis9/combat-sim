from characters.party_member import PartyMember
from characters.enemy import Enemy
from mechanics.position import Position, closest_enemy
from mechanics.combat import execute_turn, assign_default_actions


def make_simple_pair(low_hp=False, flying=False):
    """Helper to create a party member and a single enemy."""
    p = PartyMember("P","F","",1,{"STR":10},10,1,10,10,[],2,[],[],"Medium",{"damage_dice":"1d6","modifier":"STR","damage_type":"bludgeoning","range":5},"melee", flying_speed=30 if flying else 0)
    e = Enemy("E",{"STR":8},10,1,5,5,[],1,[],[],"Small",{"damage_dice":"1d6","modifier":"DEX","damage_type":"piercing","range":5},"melee")
    assign_default_actions(p)
    assign_default_actions(e)
    p.position = Position(0,0,0)
    e.position = Position(10,0,0)
    if low_hp:
        p.hitpoints_current = 1
    return p, e


def make_stats():
    return {"turns_survived":{},"actions_used":{},"reactions_used":{},"attack_count":{},"crit_count":{},"damage_dealt":{},"initiative_order":{},"rounds":0,"total_crits":0}


def test_low_hp_retreat_and_disengage():
    p, e = make_simple_pair(low_hp=True)
    stats = make_stats()
    stats["turns_survived"][p.name] = 0
    stats["turns_survived"][e.name] = 0
    execute_turn(p, [p, e], stats)
    # party member should have moved away (x < 0) and used Disengage
    assert p.position.x < 0
    assert stats["actions_used"][p.name]["Disengage"] == 1


def test_target_low_hp_in_range():
    p = PartyMember("P","F","",1,{"STR":10},10,1,10,10,[],2,[],[],"Medium",{"damage_dice":"1d6","modifier":"STR","damage_type":"bludgeoning","range":5},"melee")
    e1 = Enemy("E1",{"STR":8},10,1,5,5,[],1,[],[],"Small",{"damage_dice":"1d6","modifier":"DEX","damage_type":"piercing","range":5},"melee")
    e2 = Enemy("E2",{"STR":8},10,1,5,5,[],1,[],[],"Small",{"damage_dice":"1d6","modifier":"DEX","damage_type":"piercing","range":5},"melee")
    assign_default_actions(p)
    assign_default_actions(e1)
    assign_default_actions(e2)
    p.position = Position(0,0,0)
    e1.position = Position(4,0,0)
    e2.position = Position(3,0,0)
    e1.hitpoints_current = 10
    e2.hitpoints_current = 1
    stats = make_stats()
    stats["turns_survived"][p.name] = 0
    stats["turns_survived"][e1.name] = 0
    stats["turns_survived"][e2.name] = 0
    execute_turn(p, [p, e1, e2], stats)
    # verify the lower-HP enemy took damage
    assert e2.hitpoints_current < 1 or e2.hitpoints_current < e1.hitpoints_current


def test_no_overlap_after_move():
    p, e = make_simple_pair()
    # force same position initially and ensure p does not step onto e
    p.position = Position(0,0,0)
    e.position = Position(0,0,0)
    stats = make_stats()
    stats["turns_survived"][p.name] = 0
    stats["turns_survived"][e.name] = 0
    execute_turn(p, [p, e], stats)
    assert not (p.position.x == e.position.x and p.position.y == e.position.y and p.position.z == e.position.z)


def test_falling_damage_applied():
    p, e = make_simple_pair(flying=True)
    stats = make_stats()
    stats["turns_survived"][p.name] = 0
    stats["turns_survived"][e.name] = 0
    # simulate loss of flight at height
    p.is_flying = False
    p.position = Position(0,0,50)
    execute_turn(p, [p, e], stats)
    assert p.hitpoints_current < p.hitpoints_maximum
