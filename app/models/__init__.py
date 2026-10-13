"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.volunteer_log import VolunteerLog
from app.models.prize import Prize
from app.models.redemption import Redemption

__all__ = ["User", "VolunteerLog", "Prize", "Redemption"]
