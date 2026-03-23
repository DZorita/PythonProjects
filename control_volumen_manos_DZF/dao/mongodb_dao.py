from pymongo import MongoClient
from config.settings import Settings

class MongoDAO:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDAO, cls).__new__(cls)
            try:
                # Conexión usando las variables de entorno
                cls._instance.client = MongoClient(Settings.MONGODB_URI)
                cls._instance.db = cls._instance.client[Settings.DATABASE_NAME]
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                cls._instance.client = None
                cls._instance.db = None
        return cls._instance

    def insert_session(self, session_data):
        if self.db is not None:
            return self.db.sessions.insert_one(session_data)
        return None
        
    def update_session(self, session_id, session_data):
        if self.db is not None:
             return self.db.sessions.update_one({'_id': session_id}, {'$set': session_data})
        return None

    def insert_volume_event(self, event_data):
        if self.db is not None:
            return self.db.volume_events.insert_one(event_data)
        return None
