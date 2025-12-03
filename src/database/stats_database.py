"""
Stats database operations for Ingress Prime leaderboard bot.

This module provides a high-level interface for saving and retrieving
Ingress agent statistics using the existing SQLAlchemy models and
DatabaseConnection infrastructure.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, time
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import (
    User, Agent, StatsSubmission, AgentStat, FactionChange,
    ProgressSnapshot, LeaderboardCache
)
from .connection import DatabaseConnection
from ..monitoring.error_tracker import database_error_tracking

logger = logging.getLogger(__name__)


class StatsDatabase:
    """High-level interface for Ingress stats database operations."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize StatsDatabase with database connection.

        Args:
            db_connection: DatabaseConnection instance for session management
        """
        self.db = db_connection

    @database_error_tracking("save_stats")
    def save_stats(self, telegram_user_id: int, parsed_stats: Dict,
                   user_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Save parsed stats to database with complete transaction handling.

        Args:
            telegram_user_id: Telegram user ID
            parsed_stats: Parsed statistics dictionary from StatsParser
            user_info: Optional Telegram user information

        Returns:
            Dictionary with success status, submission_id, and metadata

        Raises:
            ValueError: For data validation errors
            SQLAlchemyError: For database operation errors
        """
        # Validate required fields
        validation_result = self._validate_parsed_stats(parsed_stats)
        if not validation_result['valid']:
            raise ValueError(f"Invalid stats data: {validation_result['error']}")

        try:
            with self.db.session_scope() as session:
                # Get or create user
                user = self._get_or_create_user(session, telegram_user_id, user_info)

                # Extract agent information
                agent_name = parsed_stats.get(1, {}).get('value', '').strip()
                faction = parsed_stats.get(2, {}).get('value', '').strip()
                level_str = parsed_stats.get(5, {}).get('value', '0').replace(',', '')
                level = int(level_str) if level_str else None

                # Validate faction
                if faction not in ['Enlightened', 'Resistance']:
                    raise ValueError(f"Invalid faction: {faction}")

                # Get or create agent with faction change detection
                agent, is_new_agent, faction_changed = self._get_or_create_agent(
                    session, user.id, agent_name, faction, level
                )

                # Extract submission metadata
                date_str = parsed_stats.get(3, {}).get('value', '').strip()
                time_str = parsed_stats.get(4, {}).get('value', '').strip()

                # Parse dates and times
                submission_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                submission_time = time.fromisoformat(time_str) if time_str else None

                lifetime_ap_str = parsed_stats.get(6, {}).get('value', '0').replace(',', '')
                current_ap_str = parsed_stats.get(7, {}).get('value', '0').replace(',', '')
                xm_collected_str = parsed_stats.get(11, {}).get('value', '0').replace(',', '')

                lifetime_ap = int(lifetime_ap_str) if lifetime_ap_str else None
                current_ap = int(current_ap_str) if current_ap_str else None
                xm_collected = int(xm_collected_str) if xm_collected_str else None

                # Check for duplicate submission
                existing = session.query(StatsSubmission).filter(
                    StatsSubmission.agent_id == agent.id,
                    StatsSubmission.submission_date == submission_date,
                    StatsSubmission.submission_time == submission_time
                ).first()

                if existing:
                    logger.warning(f"Duplicate submission found for agent {agent_name} on {submission_date} {submission_time}")
                    return {
                        'success': False,
                        'error': f'Stats already submitted for {agent_name} on {submission_date} {submission_time}',
                        'duplicate': True,
                        'existing_submission_id': existing.id
                    }

                # Create main stats submission
                stats_submission = StatsSubmission(
                    agent_id=agent.id,
                    submission_date=submission_date,
                    submission_time=submission_time,
                    stats_type='ALL TIME',
                    level=level,
                    lifetime_ap=lifetime_ap,
                    current_ap=current_ap,
                    xm_collected=xm_collected,
                    parser_version='1.0',
                    submission_format='telegram',
                    processed_at=datetime.utcnow()
                )

                session.add(stats_submission)
                session.flush()  # Get submission ID

                # Create individual stat records (fixed iteration logic)
                stats_count = self._create_individual_stats(
                    session, stats_submission.id, parsed_stats
                )

                # Create progress snapshots for key stats
                self._create_progress_snapshots(
                    session, agent.id, submission_date, parsed_stats
                )

                logger.info(
                    f"Successfully saved {stats_count} stats for agent {agent_name} "
                    f"(ID: {agent.id}, User: {telegram_user_id}, Submission ID: {stats_submission.id})"
                )

                return {
                    'success': True,
                    'submission_id': stats_submission.id,
                    'agent_name': agent_name,
                    'agent_id': agent.id,
                    'user_id': telegram_user_id,
                    'faction': faction,
                    'stats_count': stats_count,
                    'is_new_agent': is_new_agent,
                    'faction_changed': faction_changed,
                    'submission_date': submission_date.isoformat(),
                    'level': level,
                    'lifetime_ap': lifetime_ap,
                    'current_ap': current_ap,
                    'xm_collected': xm_collected
                }

        except SQLAlchemyError as e:
            logger.error(f"Database error saving stats for user {telegram_user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving stats for user {telegram_user_id}: {e}")
            raise

    def _get_or_create_user(self, session, telegram_user_id: int,
                           user_info: Optional[Dict] = None) -> User:
        """Get existing user or create new one."""
        user = session.query(User).filter(User.telegram_id == telegram_user_id).first()

        if not user:
            user = User(
                telegram_id=telegram_user_id,
                username=user_info.get('username') if user_info else None,
                first_name=user_info.get('first_name') if user_info else None,
                last_name=user_info.get('last_name') if user_info else None,
                language_code=user_info.get('language_code') if user_info else None,
                is_active=True
            )
            session.add(user)
            session.flush()
            logger.info(f"Created new user for Telegram ID {telegram_user_id}")

        return user

    def _get_or_create_agent(self, session, user_id: int, agent_name: str,
                           faction: str, level: Optional[int] = None) -> Tuple[Agent, bool, bool]:
        """Get existing agent or create new one with faction change detection."""
        agent = session.query(Agent).filter(Agent.agent_name == agent_name).first()

        is_new_agent = agent is None
        faction_changed = False

        if not agent:
            agent = Agent(
                user_id=user_id,
                agent_name=agent_name,
                faction=faction,
                level=level,
                is_active=True
            )
            session.add(agent)
            session.flush()
            logger.info(f"Created new agent: {agent_name} ({faction})")
        else:
            # Check for faction change
            if agent.faction != faction:
                # Record faction change
                faction_change = FactionChange(
                    agent_id=agent.id,
                    old_faction=agent.faction,
                    new_faction=faction,
                    change_reason='user_submission'
                )
                session.add(faction_change)

                # Update agent faction
                agent.faction = faction
                agent.updated_at = datetime.utcnow()
                faction_changed = True

                logger.warning(f"Agent {agent_name} faction changed: {agent.faction} -> {faction}")

            # Update agent level if provided
            if level is not None and agent.level != level:
                agent.level = level
                agent.updated_at = datetime.utcnow()

                logger.info(f"Agent {agent_name} level updated: {agent.level} -> {level}")

        return agent, is_new_agent, faction_changed

    def _create_individual_stats(self, session, submission_id: int,
                                parsed_stats: Dict) -> int:
        """Create individual stat records with proper iteration logic."""
        stats_count = 0

        for idx, stat_data in parsed_stats.items():
            # Skip header stats (keys 1-4) and non-numeric keys
            if isinstance(idx, int) and idx > 4:
                stat_name = stat_data.get('name', '')
                stat_value_str = stat_data.get('value', '0')
                stat_type = stat_data.get('type', 'N')  # Default to numeric

                # Skip empty stat names
                if not stat_name:
                    continue

                # Parse stat value based on type
                stat_value = self._parse_stat_value(stat_value_str, stat_type)

                agent_stat = AgentStat(
                    submission_id=submission_id,
                    stat_idx=idx,
                    stat_name=stat_name,
                    stat_value=stat_value,
                    stat_type=stat_type,
                    created_at=datetime.utcnow()
                )

                session.add(agent_stat)
                stats_count += 1

        session.flush()
        return stats_count

    def _create_progress_snapshots(self, session, agent_id: int,
                                  snapshot_date: date, parsed_stats: Dict) -> None:
        """Create progress snapshots for key leaderboard stats."""
        # Key stats to track for monthly leaderboards
        key_stats = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28]

        for stat_idx in key_stats:
            if stat_idx in parsed_stats:
                stat_data = parsed_stats[stat_idx]
                try:
                    stat_value_str = stat_data.get('value', '0')
                    stat_type = stat_data.get('type', 'N')
                    stat_value = self._parse_stat_value(stat_value_str, stat_type)

                    progress_snapshot = ProgressSnapshot(
                        agent_id=agent_id,
                        snapshot_date=snapshot_date,
                        stat_idx=stat_idx,
                        stat_value=stat_value,
                        created_at=datetime.utcnow()
                    )

                    session.add(progress_snapshot)

                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to create progress snapshot for stat {stat_idx}: {e}")
                    continue

    def _parse_stat_value(self, value_str: str, stat_type: str) -> int:
        """Parse stat value based on type."""
        if stat_type == 'N':  # Numeric
            return int(value_str.replace(',', '')) if value_str else 0
        elif stat_type == 'S':  # String
            return 0  # Strings get value 0 for numeric storage
        else:  # Unknown type
            try:
                return int(value_str.replace(',', '')) if value_str else 0
            except ValueError:
                return 0

    def _validate_parsed_stats(self, parsed_stats: Dict) -> Dict[str, Any]:
        """Validate parsed stats structure."""
        if not isinstance(parsed_stats, dict):
            return {'valid': False, 'error': 'Parsed stats must be a dictionary'}

        # Check for required header fields
        required_fields = {
            1: 'Agent Name',
            2: 'Agent Faction',
            3: 'Date',
            4: 'Time'
        }

        for field_idx, field_name in required_fields.items():
            if field_idx not in parsed_stats:
                return {'valid': False, 'error': f'Missing required field: {field_name}'}

            field_value = parsed_stats[field_idx].get('value', '').strip()
            if not field_value:
                return {'valid': False, 'error': f'Empty value for field: {field_name}'}

        # Check for minimum stats count (skip header fields 1-4)
        stat_count = len([k for k in parsed_stats.keys() if isinstance(k, int) and k > 4])
        if stat_count < 5:  # Minimum reasonable number of stats
            return {'valid': False, 'error': f'Insufficient stats: {stat_count} found (minimum 5 required)'}

        return {'valid': True}

    def get_agent_history(self, agent_name: str, stat_idx: Optional[int] = None,
                         limit: int = 10) -> List[Dict]:
        """
        Get submission history for an agent.

        Args:
            agent_name: Agent name to search for
            stat_idx: Optional specific stat index to filter by
            limit: Maximum number of submissions to return

        Returns:
            List of submission dictionaries
        """
        try:
            with self.db.session_scope() as session:
                # Find agent
                agent = session.query(Agent).filter(Agent.agent_name == agent_name).first()
                if not agent:
                    return []

                # Build query
                query = session.query(StatsSubmission).filter(
                    StatsSubmission.agent_id == agent.id
                ).order_by(StatsSubmission.submission_date.desc(),
                          StatsSubmission.submission_time.desc()).limit(limit)

                submissions = []
                for submission in query.all():
                    submission_data = {
                        'submission_id': submission.id,
                        'agent_name': agent_name,
                        'submission_date': submission.submission_date.isoformat(),
                        'submission_time': submission.submission_time.isoformat() if submission.submission_time else None,
                        'level': submission.level,
                        'lifetime_ap': submission.lifetime_ap,
                        'current_ap': submission.current_ap,
                        'xm_collected': submission.xm_collected,
                        'stats_type': submission.stats_type,
                        'processed_at': submission.processed_at.isoformat() if submission.processed_at else None
                    }

                    # Add individual stats if requested
                    if stat_idx is not None:
                        stat = session.query(AgentStat).filter(
                            AgentStat.submission_id == submission.id,
                            AgentStat.stat_idx == stat_idx
                        ).first()

                        submission_data['stat_value'] = stat.stat_value if stat else None
                        submission_data['stat_name'] = stat.stat_name if stat else None
                        submission_data['stat_type'] = stat.stat_type if stat else None
                    else:
                        # Get all stats for this submission
                        stats = session.query(AgentStat).filter(
                            AgentStat.submission_id == submission.id
                        ).all()

                        submission_data['stats'] = {
                            stat.stat_idx: {
                                'name': stat.stat_name,
                                'value': stat.stat_value,
                                'type': stat.stat_type
                            }
                            for stat in stats
                        }

                    submissions.append(submission_data)

                return submissions

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving agent history for {agent_name}: {e}")
            return []

    def get_agent_latest_stats(self, agent_name: str) -> Optional[Dict]:
        """Get the latest stats submission for an agent."""
        try:
            with self.db.session_scope() as session:
                agent = session.query(Agent).filter(Agent.agent_name == agent_name).first()
                if not agent:
                    return None

                # Get latest submission
                latest_submission = session.query(StatsSubmission).filter(
                    StatsSubmission.agent_id == agent.id
                ).order_by(StatsSubmission.submission_date.desc(),
                          StatsSubmission.submission_time.desc()).first()

                if not latest_submission:
                    return None

                # Get all individual stats for this submission
                individual_stats = session.query(AgentStat).filter(
                    AgentStat.submission_id == latest_submission.id
                ).all()

                # Build result dictionary
                result = {
                    'submission_id': latest_submission.id,
                    'agent_name': agent_name,
                    'faction': agent.faction,
                    'level': latest_submission.level,
                    'submission_date': latest_submission.submission_date.isoformat(),
                    'submission_time': latest_submission.submission_time.isoformat() if latest_submission.submission_time else None,
                    'lifetime_ap': latest_submission.lifetime_ap,
                    'current_ap': latest_submission.current_ap,
                    'xm_collected': latest_submission.xm_collected,
                    'stats_type': latest_submission.stats_type,
                    'processed_at': latest_submission.processed_at.isoformat() if latest_submission.processed_at else None,
                    'stats': {
                        stat.stat_idx: {
                            'name': stat.stat_name,
                            'value': stat.stat_value,
                            'type': stat.stat_type,
                            'created_at': stat.created_at.isoformat() if stat.created_at else None
                        }
                        for stat in individual_stats
                    }
                }

                return result

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving latest stats for {agent_name}: {e}")
            return None

    @database_error_tracking("get_leaderboard")
    def get_leaderboard_data(self, stat_idx: int, faction: Optional[str] = None,
                           period: str = 'all_time', limit: int = 20) -> List[Dict]:
        """
        Get leaderboard data for a specific stat.

        Args:
            stat_idx: Stat index to get leaderboard for
            faction: Optional faction filter ('Enlightened' or 'Resistance')
            period: Period filter ('all_time', 'monthly', 'weekly')
            limit: Maximum number of entries to return

        Returns:
            List of leaderboard entries with agent info and stat values
        """
        try:
            with self.db.session_scope() as session:
                # Build base query for agent stats
                query = session.query(AgentStat, Agent, StatsSubmission).join(
                    StatsSubmission, AgentStat.submission_id == StatsSubmission.id
                ).join(
                    Agent, StatsSubmission.agent_id == Agent.id
                ).filter(
                    AgentStat.stat_idx == stat_idx,
                    Agent.is_active == True
                )

                # Add faction filter if specified
                if faction:
                    query = query.filter(Agent.faction == faction)

                # Get the latest submission for each agent
                latest_submissions = session.query(
                    Agent.id,
                    StatsSubmission.submission_date,
                    StatsSubmission.submission_time,
                    StatsSubmission.id.label('submission_id')
                ).join(
                    StatsSubmission, Agent.id == StatsSubmission.agent_id
                ).group_by(
                    Agent.id
                ).having(
                    StatsSubmission.submission_date == session.query(
                        session.query(StatsSubmission.submission_date)
                    ).filter(StatsSubmission.agent_id == Agent.id)
                    .order_by(StatsSubmission.submission_date.desc())
                    .limit(1)
                    .as_scalar()
                ).subquery()

                # Filter to only latest submissions
                query = query.join(
                    latest_submissions,
                    (AgentStat.submission_id == latest_submissions.c.submission_id) &
                    (Agent.id == latest_submissions.c.id)
                )

                # Order by stat value (descending)
                query = query.order_by(AgentStat.stat_value.desc()).limit(limit)

                results = []
                for rank, (agent_stat, agent, submission) in enumerate(query.all(), 1):
                    entry = {
                        'rank': rank,
                        'agent_name': agent.agent_name,
                        'faction': agent.faction,
                        'level': agent.level,
                        'stat_name': agent_stat.stat_name,
                        'stat_value': agent_stat.stat_value,
                        'stat_type': agent_stat.stat_type,
                        'submission_date': submission.submission_date.isoformat(),
                        'submission_time': submission.submission_time.isoformat() if submission.submission_time else None,
                        'stats_type': submission.stats_type
                    }
                    results.append(entry)

                return results

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving leaderboard data for stat {stat_idx}: {e}")
            return []

    def get_user_agents(self, telegram_user_id: int) -> List[Dict]:
        """Get all agents associated with a Telegram user."""
        try:
            with self.db.session_scope() as session:
                user = session.query(User).filter(User.telegram_id == telegram_user_id).first()
                if not user:
                    return []

                agents = session.query(Agent).filter(
                    Agent.user_id == user.id,
                    Agent.is_active == True
                ).all()

                return [
                    {
                        'agent_id': agent.id,
                        'agent_name': agent.agent_name,
                        'faction': agent.faction,
                        'level': agent.level,
                        'created_at': agent.created_at.isoformat() if agent.created_at else None,
                        'updated_at': agent.updated_at.isoformat() if agent.updated_at else None
                    }
                    for agent in agents
                ]

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving agents for user {telegram_user_id}: {e}")
            return []

    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        try:
            with self.db.session_scope() as session:
                user_count = session.query(User).filter(User.is_active == True).count()
                agent_count = session.query(Agent).filter(Agent.is_active == True).count()
                submission_count = session.query(StatsSubmission).count()
                stat_count = session.query(AgentStat).count()

                # Faction breakdown
                enlightened_count = session.query(Agent).filter(
                    Agent.faction == 'Enlightened', Agent.is_active == True
                ).count()
                resistance_count = session.query(Agent).filter(
                    Agent.faction == 'Resistance', Agent.is_active == True
                ).count()

                return {
                    'users': user_count,
                    'agents': agent_count,
                    'submissions': submission_count,
                    'individual_stats': stat_count,
                    'factions': {
                        'Enlightened': enlightened_count,
                        'Resistance': resistance_count
                    }
                }

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving database stats: {e}")
            return {
                'error': str(e)
            }