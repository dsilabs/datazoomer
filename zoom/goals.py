"""
    System Goals
"""

import store
import datetime

class GoalAchievement(store.Entity): pass
Achievement = GoalAchievement

def achieved(goal, subject):
    """Record that a goal has been achieved"""
    now = datetime.datetime.now()
    entry = dict(goal=goal, subject=subject, username=user.username, timestamp=now)
    achievements = store.store(Achievement)
    achievements.put(entry)

