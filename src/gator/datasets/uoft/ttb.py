"""A data scraping and processing pipeline for the timetable builder API.

The University of Toronto timetable builder (TTB) API is a RESTful API that
provides access to timetable data (e.g. course and section information) for
all campuses (St. George, Mississauga, and Scarborough) and faculties (e.g.
Arts & Science, Engineering, etc.).

The API can be accessed at https://api.easi.utoronto.ca/ttb/.
"""
from typing import Any, Iterator

from gator.core.data.dataset import SessionalDataset
from gator.core.models.timetable import Session
from mongoengine import Document


class TimetableDataset(SessionalDataset):
    """A dataset for the UofT timetable builder (TTB) API.

    Remarks:
        This dataset scrapes against the University of Toronto timetable builder
        (TTB) API, and processes the data into MongoEngine models defined in
        the :mod:`gator.core.models` module. See for the following for more
        information: https://api.easi.utoronto.ca/ttb/.

    Class Attributes:
        ROOT_URL: The url for the timetable builder (TTB) homepage.
        API_URL: The root url for the timetable builder (TTB) API.
        DEFAULT_HEADERS: The default headers to use when making requests to
            the TTB API.
    """
    ROOT_URL = 'https://ttb.utoronto.ca/'
    API_URL = 'https://api.easi.utoronto.ca/ttb/'
    DEFAULT_HEADERS: dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
        )
    }

    @property
    def slug(self) -> str:
        """Return the slug for the dataset."""
        return 'ttb-{}'.format(
            '-'.join(s.code for s in self._sessions_sorted))

    @property
    def name(self) -> str:
        """Return the name for the dataset."""
        return 'Timetable Builder Data ({})'.format(
            ', '.join(s.human_str for s in self._sessions_sorted))

    @property
    def description(self) -> str:
        """Return the description for the dataset."""
        return (
            'Timetable data for the University of Toronto for the '
            '{} sessions. Scraped from the timetable builder API.'
        ).format(', '.join(s.human_str for s in self._sessions_sorted))

    def get(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator that lazily yields `(id, data)` records.

        The `id` should be a unique identifier for the record, and the `data`
        can be any hashable object. A hash of the `data` object will be compared
        with a hash stored in the database for the record with the given `id`.
        """
        raise NotImplementedError()

    def process(self, id: str, data: Any) -> Document:
        """Process the given record into a :class:`mongoengine.Document`.

        Args:
            id: The unique identifier for the record.
            data: The data for the record.
        """
        raise NotImplementedError()

    @property
    def _sessions_sorted(self) -> list[Session]:
        """Return the sessions sorted in descending order."""
        return sorted(self.sessions, reverse=True)

    @classmethod
    def _get_latest_sessions(cls):
        """Return the most up-to-date sessions for this dataset.

        Raise a ValueError if the session could not be found.
        """
        return []
