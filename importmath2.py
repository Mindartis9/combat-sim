import random
import math
from position import Position  # Import Position class from your file

def generate_entity_positions(num_entities_per_camp):
    """Generates random positions for entities in two camps while maintaining distance constraints."""
    
    def distance(pos1, pos2):
        """Calculate Euclidean distance between two positions (Position objects)."""
        return math.sqrt((pos1.x - pos2.x) ** 2 + 
                         (pos1.y - pos2.y) ** 2 + 
                         (pos1.z - pos2.z) ** 2)
    
    def generate_nearby_position(reference_points, min_dist, max_dist):
        """Generates a position near at least one reference point within the given range."""
        while True:
            ref_point = random.choice(reference_points)
            r = random.uniform(min_dist, max_dist)
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)

            x = ref_point.x + r * math.sin(phi) * math.cos(theta)
            y = ref_point.y + r * math.sin(phi) * math.sin(theta)
            z = ref_point.z + r * math.cos(phi)

            new_position = Position(round(x), round(y), round(z))
            
            if all(distance(new_position, p) >= min_dist for p in reference_points):
                return new_position
    
    # Initialize camp positions using Position objects
    camp_a = [Position(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))]
    camp_b = [Position(random.randint(200, 300), random.randint(200, 300), random.randint(200, 300))]

    # Generate entities for each camp
    for _ in range(num_entities_per_camp - 1):
        camp_a.append(generate_nearby_position(camp_a, 25, 50))
        camp_b.append(generate_nearby_position(camp_b, 25, 50))

    # Ensure opposing camps are at least 50 feet apart
    for idx in range(len(camp_b)):
        while any(distance(camp_b[idx], a) < 50 or distance(camp_b[idx], a) > 100 for a in camp_a):
            camp_b[idx] = generate_nearby_position(camp_b, 50, 100)

    return camp_a, camp_b

def update_entity_positions(camp_a, camp_b):
    """Updates positions of entities in two camps while maintaining distance constraints."""
    
    def distance(pos1, pos2):
        """Calculate Euclidean distance between two positions."""
        return math.sqrt((pos1.x - pos2.x) ** 2 + 
                         (pos1.y - pos2.y) ** 2 + 
                         (pos1.z - pos2.z) ** 2)
    
    def generate_new_position(reference_point, min_dist, max_dist):
        """Generates a new position within a range from the reference point."""
        while True:
            r = random.uniform(min_dist, max_dist)
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)

            x = reference_point.x + r * math.sin(phi) * math.cos(theta)
            y = reference_point.y + r * math.sin(phi) * math.sin(theta)
            z = reference_point.z + r * math.cos(phi)

            new_position = Position(round(x), round(y), round(z))
            return new_position

    # Update positions for Camp A
    for i in range(len(camp_a)):
        camp_a[i] = generate_new_position(camp_a[i], 25, 50)

    # Update positions for Camp B
    for i in range(len(camp_b)):
        camp_b[i] = generate_new_position(camp_b[i], 25, 50)

    # Ensure opposing camps are still at least 50 feet apart
    for i in range(len(camp_b)):
        while any(distance(camp_b[i], a) < 50 or distance(camp_b[i], a) > 100 for a in camp_a):
            camp_b[i] = generate_new_position(camp_b[i], 50, 100)

    return camp_a, camp_b

# Example Usage
camp_a, camp_b = generate_entity_positions(5)  # Initial random positions
print("Initial Camp A:", [(p.x, p.y, p.z) for p in camp_a])
print("Initial Camp B:", [(p.x, p.y, p.z) for p in camp_b])

# Update positions
camp_a, camp_b = update_entity_positions(camp_a, camp_b)
print("\nUpdated Camp A:", [(p.x, p.y, p.z) for p in camp_a])
print("Updated Camp B:", [(p.x, p.y, p.z) for p in camp_b])
