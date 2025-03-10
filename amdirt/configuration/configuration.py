class Settings:
    def __init__(self):
        self.local_json_schema = None

    def update(self, updates):
        for key, value in updates.items():
            if hasattr(self, key): 
                setattr(self, key, value)
            else:
                print(f"Warning: Setting '{key}' not found.") 

settings = Settings() 