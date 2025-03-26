import math
import random

class Position:
    """ Represents a character's position in 3D space. """
    
    def __init__(self, x, y, z=0):
        self.x = max(0, x) # Ensure within grid bounds
        self.y = max(0, y) # Ensure within grid bounds
        self.z = max(0, z) # Ensure ground-level or higher

    def move_towards(self, target):
        """Move towards another entity by a given step size"""
        # Compute the vector difference
        dx = target.x - self.x
        dy = target.y - self.y
        dz = target.z - self.z
        
        # Compute the distance to the target
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if distance <= self.weapon["range"]:
            return
        
        # Normalize direction
        dx /= distance
        dy /= distance
        dz /= distance

        # Move by speed
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.z += dz * self.speed
        
        # Round the new position
        self.x = round(self.x)
        self.y = round(self.y)
        self.z = round(self.z)

    def move_away(self, target):
        """Move away another entity by a given step size"""
        # Compute the vector difference
        dx = self.x - target.x
        dy = self.y - target.y
        dz = self.z - target.z
        
        # Compute the distance to the target
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if distance <= self.weapon["range"]:
            return
        
        # Normalize direction
        dx /= distance
        dy /= distance
        dz /= distance

        # Move by speed
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.z += dz * self.speed
        
        # Round the new position
        self.x = round(self.x)
        self.y = round(self.y)
        self.z = round(self.z)
        
def distance(pos1, pos2):
    """Calculate Euclidean distance between two positions."""
    return math.sqrt((pos1.x - pos2.x) ** 2 + 
                     (pos1.y - pos2.y) ** 2 + 
                     (pos1.z - pos2.z) ** 2)

def closest_enemy(entity, enemy_camp):
    """Find the closest enemy to the given entity."""
    return min(enemy_camp, key=lambda enemy: distance(entity.position, enemy.position))

def initialize_positions(party, enemies):
    """Initializes positions for entities in both party and enemies only once."""
  
    def generate_nearby_position(reference_points, min_dist, max_dist, entity, max_attempts=100):
        """Generates a position near at least one reference point within the given range."""
        for _ in range(max_attempts):  # Prevent infinite loops
            ref_point = random.choice(reference_points)
            r = random.uniform(min_dist, max_dist)
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)

            x = ref_point.x + r * math.sin(phi) * math.cos(theta)
            y = ref_point.y + r * math.sin(phi) * math.sin(theta)
            z = ref_point.z + r * math.cos(phi) if entity.is_flying else 0

            new_position = Position(round(x), round(y), round(z))
            
            if all(distance(new_position, p) >= min_dist for p in reference_points):
                return new_position
        
        # If no valid position is found, return a fallback value
        return Position(reference_points[0].x + min_dist, reference_points[0].y, 0)

    # Initialize base positions for both parties
    party_positions = [Position(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))]
    enemy_positions = [Position(random.randint(200, 300), random.randint(200, 300), random.randint(200, 300))]

    # Assign positions
    for member in party[1:]:
        party_positions.append(generate_nearby_position(party_positions, 25, 50, member))

    for enemy in enemies[1:]:
        enemy_positions.append(generate_nearby_position(enemy_positions, 25, 50, enemy))

    # Ensure opposing camps are at least 50 feet apart, but avoid infinite loops
    for idx in range(len(enemy_positions)):
        attempts = 0
        while any(distance(enemy_positions[idx], p) < 50 or distance(enemy_positions[idx], p) > 100 for p in party_positions):
            enemy_positions[idx] = generate_nearby_position(enemy_positions, 50, 100, enemies[idx])
            attempts += 1
            if attempts > 100:  # Avoid infinite loops
                break  # Keep the last valid position and exit the loop
    
    # Assign positions to entities
    for i, member in enumerate(party):
        member.position = party_positions[i]
    
    for i, enemy in enumerate(enemies):
        enemy.position = enemy_positions[i]  # Fixed typo (i instead of I)



def move_entities(camp_a, camp_b):
    """Moves entities using their existing movement functions."""
    
    # Example movement logic:
    # Camp A moves toward Camp B
    for entity in camp_a:
        target = random.choice(camp_b)  # Pick a random target from Camp B
        entity.position.move_towards(target.position, entity.speed, 5)

    # Camp B moves away from Camp A
    for entity in camp_b:
        target = random.choice(camp_a)  # Pick a random entity from Camp A
        entity.position.move_away(target.position, entity.speed, 5)

    return camp_a, camp_b
