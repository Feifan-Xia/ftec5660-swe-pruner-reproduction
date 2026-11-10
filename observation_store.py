"""Per-task, lossless tool observations with auditable range recovery for XJ13."""
from dataclasses import dataclass, field
import hashlib


@dataclass
class ObservationStore:
    max_lines_per_read: int = 200
    observations: dict[str, str] = field(default_factory=dict)
    reads: list[dict] = field(default_factory=list)
    _seen: set[tuple[str, int]] = field(default_factory=set)

    def put(self, text: str) -> str:
        observation_id = 'obs_' + hashlib.sha256(text.encode()).hexdigest()[:16]
        self.observations[observation_id] = text
        return observation_id

    def expand(self, observation_id: str, start: int, end: int) -> str:
        """Return inclusive one-based lines. Original text remains recoverable."""
        if observation_id not in self.observations:
            raise ValueError('Unknown observation ID')
        lines = self.observations[observation_id].splitlines(keepends=True)
        if not (1 <= start <= end <= len(lines)):
            raise ValueError(f'Range must be within 1..{len(lines)}')
        if end - start + 1 > self.max_lines_per_read:
            raise ValueError(f'Read at most {self.max_lines_per_read} lines per call')
        keys = {(observation_id, i) for i in range(start, end + 1)}
        repeated = len(keys & self._seen)
        self._seen.update(keys)
        text = ''.join(lines[start - 1:end])
        self.reads.append(dict(observation_id=observation_id, start=start, end=end,
                               repeated_lines=repeated, returned_chars=len(text)))
        return text

    def manifest(self) -> dict:
        return {'observations': self.observations, 'reads': self.reads}
