import math

class Position:
    """ Represents a character's position in 3D space. """
    
    def __init__(self, x, y, z=0, grid_size=5000):
        self.x = max(0, min(x, grid_size))
        self.y = max(0, min(y, grid_size))
        self.z = max(0, z)  # Ensure ground-level or higher
        self.grid_size = grid_size

    def distance_to(self, other, squared=False):
        """ Calculates the 3D distance to another position. Uses squared distance if specified. """
        dx, dy, dz = self.x - other.x, self.y - other.y, self.z - other.z
        dist_sq = dx ** 2 + dy ** 2 + dz ** 2
        return dist_sq if squared else math.sqrt(dist_sq)

    def move_towards(self, target_position, speed):
        """ Moves towards a target position using available speed while staying within grid bounds. """
        total_distance = self.distance_to(target_position)
        if total_distance == 0 or speed == 0:
            return  # No movement needed

        move_ratio = min(speed / total_distance, 1)
        self.x = max(0, min(self.grid_size, self.x + (target_position.x - self.x) * move_ratio))
        self.y = max(0, min(self.grid_size, self.y + (target_position.y - self.y) * move_ratio))
        self.z = max(0, self.z + (target_position.z - self.z) * move_ratio)  # Z is only restricted to ground level

    def move_away(self, target_position, speed, max_range):
        """ Moves directly away from a target while ensuring max distance is respected. """
        current_distance = self.distance_to(target_position)
        if current_distance >= max_range:
            return  # Already at max distance

        dx, dy, dz = self.x - target_position.x, self.y - target_position.y, self.z - target_position.z
        total_move = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        if total_move == 0:
            return  # Prevent division by zero

        move_ratio = min(speed / total_move, 1)
        self.x = max(0, min(self.grid_size, self.x + dx * move_ratio))
        self.y = max(0, min(self.grid_size, self.y + dy * move_ratio))
        self.z = max(0, self.z + dz * move_ratio)
