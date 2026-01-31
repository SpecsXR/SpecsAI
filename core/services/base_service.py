
class Service:
    def __init__(self):
        self.name = "BaseService"
        self.is_active = False

    def start(self):
        self.is_active = True
        print(f"{self.name} started.")

    def stop(self):
        self.is_active = False
        print(f"{self.name} stopped.")
