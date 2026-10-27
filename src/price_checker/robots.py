"""robots.txt parsing with wildcard support.

The standard library's ``urllib.robotparser`` only does prefix matching, so a rule
like ``Disallow: /*search=`` (PriceRunner uses these) would never match and we
would fetch pages the site asked bots to leave alone. This follows Google's rules:
``*`` matches anything, a trailing ``$`` anchors the end, the longest matching
rule wins and ``Allow`` wins a tie.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class _Group:
    agents: list[str] = field(default_factory=list)
    rules: list[tuple[bool, str]] = field(default_factory=list)


class Robots:
    def __init__(self, text: str) -> None:
        self.groups: list[_Group] = []
        group: _Group | None = None
        reading_agents = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if group is None or not reading_agents:
                    group = _Group()
                    self.groups.append(group)
                group.agents.append(value.lower())
                reading_agents = True
                continue
            reading_agents = False
            # An empty Disallow means "allow everything", which is the default anyway.
            if key in ("allow", "disallow") and group is not None and value:
                group.rules.append((key == "allow", value))

    def can_fetch(self, agent: str, path: str) -> bool:
        """`path` is the URL path plus query string, e.g. ``/pl/123?p=2``."""
        agent = agent.lower()
        groups = [g for g in self.groups if any(a != "*" and agent.startswith(a) for a in g.agents)]
        if not groups:
            groups = [g for g in self.groups if "*" in g.agents]
        best: tuple[int, bool] | None = None
        for group in groups:
            for allow, pattern in group.rules:
                if _matches(pattern, path):
                    key = (len(pattern), allow)
                    if best is None or key > best:
                        best = key
        return True if best is None else best[1]


def _matches(pattern: str, path: str) -> bool:
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    if anchored:
        regex += "$"
    return re.match(regex, path) is not None
