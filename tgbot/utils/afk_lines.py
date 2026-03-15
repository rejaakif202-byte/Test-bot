import random

AFK_SET_LINES = [
    "I shall take my leave for a while; duties beyond this realm now summon me.",
    "Pray excuse my absence, for I must depart and wander afar for a time.",
    "I withdraw from this discourse for the moment; summon me again when fate allows.",
    "For a brief hour I vanish into silence—think not I have abandoned thee.",
    "My presence fades for now; the world beyond this screen demands my attention.",
    "Permit me a short retreat, for matters of the mortal world call upon me.",
    "I shall be but a shadow for a while; await my return with patience.",
    "Let it be known that I depart for a time, though my return shall not be long delayed.",
    "Silence shall claim me for the moment; speak freely until I walk these halls again.",
    "I step away from this gathering for a spell, yet I shall return when time permits.",
]

AFK_TAG_LINES = [
    "Thy call echoes in vain, for I am absent from this place.",
    "Summon me not, for I wander afar and cannot heed thy voice.",
    "Though thou callest my name, I am but a silent shadow for now.",
    "Your summons reaches empty halls; I am away for a time.",
    "Call as thou may, yet I shall not answer until my return.",
    "Thy voice is heard not by me, for I am presently absent.",
    "Seek me not at this hour, for I have departed for a while.",
    "Though my name be spoken, I am not here to answer thee.",
    "The bell you ring finds no keeper; I am away from these chambers.",
    "Thy call is noted, yet my presence shall return only in time.",
]

AFK_RETURN_LINES = [
    "Lo, thou hast returned from thy silent wandering.",
    "The absent soul walks among us once more.",
    "At last thy shadow graces these halls again.",
    "The silence breaks, for thou hast returned.",
    "From distant absence thou hast found thy way back.",
    "Welcome back; thy presence was sorely missed.",
    "The void thou left behind is now filled again.",
    "Thy return ends the quiet that once lingered here.",
    "The halls awaken again with thy presence.",
    "From thy brief exile thou hast come back to these chambers.",
]

def get_afk_set_line() -> str:
    return random.choice(AFK_SET_LINES)

def get_afk_tag_line() -> str:
    return random.choice(AFK_TAG_LINES)

def get_afk_return_line() -> str:
    return random.choice(AFK_RETURN_LINES)
