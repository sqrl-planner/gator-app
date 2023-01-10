# type: ignore
"""Base classes for a datasets."""
from typing import Union
from abc import ABC, abstractmethod, abstractclassmethod

from gator.models.common import Record
from gator.models.timetable import Session

class Dataset(ABC):
    """A dataset that returns :class:`gator.models.Record` instances."""

    @abstractmethod
    def get(self) -> list[Record]:
        """Return the data contained in this dataset."""
        raise NotImplementedError()


class SessionalDataset(Dataset):
    """A dataset that is specific to a session.

    For example, a dataset of courses offered in a particular session, or a
    dataset of clubs that are active in a particular session.

    Instance Attributes:
        session: The session that this dataset is specific to.
    """
    session: Session

    def __init__(self, session: Optional[Union[Session, str]] = None) -> None:
        """Initialize a SessionalDataset.

        Args:
            session: An optional session that can be supplied instead of the
                default. This can be an instance of Session or a string providing
                the session code. If None, the latest session will be used.
        """
        super().__init__()
        if isinstance(session, str):
            self.session = Session.parse(session)
        elif session is None:
            self.session = self._get_latest_session()
        else:
            self.session = session

    @abstractclassmethod
    def _get_latest_session(cls) -> Session:
        """Return the most up-to-date session for this dataset.

        Raise a ValueError if the session could not be found.
        """
        raise NotImplementedError
