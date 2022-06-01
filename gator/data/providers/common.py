"""Common definitions for data providers."""
from typing import Optional, Union
from abc import abstractclassmethod

from gator.models.timetable import Session
from gator.data.pipeline.datasets import Dataset


class TimetableDataset(Dataset):
    """A dataset that contains course timetable information for a single session.

    Instance Attributes:
        session: The session for which the timetable data is provided.
    """

    def __init__(self, session: Optional[Union[Session, str]] = None) -> None:
        """Initialise an ArtsciTimetableAPI.

        Args:
            session: An optional session that can be supplied instead of the
                default. This can be an instance of Session or a string
                providing the session code.
        """
        super().__init__()
        if isinstance(session, str):
            self.session = Session.parse(session)
        elif session is None:
            self.session = self._get_latest_session()
        else:
            self.session = session

    @abstractclassmethod
    def _get_latest_session(cls, verify: bool = False) -> Session:
        """Return the most up-to-date session from the timetable data source.
        Raise a ValueError if the session could not be found.

        Args:
            verify: Whether to verify the session code against the timetable.
        """
        raise NotImplementedError
