from datetime import datetime

class VolumeEvent:
    """Represents a volume change event."""
    
    def __init__(self, previous_volume: float, new_volume: float, finger_distance: float, session_id=None):
        self.timestamp = datetime.utcnow()
        self.previous_volume = previous_volume
        self.new_volume = new_volume
        self.finger_distance = finger_distance
        self.session_id = session_id
        
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "previous_volume": self.previous_volume,
            "new_volume": self.new_volume,
            "finger_distance": self.finger_distance,
            "session_id": self.session_id
        }
