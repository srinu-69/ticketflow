from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    TIMESTAMP,
    func,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship

from .database import Base


# =========================
# TIMELINE MODELS
# =========================

class TimelineProject(Base):
    __tablename__ = "timeline_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tasks = relationship(
        "TimelineTask",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TimelineTask(Base):
    __tablename__ = "timeline_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("timeline_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    start = Column(DateTime, nullable=False)
    duration = Column(String(64), nullable=True)
    bar_width = Column(String(32), nullable=True)
    bar_color = Column(String(32), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("TimelineProject", back_populates="tasks")
    admin_entry = relationship(
        "AdminTimelineEntry",
        back_populates="timeline_task",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user_entries = relationship(
        "UserTimelineEntry",
        back_populates="timeline_task",
        cascade="all, delete-orphan",
    )


class AdminTimelineEntry(Base):
    __tablename__ = "admin_timeline_entries"

    entry_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timeline_task_id = Column(
        Integer,
        ForeignKey("timeline_tasks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    project_id = Column(Integer, nullable=True)
    project_title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    timeline_task = relationship("TimelineTask", back_populates="admin_entry")


class UserTimelineEntry(Base):
    __tablename__ = "user_timeline_entries"

    entry_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timeline_task_id = Column(
        Integer,
        ForeignKey("timeline_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id = Column(Integer, nullable=True)
    project_title = Column(String(255), nullable=True)
    owner_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    timeline_task = relationship("TimelineTask", back_populates="user_entries")


# =========================
# USER & ASSET MODELS
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String, nullable=False, default='')
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column("email_id", String(255), nullable=False)
    type = Column("asset_type", String(50), nullable=False)
    location = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    open_date = Column("assigned_date", DateTime, nullable=True)
    close_date = Column("return_date", DateTime, nullable=True)


class AdminAsset(Base):
    __tablename__ = "admin_assets"
 
    admin_asset_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id = Column(Integer, nullable=False)
    email = Column("email_id", String(255), nullable=False)
    type = Column("asset_type", String(50), nullable=False)
    location = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Active")
    open_date = Column("assigned_date", TIMESTAMP, nullable=True)
    close_date = Column("return_date", TIMESTAMP, nullable=True)
    actions = Column(String(50), nullable=True)



# =========================
# USER MANAGEMENT
# =========================

class UsersManagement(Base):
    __tablename__ = "users_management"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="Developer")
    department = Column(String(100), nullable=False, default="Engineering")
    tickets_issued = Column(Integer, nullable=False, default=0)
    tickets_resolved = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    language = Column(String(50), nullable=False, default="English")
    mobile_number = Column(String(30), nullable=True)
    date_format = Column(String(30), nullable=False, default="YYYY-MM-DD")
    password_reset_needed = Column(Boolean, nullable=False, default=False)
    profile_file_name = Column(String(255), nullable=True)
    profile_file_size = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    mobile_number = Column(String(20), nullable=True)
    role = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    user_status = Column(String(20), default="Active", nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# =========================
# PROJECT / TICKET SYSTEM
# =========================

class AdminRegistration(Base):
    __tablename__ = "admin_registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, default="")
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    project_key = Column(String(50), nullable=False, unique=True)
    project_type = Column(String(100), default="Software", nullable=False)
    leads = Column(Text, nullable=True)
    team_members = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Epic(Base):
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_code = Column(String(20), unique=True, nullable=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Open", nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)
    assignee = Column(String(255), nullable=True)
    reporter = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AdminEpic(Base):
    __tablename__ = "admin_epics"

    admin_epic_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    epic_id = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=True)
    project_title = Column(String(200), nullable=True)
    user_name = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AdminTicket(Base):
    __tablename__ = "admin_tickets"

    admin_ticket_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, nullable=False)
    ticket_code = Column(String(20), unique=True, nullable=True)
    epic_id = Column(Integer, nullable=True)
    project_id = Column(Integer, nullable=True)
    project_title = Column(String(200), nullable=True)
    user_name = Column(String(255), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Open", nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)
    assignee = Column(String(255), nullable=True)
    reporter = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
