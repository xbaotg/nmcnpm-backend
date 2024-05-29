from core.db import db_deps
from schemas.db import Params, Users

# class Rule:
#     def __init__(self):
#         stats = db_deps.query(Params).first()

#         self.MIN_PLAYER_AGE = stats.min_player_age
#         self.MAX_PLAYER_AGE = stats.max_player_age
#         self.MIN_CLUB_PLAYER = stats.min_club_player
#         self.MAX_CLUB_PLAYER = stats.max_club_player
#         self.MAX_FOREIGN_PLAYER = stats.max_foreign_player

#         self.POINTS_WIN = stats.points_win
#         self.POINTS_DRAW = stats.points_draw
#         self.POINTS_LOSE= stats.points_lose

#         self.MAX_GOAL_TYPES = stats.max_goal_types
#         self.MAX_GOAL_TIME = stats.max_goal_time

#     def get_MIN_PLAYER_AGE(self):
#         return self.MIN_PLAYER_AGE

#     def get_MAX_PLAYER_AGE(self):
#         return self.MAX_PLAYER_AGE

#     def get_MIN_CLUB_PLAYER(self):
#         return self.MIN_CLUB_PLAYER

#     def get_MAX_CLUB_PLAYER(self):
#         return self.MAX_CLUB_PLAYER

#     def get_MAX_FOREIGN_PLAYER(self):
#         return self.MAX_FOREIGN_PLAYER

#     def get_POINTS_WIN(self):
#         return self.POINTS_WIN

#     def get_POINTS_DRAW(self):
#         return self.POINTS_DRAW

#     def get_POINTS_LOSE(self):
#         return self.POINTS_LOSE

#     def get_MAX_GOAL_TYPES(self):
#         return self.MAX_GOAL_TYPES

#     def get_MAX_GOAL_TIME(self):
#         return self.MAX_GOAL_TIME

# RULE = Rule()
