import asyncio
import json
from dataclasses import dataclass, field


@dataclass
class ProgressTracker:
    plan_id: str
    stages: list[dict] = field(default_factory=list)
    current_stage: str = ""
    message: str = ""
    pct: int = 0
    done: bool = False
    failed: bool = False
    error: str = ""
    result: object = None
    _event: asyncio.Event = field(default_factory=asyncio.Event)

    def update(self, stage: str, message: str, pct: int):
        self.current_stage = stage
        self.message = message
        self.pct = pct
        self._event.set()

    def mark_failed(self, error: str):
        self.failed = True
        self.error = error
        self.done = True
        self._event.set()

    def add_stage_result(self, agent: str, content: str | list | dict):
        self.stages.append({"agent": agent, "content": content})


_trackers: dict[str, ProgressTracker] = {}


def get_tracker(plan_id: str) -> ProgressTracker:
    if plan_id not in _trackers:
        _trackers[plan_id] = ProgressTracker(plan_id=plan_id)
    return _trackers[plan_id]
