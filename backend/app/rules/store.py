from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class Rule:
    id: str
    intent: str
    patterns: list[str]
    language: str
    replacement_code: str
    test_case: str

class RuleStore:
    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent
        base_dir = base_dir.resolve()
        self.public_dir = base_dir / "public"
        self.private_dir = base_dir / "private"
        self.rules: dict[str, Rule] = {}
        
        # Ensure directories exist
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.private_dir.mkdir(parents=True, exist_ok=True)
        
        self.refresh()

    def refresh(self):
        """Reloads all rules from disk."""
        self.rules.clear()
        self._load_from_dir(self.public_dir)
        # Private rules override public ones if IDs collide (though they should ideally be distinct)
        # For multi-tenancy, we might want to load private rules on demand or namespaced.
        # For now, we load all found private rules.
        self._load_from_dir(self.private_dir)

    def _load_from_dir(self, directory: Path):
        if not directory.exists():
            return
            
        for file in directory.rglob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        self._add_rule(item)
                elif isinstance(data, dict):
                    self._add_rule(data)
            except Exception as e:
                logger.error(f"Failed to load rules from {file}: {e}")

    def _add_rule(self, item: dict):
        try:
            rule = Rule(**item)
            self.rules[rule.id] = rule
        except TypeError as e:
            logger.error(f"Invalid rule format: {e}")

    def get_rule_by_intent(self, intent: str, tenant_id: str = "default") -> Optional[Rule]:
        """
        Finds a rule matching the intent.
        Priority: 
        1. Tenant-specific private rule (not fully implemented in this simple version, but structure allows it)
        2. Generic private rule
        3. Public rule
        """
        # Simple lookup for now. In a real multi-tenant system, we'd filter by tenant_id prefix or directory.
        # Here we just look for any rule matching the intent.
        
        # First check for a tenant specific override if we implemented namespacing:
        # (Scanning logic would go here)

        for rule in self.rules.values():
            if rule.intent == intent:
                return rule
        return None

    def save_rule(self, rule: Rule, tenant_id: str = "default"):
        """Saves a new rule to the tenant's private store."""
        tenant_dir = self.private_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = tenant_dir / f"{rule.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(rule), f, indent=2)
        
        self.rules[rule.id] = rule
        logger.info(f"Saved rule {rule.id} for tenant {tenant_id}")

# Singleton instance
_store = None

def get_store() -> RuleStore:
    global _store
    if _store is None:
        _store = RuleStore()
    return _store
