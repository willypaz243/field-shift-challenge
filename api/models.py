from api.core.models import SyncVersion
from api.modules.alerts.models import Event
from api.modules.climate.models import ClimateHistory, Forecast
from api.modules.crops.models import Crop
from api.modules.feedback.models import Feedback, Plan
from api.modules.reports.models import Report
from api.modules.water.models import Reservoir
from api.modules.zones.models import Zone

__all__ = [
    "ClimateHistory",
    "Crop",
    "Event",
    "Feedback",
    "Forecast",
    "Plan",
    "Report",
    "Reservoir",
    "SyncVersion",
    "Zone",
]
