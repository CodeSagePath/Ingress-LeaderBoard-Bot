"""
Database models for the Ingress Prime leaderboard bot.

This module defines SQLAlchemy models for users, agents, stats submissions,
and individual stat records.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict

from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, Date,
    Time, ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Text, Boolean, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func


Base = declarative_base()


class User(Base):
    """
    Telegram user account.

    Represents a Telegram user who can submit stats.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to agents
    agents = relationship("Agent", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'language_code': self.language_code,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Agent(Base):
    """
    Ingress agent/player.

    Represents an Ingress agent that can submit stats.
    """
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    agent_name = Column(String(255), unique=True, nullable=False, index=True)
    faction = Column(String(20), nullable=False, index=True)
    level = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agents")
    stats_submissions = relationship("StatsSubmission", back_populates="agent", lazy="dynamic")

    # Constraints
    __table_args__ = (
        CheckConstraint("faction IN ('Enlightened', 'Resistance')", name="check_faction"),
        CheckConstraint("level >= 1", name="check_min_level"),
        CheckConstraint("level <= 16", name="check_max_level"),
        Index('idx_agent_name', 'agent_name'),
        Index('idx_faction', 'faction'),
        Index('idx_user_agent', 'user_id', 'agent_name')
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.agent_name}', faction='{self.faction}')>"

    def to_dict(self):
        """Convert agent to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'agent_name': self.agent_name,
            'faction': self.faction,
            'level': self.level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StatsSubmission(Base):
    """
    Complete stats submission from an agent.

    Represents a complete set of stats submitted by an agent on a specific date.
    """
    __tablename__ = 'stats_submissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False, index=True)
    submission_date = Column(Date, nullable=False, index=True)
    submission_time = Column(Time, nullable=False)
    stats_type = Column(String(20), default='ALL TIME', nullable=False, index=True)
    level = Column(Integer, nullable=True)
    lifetime_ap = Column(BigInteger, nullable=True)
    current_ap = Column(BigInteger, nullable=True)
    xm_collected = Column(BigInteger, nullable=True)
    parser_version = Column(String(20), nullable=True)
    submission_format = Column(String(20), nullable=True)  # 'telegram' or 'tabulated'
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="stats_submissions")
    individual_stats = relationship("AgentStat", back_populates="submission", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('agent_id', 'submission_date', 'stats_type', name='uq_agent_date_type'),
        CheckConstraint("stats_type IN ('ALL TIME', 'MONTHLY', 'WEEKLY', 'DAILY')", name="check_stats_type"),
        CheckConstraint("level >= 1", name="check_submission_min_level"),
        CheckConstraint("level <= 16", name="check_submission_max_level"),
        Index('idx_submission_date', 'submission_date'),
        Index('idx_agent_date', 'agent_id', 'submission_date'),
        Index('idx_stats_type', 'stats_type'),
        Index('idx_processed', 'processed_at')
    )

    def __repr__(self):
        return f"<StatsSubmission(id={self.id}, agent_id={self.agent_id}, date='{self.submission_date}', type='{self.stats_type}')>"

    def to_dict(self):
        """Convert submission to dictionary."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'submission_time': self.submission_time.isoformat() if self.submission_time else None,
            'stats_type': self.stats_type,
            'level': self.level,
            'lifetime_ap': self.lifetime_ap,
            'current_ap': self.current_ap,
            'xm_collected': self.xm_collected,
            'parser_version': self.parser_version,
            'submission_format': self.submission_format,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentStat(Base):
    """
    Individual stat value from a submission.

    Represents a single stat value from a complete stats submission.
    """
    __tablename__ = 'agent_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey('stats_submissions.id'), nullable=False, index=True)
    stat_idx = Column(Integer, nullable=False, index=True)  # Index from stats_config
    stat_name = Column(String(255), nullable=False)
    stat_value = Column(BigInteger, nullable=False)
    stat_type = Column(String(10), nullable=False)  # 'N' for numeric, 'S' for string
    original_position = Column(Integer, nullable=True)  # Original position in stats text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submission = relationship("StatsSubmission", back_populates="individual_stats")

    # Constraints
    __table_args__ = (
        UniqueConstraint('submission_id', 'stat_idx', name='uq_submission_stat'),
        CheckConstraint("stat_type IN ('N', 'S', 'U')", name="check_stat_type"),
        CheckConstraint("stat_idx >= 0", name="check_stat_idx"),
        Index('idx_stat_idx', 'stat_idx'),
        Index('idx_stat_value', 'stat_value'),
        Index('idx_stat_name', 'stat_name'),
        Index('idx_submission_stat', 'submission_id', 'stat_idx')
    )

    def __repr__(self):
        return f"<AgentStat(id={self.id}, stat_idx={self.stat_idx}, name='{self.stat_name}', value={self.stat_value})>"

    def to_dict(self):
        """Convert agent stat to dictionary."""
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'stat_idx': self.stat_idx,
            'stat_name': self.stat_name,
            'stat_value': self.stat_value,
            'stat_type': self.stat_type,
            'original_position': self.original_position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LeaderboardCache(Base):
    """
    Cached leaderboard data for performance.

    Stores pre-calculated leaderboards to avoid expensive queries.
    """
    __tablename__ = 'leaderboard_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_idx = Column(Integer, nullable=False, index=True)
    stat_name = Column(String(255), nullable=False)
    period = Column(String(20), nullable=False)  # 'all_time', 'monthly', 'weekly'
    faction = Column(String(20), nullable=True)  # 'Enlightened', 'Resistance', or None for all
    cache_data = Column(Text, nullable=False)  # JSON string with leaderboard data
    cache_size = Column(Integer, default=0, nullable=False)  # Number of entries in cache
    min_value = Column(BigInteger, nullable=True)  # Minimum value in this cache
    max_value = Column(BigInteger, nullable=True)  # Maximum value in this cache
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('stat_idx', 'period', 'faction', name='uq_leaderboard_cache'),
        CheckConstraint("period IN ('all_time', 'monthly', 'weekly', 'daily')", name="check_cache_period"),
        Index('idx_expires', 'expires_at'),
        Index('idx_cache_period', 'period'),
        Index('idx_cache_faction', 'faction')
    )

    def __repr__(self):
        return f"<LeaderboardCache(id={self.id}, stat_idx={self.stat_idx}, period='{self.period}', faction='{self.faction}')>"

    def is_expired(self):
        """Check if cache is expired."""
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        """Convert cache entry to dictionary."""
        return {
            'id': self.id,
            'stat_idx': self.stat_idx,
            'stat_name': self.stat_name,
            'period': self.period,
            'faction': self.faction,
            'cache_data': self.cache_data,
            'cache_size': self.cache_size,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class FactionChange(Base):
    """
    Track faction changes for agents.

    Important for maintaining historical data integrity.
    """
    __tablename__ = 'faction_changes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False, index=True)
    old_faction = Column(String(20), nullable=False)
    new_faction = Column(String(20), nullable=False)
    change_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    submission_count_before = Column(Integer, default=0, nullable=False)
    reason = Column(String(255), nullable=True)  # 'user_request', 'correction', etc.

    # Relationships
    agent = relationship("Agent")

    # Constraints
    __table_args__ = (
        CheckConstraint("old_faction IN ('Enlightened', 'Resistance')", name="check_old_faction"),
        CheckConstraint("new_faction IN ('Enlightened', 'Resistance')", name="check_new_faction"),
        Index('idx_agent_change', 'agent_id', 'change_date')
    )

    def __repr__(self):
        return f"<FactionChange(id={self.id}, agent_id={self.agent_id}, {self.old_faction}->{self.new_faction})>"

    def to_dict(self):
        """Convert faction change to dictionary."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'old_faction': self.old_faction,
            'new_faction': self.new_faction,
            'change_date': self.change_date.isoformat() if self.change_date else None,
            'submission_count_before': self.submission_count_before,
            'reason': self.reason
        }


class ProgressSnapshot(Base):
    """
    Monthly progress snapshots for agents.

    Used to calculate monthly/weekly progress leaderboards.
    """
    __tablename__ = 'progress_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    stat_idx = Column(Integer, nullable=False, index=True)
    stat_value = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("Agent")

    # Constraints
    __table_args__ = (
        UniqueConstraint('agent_id', 'snapshot_date', 'stat_idx', name='uq_progress_snapshot'),
        Index('idx_snapshot_date', 'snapshot_date'),
        Index('idx_agent_snapshot', 'agent_id', 'snapshot_date'),
        Index('idx_progress_stat', 'stat_idx')
    )

    def __repr__(self):
        return f"<ProgressSnapshot(id={self.id}, agent_id={self.agent_id}, date='{self.snapshot_date}', stat_idx={self.stat_idx})>"

    def to_dict(self):
        """Convert progress snapshot to dictionary."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'stat_idx': self.stat_idx,
            'stat_value': self.stat_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Utility functions for common queries
def get_latest_submission_for_agent(session: Session, agent_id: int) -> Optional[StatsSubmission]:
    """Get the latest submission for an agent."""
    return session.query(StatsSubmission).filter(
        StatsSubmission.agent_id == agent_id
    ).order_by(StatsSubmission.submission_date.desc()).first()


def get_agent_by_telegram_id(session: Session, telegram_id: int) -> Optional[Agent]:
    """Get agent by Telegram user ID."""
    return session.query(Agent).join(User).filter(
        User.telegram_id == telegram_id,
        Agent.is_active == True
    ).first()


def get_latest_stat_for_agent(session: Session, agent_id: int, stat_idx: int) -> Optional[AgentStat]:
    """Get the latest value for a specific stat for an agent."""
    return session.query(AgentStat).join(StatsSubmission).filter(
        StatsSubmission.agent_id == agent_id,
        AgentStat.stat_idx == stat_idx
    ).order_by(StatsSubmission.submission_date.desc()).first()


def get_leaderboard_for_stat(session: Session, stat_idx: int, limit: int = 20,
                          faction: Optional[str] = None) -> List[Dict]:
    """Get leaderboard data for a specific stat."""
    # First get the latest submission for each agent
    latest_subquery = session.query(
        StatsSubmission.agent_id,
        func.max(StatsSubmission.submission_date).label('max_date')
    ).group_by(StatsSubmission.agent_id).subquery()

    # Build main query with explicit join order using select_from()
    query = session.query(
        Agent.agent_name,
        Agent.faction,
        AgentStat.stat_value,
        StatsSubmission.submission_date
    ).select_from(Agent).join(
        StatsSubmission,
        StatsSubmission.agent_id == Agent.id
    ).join(
        AgentStat,
        AgentStat.submission_id == StatsSubmission.id
    ).join(
        latest_subquery,
        (StatsSubmission.agent_id == latest_subquery.c.agent_id) &
        (StatsSubmission.submission_date == latest_subquery.c.max_date)
    ).filter(
        AgentStat.stat_idx == stat_idx,
        Agent.is_active == True
    )

    if faction:
        query = query.filter(Agent.faction == faction)


    results = query.order_by(AgentStat.stat_value.desc()).limit(limit).all()

    return [
        {
            'rank': idx + 1,
            'agent_name': row.agent_name,
            'faction': row.faction,
            'value': row.stat_value,
            'date': row.submission_date
        }
        for idx, row in enumerate(results)
    ]