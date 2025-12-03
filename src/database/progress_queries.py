"""
Optimized database queries for progress tracking and leaderboard generation.

This module provides efficient SQL queries for:
- Progress snapshot aggregation using Common Table Expressions (CTEs)
- Time-based stat comparisons for performance analysis
- Multi-stat progress leaderboard generation
- Faction-based progress summaries and analytics
- Bulk operations for snapshot creation and cleanup

All queries are optimized for large datasets using proper indexing
and efficient SQL patterns while integrating with existing database schema.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, desc, asc, text
from sqlalchemy.orm import aliased, Session
from .models import (
    User, Agent, StatsSubmission, AgentStat, ProgressSnapshot,
    FactionChange, LeaderboardCache
)

logger = logging.getLogger(__name__)


class ProgressQueries:
    """
    Optimized database queries for progress tracking and leaderboard generation.

    Provides efficient SQL queries for:
    - Progress snapshot aggregation
    - Time-based stat comparisons
    - Progress leaderboard generation
    - Agent progress history
    - Faction-based progress analysis
    """

    # Key stat indices for progress tracking
    # These correspond to the most important Ingress stats
    KEY_PROGRESS_STATS = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28]

    def __init__(self, session: Session):
        """
        Initialize ProgressQueries with SQLAlchemy session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_agent_progress_snapshots(self, agent_id: int, start_date: date,
                                     end_date: date, stat_indices: Optional[List[int]] = None) -> List[ProgressSnapshot]:
        """
        Get progress snapshots for an agent within date range.

        Efficiently retrieves progress snapshots with optional stat filtering.
        Uses existing database indexes for optimal performance.

        Args:
            agent_id: ID of the agent
            start_date: Start date for progress calculation
            end_date: End date for progress calculation
            stat_indices: Optional list of stat indices to filter by

        Returns:
            List of progress snapshots ordered by date
        """
        query = self.session.query(ProgressSnapshot).filter(
            ProgressSnapshot.agent_id == agent_id,
            ProgressSnapshot.snapshot_date >= start_date,
            ProgressSnapshot.snapshot_date <= end_date
        )

        if stat_indices:
            query = query.filter(ProgressSnapshot.stat_idx.in_(stat_indices))

        return query.order_by(ProgressSnapshot.snapshot_date.asc()).all()

    def get_stat_progress_leaderboard(self, stat_idx: int, start_date: date,
                                   end_date: date, limit: int = 20,
                                   faction: Optional[str] = None) -> List[Dict]:
        """
        Get progress leaderboard for a specific stat using optimized SQL.

        Uses Common Table Expression (CTE) for efficient aggregation on large datasets.
        Calculates progress difference between first and last snapshots for each agent.

        Args:
            stat_idx: Index of the stat to analyze
            start_date: Start date for progress calculation
            end_date: End date for progress calculation
            limit: Maximum number of results to return
            faction: Optional faction filter ('Enlightened' or 'Resistance')

        Returns:
            List of agents with their progress for the stat
        """
        try:
            logger.debug(f"Getting progress leaderboard for stat {stat_idx}, "
                        f"period {start_date} to {end_date}, limit {limit}, "
                        f"faction: {faction or 'All'}")

            # CTE for progress calculation
            progress_cte = self.session.query(
                ProgressSnapshot.agent_id,
                func.min(ProgressSnapshot.stat_value).label('first_value'),
                func.max(ProgressSnapshot.stat_value).label('last_value'),
                func.min(ProgressSnapshot.snapshot_date).label('first_date'),
                func.max(ProgressSnapshot.snapshot_date).label('last_date'),
                func.count(ProgressSnapshot.id).label('snapshot_count')
            ).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx == stat_idx
            ).group_by(
                ProgressSnapshot.agent_id
            ).having(
                func.max(ProgressSnapshot.stat_value) > func.min(ProgressSnapshot.stat_value)
            ).cte('progress_data')

            # Join with agent information
            query = self.session.query(
                Agent.id.label('agent_id'),
                Agent.agent_name,
                Agent.faction,
                Agent.level,
                progress_cte.c.first_value,
                progress_cte.c.last_value,
                progress_cte.c.first_date,
                progress_cte.c.last_date,
                (progress_cte.c.last_value - progress_cte.c.first_value).label('progress'),
                progress_cte.c.snapshot_count
            ).join(
                progress_cte,
                Agent.id == progress_cte.c.agent_id
            ).filter(
                Agent.is_active == True
            )

            # Add faction filter if specified
            if faction:
                query = query.filter(Agent.faction == faction)

            # Order by progress (descending) and limit
            query = query.order_by(
                desc(progress_cte.c.last_value - progress_cte.c.first_value)
            ).limit(limit)

            results = []
            for row in query.all():
                # Calculate progress rate (per day)
                days_diff = (row.last_date - row.first_date).days
                progress_rate = row.progress / days_diff if days_diff > 0 else row.progress

                results.append({
                    'agent_id': row.agent_id,
                    'agent_name': row.agent_name,
                    'faction': row.faction,
                    'level': row.level,
                    'stat_idx': stat_idx,
                    'first_value': row.first_value,
                    'last_value': row.last_value,
                    'first_date': row.first_date,
                    'last_date': row.last_date,
                    'progress': row.progress,
                    'progress_rate': progress_rate,
                    'snapshot_count': row.snapshot_count
                })

            logger.debug(f"Progress leaderboard query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in get_stat_progress_leaderboard for stat {stat_idx}: {e}")
            return []

    def get_multi_stat_progress_leaderboard(self, stat_indices: List[int],
                                          start_date: date, end_date: date,
                                          limit: int = 10,
                                          faction: Optional[str] = None) -> List[Dict]:
        """
        Get progress leaderboard for multiple stats combined.

        Calculates combined progress score across multiple stats.
        Uses efficient CTE-based aggregation for large datasets.

        Args:
            stat_indices: List of stat indices to include in calculation
            start_date: Start date for progress calculation
            end_date: End date for progress calculation
            limit: Maximum number of results to return
            faction: Optional faction filter

        Returns:
            List of agents with their combined progress score
        """
        try:
            logger.debug(f"Getting multi-stat progress leaderboard for {len(stat_indices)} stats, "
                        f"period {start_date} to {end_date}, limit {limit}")

            # Validate stat indices
            valid_stats = [s for s in stat_indices if s in self.KEY_PROGRESS_STATS]
            if not valid_stats:
                logger.warning(f"No valid stats found in {stat_indices}")
                return []

            # CTE for progress calculation per stat
            stat_progress_cte = self.session.query(
                ProgressSnapshot.agent_id,
                ProgressSnapshot.stat_idx,
                func.min(ProgressSnapshot.stat_value).label('first_value'),
                func.max(ProgressSnapshot.stat_value).label('last_value'),
                func.count(ProgressSnapshot.id).label('snapshot_count')
            ).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx.in_(valid_stats)
            ).group_by(
                ProgressSnapshot.agent_id,
                ProgressSnapshot.stat_idx
            ).having(
                func.max(ProgressSnapshot.stat_value) > func.min(ProgressSnapshot.stat_value)
            ).cte('stat_progress')

            # Aggregate total progress per agent
            total_progress_cte = self.session.query(
                stat_progress_cte.c.agent_id,
                func.sum(stat_progress_cte.c.last_value - stat_progress_cte.c.first_value).label('total_progress'),
                func.count(func.distinct(stat_progress_cte.c.stat_idx)).label('improving_stats'),
                func.count().label('total_stats')
            ).group_by(
                stat_progress_cte.c.agent_id
            ).cte('total_progress')

            # Join with agent information
            query = self.session.query(
                Agent.id.label('agent_id'),
                Agent.agent_name,
                Agent.faction,
                Agent.level,
                total_progress_cte.c.total_progress,
                total_progress_cte.c.improving_stats,
                total_progress_cte.c.total_stats
            ).join(
                total_progress_cte,
                Agent.id == total_progress_cte.c.agent_id
            ).filter(
                Agent.is_active == True,
                total_progress_cte.c.total_stats >= len(valid_stats) * 0.5  # At least 50% of stats
            )

            # Add faction filter if specified
            if faction:
                query = query.filter(Agent.faction == faction)

            # Order by total progress (descending) and limit
            query = query.order_by(desc(total_progress_cte.c.total_progress)).limit(limit)

            results = []
            for row in query.all():
                results.append({
                    'agent_id': row.agent_id,
                    'agent_name': row.agent_name,
                    'faction': row.faction,
                    'level': row.level,
                    'total_progress': int(row.total_progress) if row.total_progress else 0,
                    'improving_stats': int(row.improving_stats) if row.improving_stats else 0,
                    'total_stats': int(row.total_stats) if row.total_stats else 0,
                    'stat_indices': valid_stats
                })

            logger.debug(f"Multi-stat progress leaderboard returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in get_multi_stat_progress_leaderboard: {e}")
            return []

    def get_agent_progress_history(self, agent_id: int, stat_idx: int,
                                 months: int = 6) -> List[Dict]:
        """
        Get progress history for a specific stat over multiple months.

        Groups snapshots by month to show monthly progress trends.
        Useful for historical analysis and progress visualization.

        Args:
            agent_id: ID of the agent
            stat_idx: Index of the stat to analyze
            months: Number of months to look back

        Returns:
            List of monthly progress data points
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=months * 30)

            # Get all snapshots for the stat in the period
            snapshots = self.session.query(ProgressSnapshot).filter(
                ProgressSnapshot.agent_id == agent_id,
                ProgressSnapshot.stat_idx == stat_idx,
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date
            ).order_by(ProgressSnapshot.snapshot_date.asc()).all()

            # Group by month
            monthly_data = {}
            for snapshot in snapshots:
                month_key = snapshot.snapshot_date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'month': month_key,
                        'start_value': snapshot.stat_value,
                        'end_value': snapshot.stat_value,
                        'progress': 0,
                        'snapshot_count': 0
                    }
                else:
                    # Update end value and count
                    monthly_data[month_key]['end_value'] = snapshot.stat_value
                    monthly_data[month_key]['snapshot_count'] += 1

            # Calculate progress for each month
            results = []
            for month_data in monthly_data.values():
                month_data['progress'] = month_data['end_value'] - month_data['start_value']
                results.append(month_data)

            # Sort by month (ascending)
            results.sort(key=lambda x: x['month'])
            return results

        except Exception as e:
            logger.error(f"Error in get_agent_progress_history for agent {agent_id}, "
                         f"stat {stat_idx}: {e}")
            return []

    def get_faction_progress_summary(self, stat_idx: int, days: int = 30) -> Dict:
        """
        Get progress summary by faction for a specific stat.

        Calculates aggregate statistics for each faction including
        active agents, total progress, and average improvement.

        Args:
            stat_idx: Index of the stat to analyze
            days: Number of days to look back

        Returns:
            Dictionary with faction statistics
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Get progress data by faction
            progress_query = self.session.query(
                Agent.faction,
                func.count(func.distinct(ProgressSnapshot.agent_id)).label('active_agents'),
                func.sum(ProgressSnapshot.stat_value).label('total_value'),
                func.avg(ProgressSnapshot.stat_value).label('avg_value')
            ).join(
                ProgressSnapshot,
                Agent.id == ProgressSnapshot.agent_id
            ).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx == stat_idx,
                Agent.is_active == True
            ).group_by(Agent.faction)

            faction_data = {}
            total_active_agents = 0

            for row in progress_query.all():
                faction_data[row.faction] = {
                    'active_agents': int(row.active_agents) if row.active_agents else 0,
                    'total_value': int(row.total_value) if row.total_value else 0,
                    'avg_value': float(row.avg_value) if row.avg_value else 0.0
                }
                total_active_agents += faction_data[row.faction]['active_agents']

            return {
                'stat_idx': stat_idx,
                'period_days': days,
                'start_date': start_date,
                'end_date': end_date,
                'factions': faction_data,
                'total_active_agents': total_active_agents
            }

        except Exception as e:
            logger.error(f"Error in get_faction_progress_summary for stat {stat_idx}: {e}")
            return {}

    def create_progress_snapshots_from_submission(self, submission_id: int) -> bool:
        """
        Create progress snapshots from a new stats submission.

        Automatically creates progress snapshots for key stats when a new
        submission is processed. This ensures the progress tracking
        system has data for future analysis.

        Args:
            submission_id: ID of the stats submission

        Returns:
            True if snapshots were created successfully
        """
        try:
            # Get the submission and its stats
            submission = self.session.query(StatsSubmission).filter(
                StatsSubmission.id == submission_id
            ).first()

            if not submission:
                logger.warning(f"Submission {submission_id} not found for snapshot creation")
                return False

            # Get agent stats for this submission
            agent_stats = self.session.query(AgentStat).filter(
                AgentStat.submission_id == submission_id,
                AgentStat.stat_idx.in_(self.KEY_PROGRESS_STATS)
            ).all()

            # Create progress snapshots for key stats
            snapshots_to_create = []
            for agent_stat in agent_stats:
                # Check if snapshot already exists for this date and agent
                existing_snapshot = self.session.query(ProgressSnapshot).filter(
                    ProgressSnapshot.agent_id == submission.agent_id,
                    ProgressSnapshot.snapshot_date == submission.submission_date,
                    ProgressSnapshot.stat_idx == agent_stat.stat_idx
                ).first()

                if not existing_snapshot:
                    snapshots_to_create.append(ProgressSnapshot(
                        agent_id=submission.agent_id,
                        snapshot_date=submission.submission_date,
                        stat_idx=agent_stat.stat_idx,
                        stat_value=agent_stat.stat_value,
                        created_at=datetime.utcnow()
                    ))

            # Bulk insert snapshots
            if snapshots_to_create:
                self.session.bulk_save_objects(snapshots_to_create)
                self.session.commit()
                logger.debug(f"Created {len(snapshots_to_create)} progress snapshots "
                             f"for submission {submission_id}")
                return True
            else:
                logger.debug(f"No new progress snapshots needed for submission {submission_id}")
                return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating progress snapshots from submission {submission_id}: {e}")
            return False

    def cleanup_old_progress_snapshots(self, days_to_keep: int = 365) -> int:
        """
        Clean up old progress snapshots to manage database size.

        Removes progress snapshots older than the specified retention period
        to maintain database performance and storage efficiency.

        Args:
            days_to_keep: Number of days to keep snapshots for

        Returns:
            Number of snapshots deleted
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)

            deleted_count = self.session.query(ProgressSnapshot).filter(
                ProgressSnapshot.snapshot_date < cutoff_date
            ).delete()

            self.session.commit()

            logger.info(f"Cleaned up {deleted_count} old progress snapshots "
                        f"(older than {cutoff_date})")

            return deleted_count

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cleaning up old progress snapshots: {e}")
            return 0

    def get_progress_statistics(self, days: int = 30) -> Dict:
        """
        Get overall progress statistics for the system.

        Calculates aggregate statistics including active agents,
        total snapshots, progress by stat category, and faction breakdown.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with comprehensive progress statistics
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Overall statistics
            total_snapshots = self.session.query(func.count(ProgressSnapshot.id)).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date
            ).scalar() or 0

            active_agents = self.session.query(func.count(func.distinct(ProgressSnapshot.agent_id))).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date
            ).scalar() or 0

            # Progress by stat category
            stat_progress = self.session.query(
                ProgressSnapshot.stat_idx,
                func.count(ProgressSnapshot.id).label('snapshot_count'),
                func.avg(ProgressSnapshot.stat_value).label('avg_value'),
                func.max(ProgressSnapshot.stat_value).label('max_value')
            ).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx.in_(self.KEY_PROGRESS_STATS)
            ).group_by(ProgressSnapshot.stat_idx).all()

            # Faction breakdown
            faction_stats = self.get_faction_progress_summary(stat_idx=6, days=days)

            return {
                'period_days': days,
                'start_date': start_date,
                'end_date': end_date,
                'total_snapshots': total_snapshots,
                'active_agents': active_agents,
                'stats_by_category': [
                    {
                        'stat_idx': row.stat_idx,
                        'snapshot_count': int(row.snapshot_count) if row.snapshot_count else 0,
                        'avg_value': float(row.avg_value) if row.avg_value else 0.0,
                        'max_value': int(row.max_value) if row.max_value else 0
                    }
                    for row in stat_progress
                ],
                'faction_breakdown': faction_stats.get('factions', {}),
                'total_active_agents': faction_stats.get('total_active_agents', 0)
            }

        except Exception as e:
            logger.error(f"Error getting progress statistics: {e}")
            return {}