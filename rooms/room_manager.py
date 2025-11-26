class RoomManager:
    def __init__(self):
        self.rooms = []

    def add_room(self, room):
        self.rooms.append(room)

    def describe_all_rooms(self):
        for room in self.rooms:
            print(room.get_full_description())

