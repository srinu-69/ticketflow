# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Optional
# from datetime import datetime
# from . import models, schemas


# def _coerce_enum_value(model_enum, incoming):
#     """
#     Coerce incoming value (str or Enum) to the DB enum string value.
#     Handles Pydantic enums, raw strings (both names and values).
#     """
#     if incoming is None:
#         return None

#     # If it's an enum instance, use its value
#     if hasattr(incoming, "value"):
#         incoming = incoming.value

#     if isinstance(incoming, str):
#         # Try as enum value
#         try:
#             return model_enum(incoming).value
#         except ValueError:
#             # Try as enum member name
#             try:
#                 return model_enum[incoming.replace(" ", "")].value
#             except Exception:
#                 return incoming  # fallback to string

#     return str(incoming)


# async def get_asset(session: AsyncSession, asset_id: str) -> Optional[models.Asset]:
#     q = select(models.Asset).where(models.Asset.id == asset_id)
#     res = await session.execute(q)
#     return res.scalars().first()


# async def list_assets(session: AsyncSession, status: Optional[str] = None) -> List[models.Asset]:
#     q = select(models.Asset)
#     if status:
#         q = q.where(models.Asset.status == status)
#     q = q.order_by(models.Asset.open_date.desc())
#     res = await session.execute(q)
#     return res.scalars().all()


# def _map_status_to_db(incoming: Optional[str]) -> Optional[str]:
#     """Map incoming status strings (from frontend/schemas) to DB StatusEnum values.

#     The frontend/schema use different status names (e.g. 'active', 'maintenance', 'inactive').
#     The DB model expects 'Open', 'Assigned', 'Closed'. Map commonly used values accordingly.
#     """
#     if incoming is None:
#         return None
#     # coerce enum-like inputs first
#     if hasattr(incoming, "value"):
#         incoming_val = incoming.value
#     else:
#         incoming_val = str(incoming)

#     # direct match to DB enum value
#     try:
#         return models.StatusEnum(incoming_val).value
#     except Exception:
#         pass

#     # common mapping from older/frontend statuses to DB statuses
#     mapping = {
#         "active": models.StatusEnum.Open.value,
#         "maintenance": models.StatusEnum.Assigned.value,
#         "inactive": models.StatusEnum.Closed.value,
#         "open": models.StatusEnum.Open.value,
#         "assigned": models.StatusEnum.Assigned.value,
#         "closed": models.StatusEnum.Closed.value,
#     }
#     key = incoming_val.lower()
#     return mapping.get(key, incoming_val)


# def _map_type_to_db(incoming: Optional[str]) -> Optional[str]:
#     """Map frontend type values to DB AssetTypeEnum values.

#     Frontend may send 'Network Issue' or 'NetworkIssue'; DB expects 'Network'.
#     """
#     if incoming is None:
#         return None
#     if hasattr(incoming, "value"):
#         incoming_val = incoming.value
#     else:
#         incoming_val = str(incoming)

#     # direct match
#     try:
#         return models.AssetTypeEnum(incoming_val).value
#     except Exception:
#         pass

#     # normalize names without spaces
#     name_key = incoming_val.replace(" ", "").lower()
#     type_map = {
#         "laptop": models.AssetTypeEnum.Laptop.value,
#         "charger": models.AssetTypeEnum.Charger.value,
#         "networkissue": models.AssetTypeEnum.Network.value,
#         "network": models.AssetTypeEnum.Network.value,
#     }
#     return type_map.get(name_key, incoming_val)


# async def create_asset(session: AsyncSession, asset_in: schemas.AssetCreate) -> models.Asset:
#     obj = models.Asset(
#         email=asset_in.email,
#         type=_map_type_to_db(asset_in.type),
#         location=_coerce_enum_value(models.LocationEnum, asset_in.location),
#         status=_map_status_to_db(asset_in.status),
#         open_date=datetime.utcnow(),
#     )
#     session.add(obj)
#     await session.commit()
#     await session.refresh(obj)
#     return obj


# async def delete_asset(session: AsyncSession, asset_id: str) -> bool:
#     obj = await get_asset(session, asset_id)
#     if not obj:
#         return False
#     await session.delete(obj)
#     await session.commit()
#     return True
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging
from . import models, schemas 
from .models import UserProfile 
from .schemas import UserProfileCreate, UserProfileUpdate 
import bcrypt 
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)



async def create_project(db: AsyncSession, name: str) -> models.TimelineProject:
    proj = models.TimelineProject(name=name)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def get_project(db: AsyncSession, project_id: int) -> Optional[models.TimelineProject]:
    q = select(models.TimelineProject).where(models.TimelineProject.id == project_id).options(selectinload(models.TimelineProject.tasks))
    res = await db.execute(q)
    return res.scalars().first()


async def list_projects(db: AsyncSession) -> List[models.TimelineProject]:
    q = select(models.TimelineProject).order_by(models.TimelineProject.created_at.desc())
    res = await db.execute(q)
    return res.scalars().all()


async def delete_project(db: AsyncSession, project_id: int) -> None:
    await db.execute(delete(models.TimelineProject).where(models.TimelineProject.id == project_id))
    await db.commit()


# Tasks
async def create_task(db: AsyncSession, task_in: schemas.TaskCreate) -> models.TimelineTask:
    task = models.TimelineTask(
        project_id=task_in.project_id,
        name=task_in.name,
        start=task_in.start,
        duration=task_in.duration,
        bar_width=task_in.bar_width,
        bar_color=task_in.bar_color,
        description=task_in.description,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: int) -> Optional[models.TimelineTask]:
    q = select(models.TimelineTask).where(models.TimelineTask.id == task_id)
    res = await db.execute(q)
    return res.scalars().first()


async def list_tasks_for_project(db: AsyncSession, project_id: int) -> List[models.TimelineTask]:
    q = select(models.TimelineTask).where(models.TimelineTask.project_id == project_id).order_by(models.TimelineTask.start)
    res = await db.execute(q)
    return res.scalars().all()


async def update_task(db: AsyncSession, task_id: int, task_upd: schemas.TaskUpdate) -> Optional[models.TimelineTask]:
    q = select(models.TimelineTask).where(models.TimelineTask.id == task_id)
    res = await db.execute(q)
    task = res.scalars().first()
    if not task:
        return None

    for field, value in task_upd.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> None:
    await db.execute(delete(models.TimelineTask).where(models.TimelineTask.id == task_id))
    await db.commit()


TICKET_TIMELINE_PROJECT_NAME = "Ticket Execution Timeline"

TIMELINE_PRIORITY_STYLES = {
    "Low": {
        "duration": "8 - 72 Hrs",
        "bar_width": "100%",
        "bar_color": "#22c55e",
        "stage_minutes": (36 * 60, 72 * 60),
    },
    "Medium": {
        "duration": "6 - 24 Hrs",
        "bar_width": "100%",
        "bar_color": "#3b82f6",
        "stage_minutes": (12 * 60, 24 * 60),
    },
    "High": {
        "duration": "30 min - 6 Hrs",
        "bar_width": "100%",
        "bar_color": "#f97316",
        "stage_minutes": (3 * 60, 6 * 60),
    },
    "Critical": {
        "duration": "15 min - 1 Hr",
        "bar_width": "100%",
        "bar_color": "#ef4444",
        "stage_minutes": (30, 60),
    },
}

TIMELINE_DEFAULT_SEGMENTS = ["#22c55e", "#ef4444"]

def _generate_ticket_code(ticket_id: int) -> str:
    """Generate external-facing ticket code using FL####V pattern."""
    padded = f"{int(ticket_id):04d}"
    return f"FL{padded}V"


def _apply_ticket_code(ticket: Optional[models.Ticket]) -> bool:
    """Ensure a Ticket row has a ticket_code assigned. Returns True if updated."""
    if ticket and ticket.id and not ticket.ticket_code:
        ticket.ticket_code = _generate_ticket_code(ticket.id)
        return True
    return False


