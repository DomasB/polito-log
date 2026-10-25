import re

# Usernames that could pass for site staff. Compared after lowercasing and
# dropping everything but letters, so "Admin_1" and "a.d.m.i.n" are caught.
RESERVED_USERNAMES = frozenset({
    "mod", "mods", "staff", "support", "root", "system", "sysadmin",
    "official", "team", "security", "help", "helpdesk", "owner", "operator",
    "noreply", "postmaster", "webmaster", "abuse",
})
# Any username starting with one of these is reserved too, e.g. "administratorius".
RESERVED_USERNAME_PREFIXES = ("admin", "moderator", "polito")


def is_reserved_username(username: str) -> bool:
    """
    Whether a username is reserved because it could pass for site staff.

    Args:
        username: Candidate username

    Returns:
        True if the username may not be used
    """
    letters = re.sub(r"[^a-z]", "", username.lower())
    return letters in RESERVED_USERNAMES or letters.startswith(RESERVED_USERNAME_PREFIXES)
