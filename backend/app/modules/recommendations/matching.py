"""Local title and skill matching rules for the recommendation preview."""

import re


def skill_patterns(skills: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    """Compile distinct skill names, keeping punctuation in C++, C# and .NET."""
    unique: dict[str, str] = {}
    for skill in skills:
        name = " ".join(skill.split())
        if name:
            unique.setdefault(name.casefold(), name)
    return [
        (name, re.compile(r"(?<![\w+#])" + re.escape(name) + r"(?![\w+#])", re.I))
        for name in unique.values()
    ]


def _role_words(value: str) -> str:
    return " " + " ".join(re.findall(r"[\w+#]+", value.casefold())) + " "


class RoleMatcher:
    """Compare complete title phrases against a headline and previous roles."""

    def __init__(self, headline: str, experience: list[str | dict[str, str]]) -> None:
        titles = [headline, *(e if isinstance(e, str) else e.get("title", "") for e in experience)]
        self.roles = [
            _role_words(part)
            for title in titles
            for part in re.split(r"[|;()·]", title)
            if part.strip() and re.search(r"\w", part)
        ]

    def matches(self, title: str) -> bool:
        """Allow extra words such as seniority on either side of a matching phrase."""
        role = _role_words(title)
        return bool(role.strip()) and any(role in other or other in role for other in self.roles)
