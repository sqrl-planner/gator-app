"""All datasets provided by Gator."""
from gator.core.models.timetable import Session

from gator.app.extensions.dataset_registry import dataset_registry
from gator.datasets.uoft.utsg import UtsgArtsciTimetableDataset

# The sessions that are tracked by the registry. Order does not matter.
#
# You'll need to add new sessions here as they become available. The registry
# will automatically track all datasets for all sessions listed below.
SESSIONS = [
    Session(2022, summer=False),  # 2022 Fall/Winter
    Session(2022, summer=True),   # 2022 Summer
    Session(2021, summer=False)   # 2021 Fall/Winter
]


def register_all_datasets() -> None:
    """Register all available datasets to be tracked by the registry.

    Tracking a dataset means that the registry will automatically pull data
    from the dataset and sync it with the database. This function should be
    called once at the start of the application.

    Currently tracked datasets:
        - UofT St. George ArtSci timetable
    """
    for session in SESSIONS:
        dataset_registry.register(UtsgArtsciTimetableDataset(session))