def _apply_admin_ticket_code(admin_ticket: Optional[models.AdminTicket], fallback_ticket_id: Optional[int] = None) -> bool:
    """Ensure an AdminTicket row has a ticket_code assigned. Returns True if updated."""
    if not admin_ticket:
        return False
    base_id = admin_ticket.ticket_id or fallback_ticket_id
    if base_id and not admin_ticket.ticket_code:
        admin_ticket.ticket_code = _generate_ticket_code(base_id)
        return True
    return False


async def _get_ticket_timeline_project(session: AsyncSession) -> Optional[models.TimelineProject]:
    q = select(models.TimelineProject).where(models.TimelineProject.name == TICKET_TIMELINE_PROJECT_NAME)
    res = await session.execute(q)
    return res.scalars().first()


async def ensure_ticket_timeline_project(session: AsyncSession) -> models.TimelineProject:
    project = await _get_ticket_timeline_project(session)
    if project:
        return project

    project = models.TimelineProject(name=TICKET_TIMELINE_PROJECT_NAME)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _get_timeline_task_for_ticket(session: AsyncSession, project_id: int, ticket_id: int) -> Optional[models.TimelineTask]:
    search_fragment = f'"ticket_id": {ticket_id}'
    q = select(models.TimelineTask).where(
        models.TimelineTask.project_id == project_id,
        models.TimelineTask.description.contains(search_fragment)
    )
    res = await session.execute(q)
    return res.scalars().first()


def _build_timeline_description(
    ticket: models.Ticket,
    project_id: Optional[int] = None,
    project_title: Optional[str] = None,
    owner_email: Optional[str] = None,
) -> str:
    style = TIMELINE_PRIORITY_STYLES.get(ticket.priority or "Medium", TIMELINE_PRIORITY_STYLES["Medium"])
    stage_minutes = style.get("stage_minutes", (0, 0))

    payload = {
        "ticket_id": ticket.id,
        "priority": ticket.priority,
        "status": ticket.status,
        "stage_minutes": stage_minutes,
        "segments": TIMELINE_DEFAULT_SEGMENTS,
        "completed_at": None,
        "accumulated_minutes": 0.0,
        "last_started_at": None,
        "is_paused": False,
        "blocked_at": None,
        "project_id": project_id,
        "project_title": project_title,
        "owner_email": owner_email,
        "ticket_code": ticket.ticket_code,
    }
    return json.dumps(payload)


TIMELINE_ACTIVE_STATUS_KEYS = {"inprogress", "analysis", "codereview", "qa", "blocked", "milestone"}
TIMELINE_ACTIVE_NON_BLOCKED_KEYS = TIMELINE_ACTIVE_STATUS_KEYS - {"blocked"}
TIMELINE_DONE_STATUS_KEYS = {"done", "completed", "resolved", "closed"}


def _compact_status(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.lower() if not ch.isspace())


