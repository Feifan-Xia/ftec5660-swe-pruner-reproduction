"""OpenHands extension layered over the authors' unchanged pruning executor."""
import json
import os
from pathlib import Path
from pydantic import Field
from openhands.sdk import Action, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor
from observation_store import ObservationStore
from tool_utils import BashObservation, PrunerBashExecutor, PrunerBashAction, _BASH_DESCRIPTION_PRUNE

STORE = ObservationStore()


def persist():
    path = Path(os.environ['OBSERVATION_LOG'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(STORE.manifest(), ensure_ascii=False), encoding='utf-8')


class RecoverableObservation(BashObservation):
    observation_id: str
    line_count: int

    @property
    def to_llm_content(self):
        return [*super().to_llm_content, TextContent(text=(
            f'\n\nOriginal output saved as {self.observation_id}, {self.line_count} lines. '
            'Use the expand tool with inclusive one-based start/end lines to recover details.'))]


class RecoverableExecutor(PrunerBashExecutor):
    def __call__(self, action, conversation=None):
        result = super().__call__(action, conversation)
        raw = result.original_output or ''
        key = STORE.put(raw)
        persist()
        return RecoverableObservation(**result.model_dump(exclude={'kind'}),
                                      observation_id=key, line_count=len(raw.splitlines()))


class RecoverableBashTool(ToolDefinition[PrunerBashAction, RecoverableObservation]):
    @classmethod
    def create(cls, conv_state, executor=None):
        return [cls(description=_BASH_DESCRIPTION_PRUNE,
                    action_type=PrunerBashAction, observation_type=RecoverableObservation,
                    executor=executor or RecoverableExecutor())]


class ExpandAction(Action):
    observation_id: str = Field(description='Saved observation ID')
    start: int = Field(description='First line, one-based inclusive')
    end: int = Field(description='Last line, inclusive; at most 200 lines per call')


class ExpandExecutor(ToolExecutor[ExpandAction, BashObservation]):
    def __call__(self, action, conversation=None):
        try:
            text = STORE.expand(action.observation_id, action.start, action.end)
        except ValueError as exc:
            text = str(exc)
        persist()
        return BashObservation(output=text, original_output=text)


class ExpandTool(ToolDefinition[ExpandAction, BashObservation]):
    @classmethod
    def create(cls, conv_state, executor=None):
        return [cls(description='Recover exact original lines from a saved tool output when details are needed.',
                    action_type=ExpandAction, observation_type=BashObservation,
                    executor=executor or ExpandExecutor())]


def make_recoverable(conv_state):
    return RecoverableBashTool.create(conv_state)


def make_expand(conv_state):
    return ExpandTool.create(conv_state)
