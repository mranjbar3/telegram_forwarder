import re
from typing import List
from sqlalchemy.orm import Session
from app.models import FilterRule

class FilterService:
    def __init__(self, db: Session):
        self.db = db
        self.rules = db.query(FilterRule).filter_by(is_active=True).all()

    def should_skip(self, text: str) -> tuple[bool, str]:
        if not text:
            return False, ""
        for rule in self.rules:
            if rule.rule_type == "keyword" and rule.pattern.lower() in text.lower():
                return True, f"کلمه ممنوعه: {rule.pattern}"
            if rule.rule_type == "regex":
                try:
                    if re.search(rule.pattern, text):
                        return True, f"تطابق regex: {rule.pattern}"
                except re.error:
                    continue
        return False, ""

    def apply_decorations(self, text: str) -> str:
        header = ""
        footer = ""
        for rule in self.rules:
            if rule.rule_type == "header":
                header = rule.pattern
            elif rule.rule_type == "footer":
                footer = rule.pattern
        parts = []
        if header:
            parts.append(header)
        if text:
            parts.append(text)
        if footer:
            parts.append(footer)
        return "\n".join(parts)