async def sync_timeline_for_ticket(session: AsyncSession, ticket: models.Ticket, old_status: Optional[str] = None) -> None:
    """Create or update a timeline task for a ticket based on its status/priority."""
    new_status_key = _compact_status(ticket.status)
    old_status_key = _compact_status(old_status) if old_status else ""

    is_new_progress = new_status_key in TIMELINE_ACTIVE_NON_BLOCKED_KEYS
    is_new_blocked = new_status_key == "blocked"
    is_new_done = new_status_key in TIMELINE_DONE_STATUS_KEYS
    was_progress = old_status_key in TIMELINE_ACTIVE_STATUS_KEYS

    if not (is_new_progress or is_new_blocked or is_new_done or was_progress):
        # Nothing to do if the ticket is not entering, exiting, or completing an active workflow stage
        return

    project = await ensure_ticket_timeline_project(session)
    task = await _get_timeline_task_for_ticket(session, project.id, ticket.id)

    style = TIMELINE_PRIORITY_STYLES.get(ticket.priority or "Medium", TIMELINE_PRIORITY_STYLES["Medium"])
    stage_minutes = style.get("stage_minutes")
    stage_minutes_list = list(stage_minutes) if stage_minutes else None

    admin_ticket = await session.execute(
        select(models.AdminTicket).where(models.AdminTicket.ticket_id == ticket.id)
    )
    admin_ticket = admin_ticket.scalars().first()
    project_id = admin_ticket.project_id if admin_ticket else None
    project_title = admin_ticket.project_title if admin_ticket else None
    owner_email = ticket.assignee

    description_data = json.loads(
        _build_timeline_description(
            ticket,
            project_id=project_id,
            project_title=project_title,
            owner_email=owner_email,
        )
    )

    if is_new_progress:
        if task is None:
            start_dt = datetime.utcnow()
            description_data["completed_at"] = None
            description_data["accumulated_minutes"] = 0.0
            description_data["last_started_at"] = start_dt.isoformat()
            description_data["is_paused"] = False
            description_data["blocked_at"] = None
            description_data["status"] = ticket.status
            if stage_minutes_list is not None:
                description_data["stage_minutes"] = stage_minutes_list
            task = models.TimelineTask(
                project_id=project.id,
                name=ticket.title,
                start=start_dt,
                duration=style["duration"],
                bar_width=style["bar_width"],
                bar_color=style["bar_color"],
                description=json.dumps(description_data),
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            await _ensure_portal_entries(session, task.id, description_data)
            await session.commit()
        else:
            updated = False
            if task.name != ticket.title:
                task.name = ticket.title
                updated = True
            if task.duration != style["duration"]:
                task.duration = style["duration"]
                updated = True
            if task.bar_width != style["bar_width"]:
                task.bar_width = style["bar_width"]
                updated = True
            if task.bar_color != style["bar_color"]:
                task.bar_color = style["bar_color"]
                updated = True
            existing_payload = {}
            if task.description:
                try:
                    existing_payload = json.loads(task.description)
                except json.JSONDecodeError:
                    existing_payload = {}

            # Check if resuming from blocked state
            was_blocked = existing_payload.get("is_paused") or existing_payload.get("blocked_at") is not None
            now_dt = datetime.utcnow()
            now_iso = now_dt.isoformat()

            merged_payload = {
                **existing_payload,
                "ticket_id": ticket.id,
                "priority": ticket.priority,
                "status": ticket.status,
                "stage_minutes": stage_minutes_list or existing_payload.get("stage_minutes"),
                "segments": TIMELINE_DEFAULT_SEGMENTS,
                "project_id": project_id,
                "project_title": project_title,
                "owner_email": owner_email,
                "ticket_code": ticket.ticket_code,
            }

            if merged_payload.get("is_paused"):
                merged_payload["is_paused"] = False
            if merged_payload.get("blocked_at") is not None:
                merged_payload["blocked_at"] = None
            # When resuming from blocked, set last_started_at to current time to resume timeline
            if was_blocked:
                merged_payload["last_started_at"] = now_iso

            task.description = json.dumps(merged_payload)
            await session.commit()
            await session.refresh(task)
            await _ensure_portal_entries(session, task.id, merged_payload)
            await session.commit()
        return

    if is_new_done and task is None:
        completion_dt = datetime.utcnow()
        description_data["completed_at"] = completion_dt.isoformat()
        description_data["last_started_at"] = None
        description_data["is_paused"] = False
        description_data["blocked_at"] = None
        description_data["status"] = ticket.status
        if stage_minutes_list is not None:
            description_data["stage_minutes"] = stage_minutes_list
        task = models.TimelineTask(
            project_id=project.id,
            name=ticket.title,
            start=completion_dt,
            duration=style["duration"],
            bar_width=style["bar_width"],
            bar_color=style["bar_color"],
            description=json.dumps(description_data),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        await _ensure_portal_entries(session, task.id, description_data)
        await session.commit()
        return

    if was_progress and task is not None:
        existing_payload = {}
        if task.description:
            try:
                existing_payload = json.loads(task.description)
            except json.JSONDecodeError:
                existing_payload = {}
        accumulated = float(existing_payload.get("accumulated_minutes") or 0.0)
        last_started_at = existing_payload.get("last_started_at")
        now_dt = datetime.utcnow()
        now_iso = now_dt.isoformat()
        if last_started_at:
            try:
                last_started_dt = datetime.fromisoformat(last_started_at)
                accumulated += max((now_dt - last_started_dt).total_seconds() / 60.0, 0.0)
            except ValueError:
                pass

        if is_new_done:
            if existing_payload.get("completed_at") is None:
                existing_payload["completed_at"] = now_iso
            existing_payload["accumulated_minutes"] = accumulated
            existing_payload["last_started_at"] = None
            existing_payload["is_paused"] = False
            existing_payload["blocked_at"] = None
            existing_payload["status"] = ticket.status
            if stage_minutes_list is not None:
                existing_payload["stage_minutes"] = stage_minutes_list
            existing_payload["project_id"] = project_id
            existing_payload["project_title"] = project_title
            existing_payload["owner_email"] = owner_email
            existing_payload["ticket_code"] = ticket.ticket_code

            if task.name != ticket.title:
                task.name = ticket.title
            if task.duration != style["duration"]:
                task.duration = style["duration"]
            if task.bar_width != style["bar_width"]:
                task.bar_width = style["bar_width"]
            if task.bar_color != style["bar_color"]:
                task.bar_color = style["bar_color"]

            task.description = json.dumps(existing_payload)
            await session.commit()
            await session.refresh(task)
            await _ensure_portal_entries(session, task.id, existing_payload)
            await session.commit()
        elif is_new_blocked:
            existing_payload["accumulated_minutes"] = accumulated
            existing_payload["last_started_at"] = None
            existing_payload["is_paused"] = True
            existing_payload["blocked_at"] = now_iso
            existing_payload["status"] = ticket.status
            if stage_minutes_list is not None:
                existing_payload["stage_minutes"] = stage_minutes_list
            existing_payload["project_id"] = project_id
            existing_payload["project_title"] = project_title
            existing_payload["owner_email"] = owner_email
            existing_payload["completed_at"] = None
            existing_payload["segments"] = TIMELINE_DEFAULT_SEGMENTS
            existing_payload["ticket_code"] = ticket.ticket_code
            task.description = json.dumps(existing_payload)
            await session.commit()
            await session.refresh(task)
            await _ensure_portal_entries(session, task.id, existing_payload)
            await session.commit()
        else:
            await session.delete(task)
            await session.commit()
        return

    if task is not None and (is_new_done or is_new_blocked or was_progress):
        await session.delete(task)
        await session.commit()


async def list_ticket_timeline_tasks(session: AsyncSession) -> dict:
    project = await ensure_ticket_timeline_project(session)
    if not project:
        return {"server_now": datetime.utcnow().isoformat(), "tasks": []}

    q = select(models.TimelineTask).where(models.TimelineTask.project_id == project.id).order_by(models.TimelineTask.start.desc())
    res = await session.execute(q)
    tasks = []
    for task in res.scalars().all():
        metadata = {}
        if task.description:
            try:
                metadata = json.loads(task.description)
            except json.JSONDecodeError:
                metadata = {}

        priority_value = metadata.get("priority") or "Medium"
        style = TIMELINE_PRIORITY_STYLES.get(priority_value, TIMELINE_PRIORITY_STYLES["Medium"])
        stage_minutes_meta = metadata.get("stage_minutes")
        if isinstance(stage_minutes_meta, (list, tuple)) and len(stage_minutes_meta) >= 2:
            total_minutes = stage_minutes_meta[1]
        else:
            total_minutes = style.get("stage_minutes", (0, 0))[1]
        if not isinstance(total_minutes, (int, float)):
            total_minutes = style.get("stage_minutes", (0, 0))[1]
        if total_minutes is None:
            total_minutes = 0
        try:
            total_minutes = int(total_minutes)
        except (TypeError, ValueError):
            total_minutes = 0

        start_dt = task.start
        end_dt = None
        if start_dt and total_minutes and total_minutes > 0:
            end_dt = start_dt + timedelta(minutes=total_minutes)

        ticket_id = metadata.get("ticket_id")
        ticket_code = metadata.get("ticket_code")
        if ticket_code is None and ticket_id is not None:
            try:
                ticket_code = _generate_ticket_code(int(ticket_id))
            except (TypeError, ValueError):
                ticket_code = None

        tasks.append({
            "id": task.id,
            "ticket_id": ticket_id,
            "ticket_code": ticket_code,
            "name": task.name,
            "priority": priority_value,
            "status": metadata.get("status"),
            "start": task.start,
            "duration": task.duration,
            "bar_width": task.bar_width,
            "bar_color": task.bar_color,
            "stage_minutes": metadata.get("stage_minutes"),
            "segments": metadata.get("segments", TIMELINE_DEFAULT_SEGMENTS),
            "completed_at": metadata.get("completed_at"),
            "accumulated_minutes": metadata.get("accumulated_minutes"),
            "last_started_at": metadata.get("last_started_at"),
            "is_paused": metadata.get("is_paused"),
            "blocked_at": metadata.get("blocked_at"),
            "project_id": metadata.get("project_id"),
            "project_title": metadata.get("project_title"),
            "owner_email": metadata.get("owner_email"),
            "total_minutes": total_minutes,
            "end": end_dt.isoformat() if end_dt else None,
            "created_at": task.created_at,
        })

    timeline_ids = [item["id"] for item in tasks]
    if timeline_ids:
        admin_entries = await session.execute(
            select(models.AdminTimelineEntry).where(models.AdminTimelineEntry.timeline_task_id.in_(timeline_ids))
        )
        admin_map = {entry.timeline_task_id: entry for entry in admin_entries.scalars().all()}

        user_entries = await session.execute(
            select(models.UserTimelineEntry).where(models.UserTimelineEntry.timeline_task_id.in_(timeline_ids))
        )
        user_map: dict[int, list[models.UserTimelineEntry]] = {}
        for entry in user_entries.scalars().all():
            user_map.setdefault(entry.timeline_task_id, []).append(entry)

        entries_changed = False
        for payload in tasks:
            admin_entry = admin_map.get(payload["id"])
            if admin_entry is None and payload.get("project_id") is not None:
                await _ensure_portal_entries(session, payload["id"], payload)
                entries_changed = True
                admin_entry = await session.execute(
                    select(models.AdminTimelineEntry).where(models.AdminTimelineEntry.timeline_task_id == payload["id"])
                )
                admin_entry = admin_entry.scalars().first()

            if admin_entry:
                payload.setdefault("project_id", admin_entry.project_id)
                payload.setdefault("project_title", admin_entry.project_title)

            user_list = user_map.get(payload["id"], [])
            if not user_list and payload.get("project_id") is not None:
                await _ensure_portal_entries(session, payload["id"], payload)
                entries_changed = True
                refreshed_user = await session.execute(
                    select(models.UserTimelineEntry).where(
                        models.UserTimelineEntry.timeline_task_id == payload["id"]
                    )
                )
                user_list = refreshed_user.scalars().all()

            payload["user_entries"] = [
                {
                    "project_id": ue.project_id,
                    "project_title": ue.project_title,
                    "owner_email": ue.owner_email,
                }
                for ue in user_list
            ]

        if entries_changed:
            await session.commit()

    stats_payload = _calculate_timeline_stats(tasks)

    return {
        "server_now": datetime.utcnow().isoformat(),
        "tasks": tasks,
        "stats": stats_payload,
    }


def _calculate_timeline_stats(tasks: list[dict]) -> dict:
    priority_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    critical = 0
    completed = 0
    in_progress = 0

    for item in tasks:
        priority_key = (item.get("priority") or "").strip().lower()
        if priority_key.startswith("crit"):
            priority_counts["Critical"] += 1
            critical += 1
        elif priority_key.startswith("high"):
            priority_counts["High"] += 1
        elif priority_key.startswith("low"):
            priority_counts["Low"] += 1
        else:
            priority_counts["Medium"] += 1

        raw_status = (item.get("status") or "")
        status_key = raw_status.strip().lower()
        compact_status = "".join(ch for ch in status_key if not ch.isspace())

        if status_key in {"completed", "complete"} or compact_status in {"done", "resolved", "closed"}:
            completed += 1
        elif status_key == "in progress" or compact_status == "inprogress":
            in_progress += 1

    return {
        "total_tasks": len(tasks),
        "critical_tasks": critical,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "priority_counts": priority_counts,
    }


async def get_timeline_stats(session: AsyncSession) -> dict:
    data = await list_ticket_timeline_tasks(session)
    tasks = data.get("tasks", [])
    return data.get("stats", _calculate_timeline_stats(tasks))


async def remove_timeline_task_for_ticket(session: AsyncSession, ticket_id: int) -> None:
    project = await _get_ticket_timeline_project(session)
    if not project:
        return

    await session.execute(
        delete(models.TimelineTask).where(
            models.TimelineTask.project_id == project.id,
            models.TimelineTask.description.contains(f'"ticket_id": {ticket_id}')
        )
    )


# Helpers to normalize inputs to DB-expected strings
def _normalize_type(incoming) -> Optional[str]:
    if incoming is None:
        return None
    val = incoming.value if hasattr(incoming, 'value') else str(incoming)
    val = str(val).strip()
    key = ''.join(ch for ch in val.lower() if ch.isalnum())
    if key in ('laptop',):
        return 'Laptop'
    if key in ('charger',):
        return 'Charger'
    if key in ('networkissue', 'network', 'networkissue'):
        # DB expects 'NetworkIssue' (without space, camelCase)
        return 'NetworkIssue'
    # fallback: return original trimmed value 
    return val


def _normalize_status(incoming) -> str:
    # Map frontend status values to DB status values: Open/Assigned/Closed
    if incoming is None:
        return 'Open'
    val = incoming.value if hasattr(incoming, 'value') else str(incoming)
    val = str(val).strip()
    key = ''.join(ch for ch in val.lower() if ch.isalnum())
    if key in ('active', 'open'):
        return 'Open'
    if key in ('maintenance', 'assigned'):
        return 'Assigned'
    if key in ('inactive', 'closed'):
        return 'Closed'
    return val


def _normalize_location(incoming) -> Optional[str]:
    if incoming is None:
        return None
    val = incoming.value if hasattr(incoming, 'value') else str(incoming)
    val = str(val).strip()
    key = ''.join(ch for ch in val.lower() if ch.isalnum())
    if key in ('wfo', 'office', 'onsite'):
        return 'WFO'
    if key in ('wfh', 'home'):
        return 'WFH'
    return val

async def get_asset(session: AsyncSession, asset_id: int) -> Optional[models.Asset]:
    q = select(models.Asset).where(models.Asset.id == asset_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_assets(session: AsyncSession, status: Optional[str] = None, user_email: Optional[str] = None) -> List[models.Asset]:
    q = select(models.Asset)
    if status:
        # Map frontend status to database status
        status_map = {
            "active": "Open",
            "maintenance": "Assigned", 
            "inactive": "Closed"
        }
        db_status = status_map.get(status, status)
        q = q.where(models.Asset.status == db_status)
    if user_email:
        q = q.where(models.Asset.email == user_email)
    q = q.order_by(models.Asset.open_date.desc())
    res = await session.execute(q)
    return res.scalars().all()

async def create_asset(session: AsyncSession, asset_in: schemas.AssetCreate) -> models.Asset:
    # Normalize incoming values to what the DB check constraints expect
    type_val = _normalize_type(asset_in.type)
    status_val = _normalize_status(asset_in.status)
    loc_val = _normalize_location(asset_in.location) or 'WFO'

    obj = models.Asset(
        email=asset_in.email,
        type=type_val,
        location=loc_val,
        status=status_val,
        description=asset_in.description,
        open_date=datetime.utcnow(),
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj

async def update_asset(session: AsyncSession, asset_id: int, asset_in: schemas.AssetUpdate) -> Optional[models.Asset]:
    obj = await get_asset(session, asset_id)
    if not obj:
        return None
    
    # Use normalization helpers for updates as well
    
    if asset_in.email is not None:
        obj.email = asset_in.email
    if asset_in.type is not None:
        obj.type = _normalize_type(asset_in.type)
    if asset_in.location is not None:
        obj.location = _normalize_location(asset_in.location)
    if asset_in.status is not None:
        obj.status = _normalize_status(asset_in.status)
    if asset_in.description is not None:
        obj.description = asset_in.description
    
    await session.commit()
    await session.refresh(obj)
    return obj

async def delete_asset(session: AsyncSession, asset_id: int) -> bool:
    obj = await get_asset(session, asset_id)
    if not obj:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def create_user(session: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    """Create a new user with hashed password"""
    try:
        # Hash password with bcrypt - ensure password is bytes and not too long
        password_bytes = user_in.password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Use raw SQL insert to avoid column mismatch issues
        from sqlalchemy import text
        insert_query = text("""
            INSERT INTO users (full_name, email, hashed_password)
            VALUES (:full_name, :email, :hashed_password)
            RETURNING id, email, full_name, hashed_password
        """)
        result = await session.execute(insert_query, {
            "full_name": user_in.full_name or "",
            "email": user_in.email,
            "hashed_password": hashed_password
        })
        await session.commit()
        
        row = result.first()
        if row:
            user = models.User()
            user.id = row.id
            user.email = row.email
            user.full_name = row.full_name or ""
            user.hashed_password = row.hashed_password
            logger.info(f"✅ User created successfully with ID: {user.id}, Email: {user.email}")
            return user
        else:
            raise Exception("User was not created - no row returned")
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creating user: {str(e)}", exc_info=True)
        raise

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[models.User]:
    """Get user by email - uses raw SQL to avoid column mismatch issues"""
    try:
        from sqlalchemy import text
        query = text("SELECT id, email, full_name, hashed_password FROM users WHERE email = :email")
        result = await session.execute(query, {"email": email})
        row = result.first()
        if row:
            user = models.User()
            user.id = row.id
            user.email = row.email
            user.full_name = row.full_name or ""
            user.hashed_password = row.hashed_password
            return user
        return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}", exc_info=True)
        # Fallback to ORM query (might fail if columns don't match)
        try:
            q = select(models.User.id, models.User.email, models.User.full_name, models.User.hashed_password).where(models.User.email == email)
            res = await session.execute(q)
            row = res.first()
            if row:
                user = models.User()
                user.id = row.id
                user.email = row.email
                user.full_name = row.full_name or ""
                user.hashed_password = row.hashed_password
                return user
            return None
        except Exception as e2:
            logger.error(f"Fallback query also failed: {e2}")
            return None



async def get_users(db: AsyncSession):
    result = await db.execute(select(UserProfile))
    return result.scalars().all()

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()

async def create_user_profile(db: AsyncSession, user: UserProfileCreate):
    db_user = UserProfile(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user: UserProfileUpdate):
    await db.execute(
        update(UserProfile)
        .where(UserProfile.user_id == user_id)
        .values(**user.dict(exclude_unset=True))
    )
    await db.commit()
    return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: int):
    await db.execute(delete(UserProfile).where(UserProfile.user_id == user_id))
    await db.commit()
    return {"message": "User deleted successfully"}

# Admin Registration CRUD Functions
async def create_admin(session: AsyncSession, admin_in: schemas.AdminCreate) -> models.AdminRegistration:
    """Create a new admin registration"""
    try:
        # Hash password with bcrypt
        password_bytes = admin_in.password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        admin = models.AdminRegistration(
            full_name=admin_in.full_name,
            email=admin_in.email,
            hashed_password=hashed_password,
        )
        session.add(admin)
        await session.flush()  # Flush to get the ID without committing
        await session.commit()  # Commit the transaction
        await session.refresh(admin)  # Refresh to get all fields
        logger.info(f"✅ Admin created successfully with ID: {admin.id}, Email: {admin.email}")
        return admin
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creating admin: {str(e)}", exc_info=True)
        raise

async def get_admin_by_email(session: AsyncSession, email: str) -> Optional[models.AdminRegistration]:
    """Get admin by email"""
    q = select(models.AdminRegistration).where(models.AdminRegistration.email == email)
    res = await session.execute(q)
    return res.scalars().first()

async def list_all_admins(session: AsyncSession) -> List[models.AdminRegistration]:
    """List all admins from admin_registrations table"""
    result = await session.execute(select(models.AdminRegistration))
    return list(result.scalars().all())

async def list_all_users(session: AsyncSession) -> List[models.User]:
    """List all users from users table"""
    try:
        # Use text query to select only columns that exist
        from sqlalchemy import text
        query = text("SELECT id, email, full_name, hashed_password FROM users")
        result = await session.execute(query)
        rows = result.fetchall()
        
        # Convert to User objects
        users = []
        for row in rows:
            user = models.User()
            user.id = row.id
            user.email = row.email
            user.full_name = row.full_name or ""
            user.hashed_password = row.hashed_password
            users.append(user)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        # Fallback: try ORM select (might fail if columns don't match)
        try:
            result = await session.execute(select(models.User.id, models.User.email, models.User.full_name))
            rows = result.all()
            users = []
            for row in rows:
                user = models.User()
                user.id = row.id
                user.email = row.email
                user.full_name = getattr(row, 'full_name', '') or ""
                user.hashed_password = ""
                users.append(user)
            return users
        except Exception as e2:
            logger.error(f"Fallback query also failed: {e2}")
            return []

# Ticket CRUD Functions
async def _update_tickets_issued_counter(session: AsyncSession, email: str, increment: bool = True):
    """Helper function to update tickets_issued counter for a user"""
    if not email:
        return
    user = await get_users_management_by_email(session, email)
    if user:
        if increment:
            user.tickets_issued = (user.tickets_issued or 0) + 1
        else:
            user.tickets_issued = max(0, (user.tickets_issued or 0) - 1)
        await session.commit()

async def _update_tickets_resolved_counter(session: AsyncSession, email: str, increment: bool = True):
    """Helper function to update tickets_resolved counter for a user"""
    if not email:
        return
    user = await get_users_management_by_email(session, email)
    if user:
        if increment:
            user.tickets_resolved = (user.tickets_resolved or 0) + 1
        else:
            user.tickets_resolved = max(0, (user.tickets_resolved or 0) - 1)
        await session.commit()

async def create_ticket(session: AsyncSession, ticket_in: schemas.TicketCreate) -> models.Ticket:
    """Create a new ticket"""
    ticket = models.Ticket(
        user_id=ticket_in.user_id,
        title=ticket_in.title,
        description=ticket_in.description,
        status=ticket_in.status,
        priority=ticket_in.priority,
        assignee=ticket_in.assignee,
        reporter=ticket_in.reporter,
        start_date=ticket_in.start_date,
        due_date=ticket_in.due_date
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    if _apply_ticket_code(ticket):
        await session.commit()
        await session.refresh(ticket)
    
    # Update counters if assignee is set
    if ticket.assignee:
        if ticket.status == 'Done':
            # If ticket is created as Done, increment tickets_resolved directly
            await _update_tickets_resolved_counter(session, ticket.assignee, increment=True)
        else:
            # If ticket is not Done, increment tickets_issued
            await _update_tickets_issued_counter(session, ticket.assignee, increment=True)
    
    await sync_timeline_for_ticket(session, ticket)

    return ticket

async def get_ticket(session: AsyncSession, ticket_id: int) -> Optional[models.Ticket]:
    """Get ticket by ID"""
    q = select(models.Ticket).where(models.Ticket.id == ticket_id)
    res = await session.execute(q)
    ticket = res.scalars().first()
    if ticket and _apply_ticket_code(ticket):
        await session.commit()
        await session.refresh(ticket)
    return ticket

async def list_tickets(session: AsyncSession, user_id: Optional[int] = None, status: Optional[str] = None) -> List[models.Ticket]:
    """List tickets with optional filters"""
    q = select(models.Ticket)
    if user_id:
        q = q.where(models.Ticket.user_id == user_id)
    if status:
        q = q.where(models.Ticket.status == status)
    q = q.order_by(models.Ticket.created_at.desc())
    res = await session.execute(q)
    tickets = res.scalars().all()
    updated = False
    for ticket in tickets:
        if _apply_ticket_code(ticket):
            updated = True
    if updated:
        await session.commit()
    return tickets

async def update_ticket(session: AsyncSession, ticket_id: int, ticket_in: schemas.TicketUpdate) -> Optional[models.Ticket]:
    """Update a ticket"""
    ticket = await get_ticket(session, ticket_id)
    if not ticket:
        return None
    
    # Store old values for counter updates
    old_assignee = ticket.assignee
    old_status = ticket.status
    
    if ticket_in.title is not None:
        ticket.title = ticket_in.title
    if ticket_in.description is not None:
        ticket.description = ticket_in.description
    if ticket_in.status is not None:
        ticket.status = ticket_in.status
    if ticket_in.priority is not None:
        ticket.priority = ticket_in.priority
    if ticket_in.assignee is not None:
        ticket.assignee = ticket_in.assignee
    if ticket_in.reporter is not None:
        ticket.reporter = ticket_in.reporter
    if ticket_in.start_date is not None:
        ticket.start_date = ticket_in.start_date
    if ticket_in.due_date is not None:
        ticket.due_date = ticket_in.due_date
    
    await session.commit()
    await session.refresh(ticket)

    if _apply_ticket_code(ticket):
        await session.commit()
        await session.refresh(ticket)
    
    # Handle counter updates
    new_assignee = ticket.assignee if ticket_in.assignee is not None else old_assignee
    new_status = ticket.status if ticket_in.status is not None else old_status
    
    # Handle assignee changes FIRST (before status changes)
    if ticket_in.assignee is not None and old_assignee != new_assignee:
        # Remove from old assignee
        if old_assignee:
            if old_status == 'Done':
                await _update_tickets_resolved_counter(session, old_assignee, increment=False)
            else:
                await _update_tickets_issued_counter(session, old_assignee, increment=False)
        
        # Add to new assignee
        if new_assignee:
            if new_status == 'Done':
                await _update_tickets_resolved_counter(session, new_assignee, increment=True)
            else:
                await _update_tickets_issued_counter(session, new_assignee, increment=True)
    
    # Handle status changes (only if assignee didn't change)
    if ticket_in.status is not None and old_status != new_status and ticket_in.assignee is None:
        assignee_for_status = old_assignee
        if assignee_for_status:
            # If moving to Done
            if new_status == 'Done' and old_status != 'Done':
                # Increment tickets_resolved and decrement tickets_issued
                await _update_tickets_resolved_counter(session, assignee_for_status, increment=True)
                await _update_tickets_issued_counter(session, assignee_for_status, increment=False)
            # If moving from Done to something else
            elif old_status == 'Done' and new_status != 'Done':
                # Decrement tickets_resolved and increment tickets_issued
                await _update_tickets_resolved_counter(session, assignee_for_status, increment=False)
                await _update_tickets_issued_counter(session, assignee_for_status, increment=True)
    
    await sync_timeline_for_ticket(session, ticket, old_status=old_status)

    return ticket

async def delete_ticket(session: AsyncSession, ticket_id: int) -> bool:
    """Delete a ticket"""
    ticket = await get_ticket(session, ticket_id)
    if not ticket:
        return False
    
    # Update counters before deleting
    if ticket.assignee:
        if ticket.status == 'Done':
            # If ticket was Done, decrement tickets_resolved
            await _update_tickets_resolved_counter(session, ticket.assignee, increment=False)
        else:
            # If ticket was not Done, decrement tickets_issued
            await _update_tickets_issued_counter(session, ticket.assignee, increment=False)
    
    await remove_timeline_task_for_ticket(session, ticket_id)

    await session.delete(ticket)
    await session.commit()
    return True

# Project CRUD Functions
async def create_project(session: AsyncSession, project_in: schemas.ProjectCreate) -> models.Project:
    """Create a new project"""
    project = models.Project(
        name=project_in.name,
        project_key=project_in.project_key,
        project_type=project_in.project_type,
        leads=project_in.leads,
        team_members=project_in.team_members,
        description=project_in.description
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

async def get_project(session: AsyncSession, project_id: int) -> Optional[models.Project]:
    """Get project by ID"""
    q = select(models.Project).where(models.Project.id == project_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_projects(session: AsyncSession, user_email: Optional[str] = None) -> List[models.Project]:
    """List projects, optionally filtered by user email (as lead or team member)"""
    q = select(models.Project).order_by(models.Project.created_at.desc())
    res = await session.execute(q)
    projects = res.scalars().all()
    
    # If user_email is provided, filter projects where user is lead OR team member
    if user_email:
        filtered_projects = []
        for project in projects:
            # Check if user is in leads
            is_lead = False
            if project.leads:
                lead_emails = [email.strip() for email in project.leads.split(',') if email.strip()]
                is_lead = user_email in lead_emails
            
            # Check if user is in team_members
            is_team_member = False
            if project.team_members:
                team_emails = [email.strip() for email in project.team_members.split(',') if email.strip()]
                is_team_member = user_email in team_emails
            
            # Include project if user is either lead or team member
            if is_lead or is_team_member:
                filtered_projects.append(project)
        
        return filtered_projects
    
    return projects

async def update_project(session: AsyncSession, project_id: int, project_in: schemas.ProjectUpdate) -> Optional[models.Project]:
    """Update a project"""
    project = await get_project(session, project_id)
    if not project:
        return None

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.project_key is not None:
        project.project_key = project_in.project_key
    if project_in.project_type is not None:
        project.project_type = project_in.project_type
    if project_in.leads is not None:
        project.leads = project_in.leads
    if project_in.team_members is not None:
        project.team_members = project_in.team_members
    if project_in.description is not None:
        project.description = project_in.description

    await session.commit()
    await session.refresh(project)
    return project

async def delete_project(session: AsyncSession, project_id: int) -> bool:
    """Delete a project and all associated epics and tickets (cascade delete)"""
    from sqlalchemy import delete
    
    project = await get_project(session, project_id)
    if not project:
        return False
    
    # Delete associated admin_tickets first
    await session.execute(
        delete(models.AdminTicket).where(models.AdminTicket.project_id == project_id)
    )
    
    # Delete associated admin_epics
    await session.execute(
        delete(models.AdminEpic).where(models.AdminEpic.project_id == project_id)
    )
    
    # Delete associated tickets (if you have a project_id column in tickets table)
    # Note: Currently tickets don't have project_id directly, so we need to delete by epic_id
    # First, get all epic IDs for this project
    epics_result = await session.execute(
        select(models.Epic.id).where(models.Epic.project_id == project_id)
    )
    epic_ids = [row[0] for row in epics_result.all()]
    
    # Delete tickets associated with these epics (from admin_tickets by epic_id)
    if epic_ids:
        await session.execute(
            delete(models.AdminTicket).where(models.AdminTicket.epic_id.in_(epic_ids))
        )
    
    # Delete associated epics
    await session.execute(
        delete(models.Epic).where(models.Epic.project_id == project_id)
    )
    
    # Finally, delete the project itself
    await session.delete(project)
    await session.commit()
    return True

# Epic CRUD Functions
async def create_epic(session: AsyncSession, epic_in: schemas.EpicCreate) -> models.Epic:
    """Create a new epic"""
    epic = models.Epic(project_id=epic_in.project_id, name=epic_in.name)
    session.add(epic)
    await session.commit()
    await session.refresh(epic)
    return epic

async def get_epic(session: AsyncSession, epic_id: int) -> Optional[models.Epic]:
    """Get epic by ID"""
    q = select(models.Epic).where(models.Epic.id == epic_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_epics(session: AsyncSession, project_id: Optional[int] = None) -> List[models.Epic]:
    """List all epics, optionally filtered by project"""
    q = select(models.Epic)
    if project_id:
        q = q.where(models.Epic.project_id == project_id)
    q = q.order_by(models.Epic.created_at.desc())
    res = await session.execute(q)
    return res.scalars().all()

async def delete_epic(session: AsyncSession, epic_id: int) -> bool:
    """Delete an epic"""
    epic = await get_epic(session, epic_id)
    if not epic:
        return False
    await session.delete(epic)
    await session.commit()
    return True

# Admin Asset CRUD Functions
async def create_admin_asset(session: AsyncSession, admin_asset_in: schemas.AdminAssetCreate) -> models.AdminAsset:
    """Create a new admin asset"""
    admin_asset = models.AdminAsset(
        id=admin_asset_in.id,
        email=admin_asset_in.email,
        type=admin_asset_in.type,
        location=admin_asset_in.location,
        description=admin_asset_in.description,
        status=admin_asset_in.status,
        open_date=admin_asset_in.open_date,
        close_date=admin_asset_in.close_date,
        actions=admin_asset_in.actions
    )
    session.add(admin_asset)
    await session.commit()
    await session.refresh(admin_asset)
    return admin_asset

async def get_admin_asset(session: AsyncSession, admin_asset_id: int) -> Optional[models.AdminAsset]:
    """Get admin asset by ID"""
    q = select(models.AdminAsset).where(models.AdminAsset.admin_asset_id == admin_asset_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_admin_assets(session: AsyncSession) -> List[models.AdminAsset]:
    """List all admin assets"""
    q = select(models.AdminAsset).order_by(models.AdminAsset.open_date.desc())
    res = await session.execute(q)
    return res.scalars().all()

async def update_admin_asset(session: AsyncSession, admin_asset_id: int, admin_asset_in: schemas.AdminAssetUpdate) -> Optional[models.AdminAsset]:
    """Update an admin asset"""
    admin_asset = await get_admin_asset(session, admin_asset_id)
    if not admin_asset:
        return None

    if admin_asset_in.email is not None:
        admin_asset.email = admin_asset_in.email
    if admin_asset_in.type is not None:
        admin_asset.type = admin_asset_in.type
    if admin_asset_in.location is not None:
        admin_asset.location = admin_asset_in.location
    if admin_asset_in.description is not None:
        admin_asset.description = admin_asset_in.description
    if admin_asset_in.status is not None:
        admin_asset.status = admin_asset_in.status
    if admin_asset_in.open_date is not None:
        admin_asset.open_date = admin_asset_in.open_date
    if admin_asset_in.close_date is not None:
        admin_asset.close_date = admin_asset_in.close_date
    if admin_asset_in.actions is not None:
        admin_asset.actions = admin_asset_in.actions

    await session.commit()
    await session.refresh(admin_asset)
    return admin_asset

async def delete_admin_asset(session: AsyncSession, admin_asset_id: int) -> bool:
    """Delete an admin asset and its corresponding asset record"""
    admin_asset = await get_admin_asset(session, admin_asset_id)
    if not admin_asset:
        return False

    # Capture original asset ID before deletion
    original_asset_id = admin_asset.id

    await session.delete(admin_asset)
    if original_asset_id is not None:
        await session.execute(
            delete(models.Asset).where(models.Asset.id == original_asset_id)
        )
    await session.commit()
    return True

# ==================== UsersManagement CRUD ====================

async def create_users_management(session: AsyncSession, user_in: schemas.UsersManagementCreate) -> models.UsersManagement:
    """Create a new user in users_management table"""
    user = models.UsersManagement(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        role=user_in.role,
        department=user_in.department,
        tickets_issued=user_in.tickets_issued,
        tickets_resolved=user_in.tickets_resolved,
        active=user_in.active,
        language=user_in.language,
        mobile_number=user_in.mobile_number,
        date_format=user_in.date_format,
        password_reset_needed=user_in.password_reset_needed,
        profile_file_name=user_in.profile_file_name,
        profile_file_size=user_in.profile_file_size
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_users_management_by_id(session: AsyncSession, user_id: int) -> Optional[models.UsersManagement]:
    """Get a user from users_management by ID"""
    result = await session.execute(
        select(models.UsersManagement).where(models.UsersManagement.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_users_management_by_email(session: AsyncSession, email: str) -> Optional[models.UsersManagement]:
    """Get a user from users_management by email"""
    result = await session.execute(
        select(models.UsersManagement).where(models.UsersManagement.email == email)
    )
    return result.scalar_one_or_none()

async def list_users_management(session: AsyncSession) -> List[models.UsersManagement]:
    """List all users from users_management table"""
    result = await session.execute(select(models.UsersManagement))
    return list(result.scalars().all())

async def update_users_management(session: AsyncSession, user_id: int, user_in: schemas.UsersManagementUpdate) -> Optional[models.UsersManagement]:
    """Update a user in users_management table"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = await get_users_management_by_id(session, user_id)
    if not user:
        logger.warning(f"User {user_id} not found in users_management table")
        return None
    
    logger.info(f"Updating user {user_id}: before update - role={user.role}, department={user.department}, active={user.active}")
    
    # Update fields only if they are provided (not None)
    if user_in.first_name is not None:
        user.first_name = user_in.first_name
    if user_in.last_name is not None:
        user.last_name = user_in.last_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.role is not None:
        user.role = user_in.role
        logger.info(f"Setting role to: {user_in.role}")
    if user_in.department is not None:
        user.department = user_in.department
        logger.info(f"Setting department to: {user_in.department}")
    if user_in.tickets_issued is not None:
        user.tickets_issued = user_in.tickets_issued
    if user_in.tickets_resolved is not None:
        user.tickets_resolved = user_in.tickets_resolved
    if user_in.active is not None:
        user.active = user_in.active
        logger.info(f"Setting active to: {user_in.active}")
    if user_in.language is not None:
        user.language = user_in.language
    if user_in.mobile_number is not None:
        user.mobile_number = user_in.mobile_number
    if user_in.date_format is not None:
        user.date_format = user_in.date_format
    if user_in.password_reset_needed is not None:
        user.password_reset_needed = user_in.password_reset_needed
    if user_in.profile_file_name is not None:
        user.profile_file_name = user_in.profile_file_name
    if user_in.profile_file_size is not None:
        user.profile_file_size = user_in.profile_file_size
    
    try:
        await session.flush()  # Flush to validate before commit
        await session.commit()
        await session.refresh(user)
        logger.info(f"Successfully updated user {user_id}: after update - role={user.role}, department={user.department}, active={user.active}")
        return user
    except Exception as e:
        await session.rollback()
        logger.error(f"Error committing update for user {user_id}: {e}", exc_info=True)
        raise

async def delete_users_management(session: AsyncSession, user_id: int) -> bool:
    """Delete a user from users_management table"""
    user = await get_users_management_by_id(session, user_id)
    if not user:
        return False
    await session.delete(user)
    await session.commit()
    return True

# ==================== UserProfile CRUD ====================

async def create_user_profile(session: AsyncSession, profile_in: schemas.UserProfileCreate) -> models.UserProfile:
    """Create a new user profile"""
    profile = models.UserProfile(
        full_name=profile_in.full_name,
        email=profile_in.email,
        mobile_number=profile_in.mobile_number,
        role=profile_in.role,
        department=profile_in.department,
        date_of_birth=profile_in.date_of_birth,
        user_status=profile_in.user_status
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile

async def get_user_profile_by_id(session: AsyncSession, user_id: int) -> Optional[models.UserProfile]:
    """Get a user profile by user_id"""
    result = await session.execute(
        select(models.UserProfile).where(models.UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_profile_by_email(session: AsyncSession, email: str) -> Optional[models.UserProfile]:
    """Get a user profile by email"""
    result = await session.execute(
        select(models.UserProfile).where(models.UserProfile.email == email)
    )
    return result.scalar_one_or_none()

async def list_user_profiles(session: AsyncSession) -> List[models.UserProfile]:
    """List all user profiles"""
    result = await session.execute(select(models.UserProfile))
    return list(result.scalars().all())

async def update_user_profile(session: AsyncSession, user_id: int, profile_in: schemas.UserProfileUpdate) -> Optional[models.UserProfile]:
    """Update a user profile"""
    profile = await get_user_profile_by_id(session, user_id)
    if not profile:
        return None
    
    if profile_in.full_name is not None:
        profile.full_name = profile_in.full_name
    if profile_in.email is not None:
        profile.email = profile_in.email
    if profile_in.mobile_number is not None:
        profile.mobile_number = profile_in.mobile_number
    if profile_in.role is not None:
        profile.role = profile_in.role
    if profile_in.department is not None:
        profile.department = profile_in.department
    if profile_in.date_of_birth is not None:
        profile.date_of_birth = profile_in.date_of_birth
    if profile_in.user_status is not None:
        profile.user_status = profile_in.user_status
    
    await session.commit()
    await session.refresh(profile)
    return profile

async def delete_user_profile(session: AsyncSession, user_id: int) -> bool:
    """Delete a user profile"""
    profile = await get_user_profile_by_id(session, user_id)
    if not profile:
        return False
    await session.delete(profile)
    await session.commit()
    return True

# ==================== AdminEpic CRUD ====================

async def create_admin_epic(session: AsyncSession, admin_epic_in: schemas.AdminEpicCreate) -> models.AdminEpic:
    """Create a new admin epic"""
    admin_epic = models.AdminEpic(
        epic_id=admin_epic_in.epic_id,
        project_id=admin_epic_in.project_id,
        project_title=admin_epic_in.project_title,
        user_name=admin_epic_in.user_name,
        name=admin_epic_in.name
    )
    session.add(admin_epic)
    await session.commit()
    await session.refresh(admin_epic)
    return admin_epic

async def get_admin_epic(session: AsyncSession, admin_epic_id: int) -> Optional[models.AdminEpic]:
    """Get an admin epic by admin_epic_id"""
    result = await session.execute(
        select(models.AdminEpic).where(models.AdminEpic.admin_epic_id == admin_epic_id)
    )
    return result.scalar_one_or_none()

async def get_admin_epic_by_epic_id(session: AsyncSession, epic_id: int) -> Optional[models.AdminEpic]:
    """Get an admin epic by original epic_id"""
    result = await session.execute(
        select(models.AdminEpic).where(models.AdminEpic.epic_id == epic_id)
    )
    return result.scalar_one_or_none()

async def list_admin_epics(session: AsyncSession, project_id: Optional[int] = None) -> List[models.AdminEpic]:
    """List all admin epics, optionally filtered by project"""
    query = select(models.AdminEpic)
    if project_id is not None:
        query = query.where(models.AdminEpic.project_id == project_id)
    result = await session.execute(query)
    return list(result.scalars().all())

async def update_admin_epic(session: AsyncSession, admin_epic_id: int, admin_epic_in: schemas.AdminEpicUpdate) -> Optional[models.AdminEpic]:
    """Update an admin epic"""
    admin_epic = await get_admin_epic(session, admin_epic_id)
    if not admin_epic:
        return None
    
    if admin_epic_in.project_id is not None:
        admin_epic.project_id = admin_epic_in.project_id
    if admin_epic_in.project_title is not None:
        admin_epic.project_title = admin_epic_in.project_title
    if admin_epic_in.user_name is not None:
        admin_epic.user_name = admin_epic_in.user_name
    if admin_epic_in.name is not None:
        admin_epic.name = admin_epic_in.name
    
    await session.commit()
    await session.refresh(admin_epic)
    return admin_epic

async def delete_admin_epic(session: AsyncSession, admin_epic_id: int) -> bool:
    """Delete an admin epic"""
    admin_epic = await get_admin_epic(session, admin_epic_id)
    if not admin_epic:
        return False
    await session.delete(admin_epic)
    await session.commit()
    return True

# ==================== AdminTicket CRUD ====================

async def create_admin_ticket(session: AsyncSession, admin_ticket_in: schemas.AdminTicketCreate) -> models.AdminTicket:
    """Create a new admin ticket"""
    admin_ticket = models.AdminTicket(
        ticket_id=admin_ticket_in.ticket_id,
        ticket_code=admin_ticket_in.ticket_code,
        epic_id=admin_ticket_in.epic_id,
        project_id=admin_ticket_in.project_id,
        project_title=admin_ticket_in.project_title,
        user_name=admin_ticket_in.user_name,
        title=admin_ticket_in.title,
        description=admin_ticket_in.description,
        status=admin_ticket_in.status,
        priority=admin_ticket_in.priority,
        assignee=admin_ticket_in.assignee,
        reporter=admin_ticket_in.reporter,
        start_date=admin_ticket_in.start_date,
        due_date=admin_ticket_in.due_date
    )
    session.add(admin_ticket)
    await session.commit()
    await session.refresh(admin_ticket)
    if _apply_admin_ticket_code(admin_ticket, fallback_ticket_id=admin_ticket.ticket_id):
        await session.commit()
        await session.refresh(admin_ticket)
    return admin_ticket

async def get_admin_ticket(session: AsyncSession, admin_ticket_id: int) -> Optional[models.AdminTicket]:
    """Get an admin ticket by admin_ticket_id"""
    result = await session.execute(
        select(models.AdminTicket).where(models.AdminTicket.admin_ticket_id == admin_ticket_id)
    )
    admin_ticket = result.scalar_one_or_none()
    if admin_ticket and _apply_admin_ticket_code(admin_ticket, fallback_ticket_id=admin_ticket.ticket_id):
        await session.commit()
        await session.refresh(admin_ticket)
    return admin_ticket

async def get_admin_ticket_by_ticket_id(session: AsyncSession, ticket_id: int) -> Optional[models.AdminTicket]:
    """Get an admin ticket by original ticket_id"""
    result = await session.execute(
        select(models.AdminTicket).where(models.AdminTicket.ticket_id == ticket_id)
    )
    admin_ticket = result.scalar_one_or_none()
    if admin_ticket and _apply_admin_ticket_code(admin_ticket, fallback_ticket_id=ticket_id):
        await session.commit()
        await session.refresh(admin_ticket)
    return admin_ticket

async def list_admin_tickets(session: AsyncSession, project_id: Optional[int] = None, epic_id: Optional[int] = None) -> List[models.AdminTicket]:
    """List all admin tickets, optionally filtered by project or epic"""
    query = select(models.AdminTicket)
    if project_id is not None:
        query = query.where(models.AdminTicket.project_id == project_id)
    if epic_id is not None:
        query = query.where(models.AdminTicket.epic_id == epic_id)
    result = await session.execute(query)
    admin_tickets = list(result.scalars().all())
    updated = False
    for admin_ticket in admin_tickets:
        if _apply_admin_ticket_code(admin_ticket):
            updated = True
    if updated:
        await session.commit()
    return admin_tickets

async def update_admin_ticket(session: AsyncSession, admin_ticket_id: int, admin_ticket_in: schemas.AdminTicketUpdate) -> Optional[models.AdminTicket]:
    """Update an admin ticket"""
    admin_ticket = await get_admin_ticket(session, admin_ticket_id)
    if not admin_ticket:
        return None
    
    if admin_ticket_in.epic_id is not None:
        admin_ticket.epic_id = admin_ticket_in.epic_id
    if admin_ticket_in.project_id is not None:
        admin_ticket.project_id = admin_ticket_in.project_id
    if admin_ticket_in.project_title is not None:
        admin_ticket.project_title = admin_ticket_in.project_title
    if admin_ticket_in.user_name is not None:
        admin_ticket.user_name = admin_ticket_in.user_name
    if admin_ticket_in.ticket_code is not None:
        admin_ticket.ticket_code = admin_ticket_in.ticket_code
    if admin_ticket_in.title is not None:
        admin_ticket.title = admin_ticket_in.title
    if admin_ticket_in.description is not None:
        admin_ticket.description = admin_ticket_in.description
    if admin_ticket_in.status is not None:
        admin_ticket.status = admin_ticket_in.status
    if admin_ticket_in.priority is not None:
        admin_ticket.priority = admin_ticket_in.priority
    if admin_ticket_in.assignee is not None:
        admin_ticket.assignee = admin_ticket_in.assignee
    if admin_ticket_in.reporter is not None:
        admin_ticket.reporter = admin_ticket_in.reporter
    if admin_ticket_in.start_date is not None:
        admin_ticket.start_date = admin_ticket_in.start_date
    if admin_ticket_in.due_date is not None:
        admin_ticket.due_date = admin_ticket_in.due_date
    
    await session.commit()
    await session.refresh(admin_ticket)
    if _apply_admin_ticket_code(admin_ticket, fallback_ticket_id=admin_ticket.ticket_id):
        await session.commit()
        await session.refresh(admin_ticket)
    return admin_ticket

async def delete_admin_ticket(session: AsyncSession, admin_ticket_id: int) -> bool:
    """Delete an admin ticket"""
    admin_ticket = await get_admin_ticket(session, admin_ticket_id)
    if not admin_ticket:
        return False
    await session.delete(admin_ticket)
    await session.commit()
    return True

async def _ensure_portal_entries(session: AsyncSession, timeline_task_id: int, metadata: dict) -> None:
    project_id = metadata.get("project_id")
    project_title = metadata.get("project_title")
    owner_email = metadata.get("owner_email")

    admin_entry = await session.execute(
        select(models.AdminTimelineEntry).where(models.AdminTimelineEntry.timeline_task_id == timeline_task_id)
    )
    admin_entry = admin_entry.scalars().first()
    if admin_entry is None:
        session.add(
            models.AdminTimelineEntry(
                timeline_task_id=timeline_task_id,
                project_id=project_id,
                project_title=project_title,
            )
        )
    else:
        if (admin_entry.project_id != project_id) or (admin_entry.project_title != project_title):
            admin_entry.project_id = project_id
            admin_entry.project_title = project_title

    if project_id is not None:
        user_entry = await session.execute(
            select(models.UserTimelineEntry).where(
                models.UserTimelineEntry.timeline_task_id == timeline_task_id,
                models.UserTimelineEntry.project_id == project_id,
            )
        )
        user_entry = user_entry.scalars().first()
        if user_entry is None:
            session.add(
                models.UserTimelineEntry(
                    timeline_task_id=timeline_task_id,
                    project_id=project_id,
                    project_title=project_title,
                    owner_email=owner_email,
                )
            )
        else:
            dirty = False
            if user_entry.project_title != project_title:
                user_entry.project_title = project_title
                dirty = True
            if owner_email and user_entry.owner_email != owner_email:
                user_entry.owner_email = owner_email
                dirty = True
            if dirty:
                user_entry.updated_at = datetime.utcnow()