from datetime import datetime

class Session:
    """Represents an application usage session."""
    
    def __init__(self, start_time: datetime = None, end_time: datetime = None):
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
    
    def end_session(self):
        self.end_time = datetime.utcnow()

    def to_dict(self):
        data = {
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        if self.start_time and self.end_time:
            data["duration_seconds"] = (self.end_time - self.start_time).total_seconds()
        return data
