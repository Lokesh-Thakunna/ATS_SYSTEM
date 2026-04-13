from datetime import timedelta


APPLICATION_STAGE_FLOW = [
    "Applied",
    "Under Review",
    "Shortlisted",
    "Interview",
    "Hired",
]


APPLICATION_STATUS_META = {
    "applied": {
        "label": "Applied",
        "stages": APPLICATION_STAGE_FLOW,
        "current_stage": "Applied",
        "next_stage": "Under Review",
        "next_update_days": 2,
    },
    "under_review": {
        "label": "Under Review",
        "stages": APPLICATION_STAGE_FLOW,
        "current_stage": "Under Review",
        "next_stage": "Shortlisted",
        "next_update_days": 3,
    },
    "shortlisted": {
        "label": "Shortlisted",
        "stages": APPLICATION_STAGE_FLOW,
        "current_stage": "Shortlisted",
        "next_stage": "Interview",
        "next_update_days": 4,
    },
    "interviewed": {
        "label": "Interview",
        "stages": APPLICATION_STAGE_FLOW,
        "current_stage": "Interview",
        "next_stage": "Hired",
        "next_update_days": 5,
    },
    "hired": {
        "label": "Hired",
        "stages": APPLICATION_STAGE_FLOW,
        "current_stage": "Hired",
        "next_stage": None,
        "next_update_days": None,
    },
    "rejected": {
        "label": "Rejected",
        "stages": ["Applied", "Under Review", "Rejected"],
        "current_stage": "Rejected",
        "next_stage": None,
        "next_update_days": None,
    },
}


def build_application_progress(application):
    status_key = str(getattr(application, "status", "applied") or "applied").strip().lower()
    meta = APPLICATION_STATUS_META.get(status_key, APPLICATION_STATUS_META["applied"])
    next_update_at = None

    if meta["next_update_days"] is not None and getattr(application, "updated_at", None):
        next_update_at = application.updated_at + timedelta(days=meta["next_update_days"])

    return {
        "status_label": meta["label"],
        "available_stages": meta["stages"],
        "current_stage": meta["current_stage"],
        "current_stage_index": (
            meta["stages"].index(meta["current_stage"])
            if meta["current_stage"] in meta["stages"]
            else None
        ),
        "next_stage": meta["next_stage"],
        "next_update_at": next_update_at,
        "is_terminal": meta["next_stage"] is None,
    }
