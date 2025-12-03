"""
Progress tracking and comparison system for Ingress Prime agents.

This module provides comprehensive progress analysis capabilities including:
- Individual progress calculation over time periods
- Progress leaderboard generation
- Progress report formatting for Telegram
- Multi-stat progress analysis

The system leverages the existing ProgressSnapshot table for efficient
progress calculations and integrates seamlessly with the existing
stats configuration and bot architecture.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import logging

from ..database.models import (
    User, Agent, StatsSubmission, AgentStat, ProgressSnapshot,
    get_latest_submission_for_agent
)
from ..database.connection import get_db_session
from ..config.stats_config import get_stat_by_idx, format_stat_value

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Progress tracking and comparison system for Ingress Prime agents.

    Calculates and formats progress over specified time periods,
    generates progress-based leaderboards, and provides
    statistics for agent improvement over time.
    """

    # Key stat indices for progress tracking
    # These are the most important stats that users want to track
    KEY_PROGRESS_STATS = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28]

    # Stat mappings for user-friendly references
    STAT_MAPPINGS = {
        'ap': 6,
        'explorer': 8,
        'xm': 11,
        'trekker': 13,
        'builder': 14,
        'connector': 15,
        'mindcontroller': 16,
        'liberator': 17,
        'recharger': 20,
        'hacker': 28
    }

    def __init__(self, session=None):
        """
        Initialize ProgressTracker with optional database session.

        Args:
            session: SQLAlchemy session instance or None to create new one
        """
        self.session = session or get_db_session()

    def calculate_progress(self, agent_name: str, days: int = 30) -> Dict:
        """
        Calculate progress for an agent over specified days.

        Analyzes ProgressSnapshot data to calculate improvement in key stats
        over the specified time period. Includes progress rate calculations
        and integrates with latest submission data for comprehensive analysis.

        Args:
            agent_name: Name of the Ingress agent
            days: Number of days to look back for progress calculation

        Returns:
            Dictionary containing comprehensive progress data:
            - agent_name, agent_id, faction, level
            - period_days, calculated_at
            - progress: Dict mapping stat_idx to progress information
            - error: Error message if calculation failed
        """
        try:
            # Get agent information
            agent = self.session.query(Agent).filter(
                Agent.agent_name == agent_name,
                Agent.is_active == True
            ).first()

            if not agent:
                return {'error': f'Agent {agent_name} not found'}

            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            logger.info(f"Calculating progress for {agent_name} over {days} days "
                       f"({start_date} to {end_date})")

            # Get progress snapshots for the period
            snapshots = self.session.query(ProgressSnapshot).filter(
                ProgressSnapshot.agent_id == agent.id,
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx.in_(self.KEY_PROGRESS_STATS)
            ).order_by(ProgressSnapshot.snapshot_date.asc()).all()

            # Get latest submission for comparison and current values
            latest_submission = get_latest_submission_for_agent(self.session, agent.id)

            # Calculate progress for each stat
            progress_data = self._calculate_stat_progress(snapshots, latest_submission)

            result = {
                'agent_name': agent_name,
                'agent_id': agent.id,
                'faction': agent.faction,
                'level': agent.level,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'progress': progress_data,
                'calculated_at': datetime.now().isoformat(),
                'snapshot_count': len(snapshots)
            }

            logger.info(f"Progress calculation completed for {agent_name}: "
                       f"{len(progress_data)} stats with positive progress")

            return result

        except Exception as e:
            logger.error(f"Progress calculation failed for {agent_name}: {e}")
            return {'error': f'Progress calculation failed: {str(e)}'}

    def calculate_progress_for_stat(self, stat_idx: int, days: int = 30,
                                   faction: Optional[str] = None) -> List[Dict]:
        """
        Calculate progress for all agents for a specific stat over time period.

        Generates a leaderboard-style list of agents sorted by their improvement
        in the specified stat over the given time period. Can be filtered
        by faction for faction-specific progress leaderboards.

        Args:
            stat_idx: Index of the stat to analyze (from stats_config.py)
            days: Number of days to look back
            faction: Optional faction filter ('Enlightened' or 'Resistance')

        Returns:
            List of progress entries sorted by improvement (descending):
            - agent_name, agent_id, faction, level
            - stat_idx, first_value, last_value, progress
            - first_date, last_date, snapshot_count
            - rank (added after sorting)
        """
        try:
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            logger.info(f"Calculating progress leaderboard for stat {stat_idx} "
                       f"over {days} days, faction: {faction or 'All'}")

            # Validate stat exists
            stat_def = get_stat_by_idx(stat_idx)
            if not stat_def:
                return [{'error': f'Invalid stat index: {stat_idx}'}]

            # Base query for progress snapshots
            query = self.session.query(
                ProgressSnapshot.agent_id,
                Agent.agent_name,
                Agent.faction,
                Agent.level,
                ProgressSnapshot.stat_idx,
                ProgressSnapshot.stat_value,
                ProgressSnapshot.snapshot_date
            ).join(Agent).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx == stat_idx,
                Agent.is_active == True
            )

            # Add faction filter if specified
            if faction:
                query = query.filter(Agent.faction == faction)

            # Order by agent and date for processing
            snapshots = query.order_by(
                ProgressSnapshot.agent_id,
                ProgressSnapshot.snapshot_date
            ).all()

            # Group by agent and calculate progress
            agent_progress = {}

            for snapshot in snapshots:
                agent_id = snapshot.agent_id
                if agent_id not in agent_progress:
                    agent_progress[agent_id] = {
                        'agent_name': snapshot.agent_name,
                        'agent_id': agent_id,
                        'faction': snapshot.faction,
                        'level': snapshot.level,
                        'stat_idx': stat_idx,
                        'first_value': snapshot.stat_value,
                        'first_date': snapshot.snapshot_date,
                        'last_value': snapshot.stat_value,
                        'last_date': snapshot.snapshot_date,
                        'progress': 0,
                        'snapshot_count': 0
                    }
                else:
                    # Update last value and date
                    agent_progress[agent_id]['last_value'] = snapshot.stat_value
                    agent_progress[agent_id]['last_date'] = snapshot.snapshot_date
                    agent_progress[agent_id]['snapshot_count'] += 1

            # Calculate progress for each agent
            results = []
            for agent_id, data in agent_progress.items():
                progress = data['last_value'] - data['first_value']

                # Only include agents with positive progress
                if progress > 0 and data['snapshot_count'] >= 1:
                    data['progress'] = progress
                    # Calculate progress rate (per day)
                    days_diff = (data['last_date'] - data['first_date']).days
                    if days_diff > 0:
                        data['progress_rate'] = progress / days_diff
                    else:
                        data['progress_rate'] = progress

                    results.append(data)

            # Sort by progress (descending) then add ranks
            results.sort(key=lambda x: x['progress'], reverse=True)

            for rank, entry in enumerate(results, 1):
                entry['rank'] = rank

            logger.info(f"Progress leaderboard generated for stat {stat_idx}: "
                       f"{len(results)} agents with positive progress")

            return results

        except Exception as e:
            logger.error(f"Progress leaderboard calculation failed for stat {stat_idx}: {e}")
            return [{'error': f'Progress calculation failed: {str(e)}'}]

    def format_progress_report(self, progress_data: Dict, agent_name: str, days: int = 30) -> str:
        """
        Format progress data into a human-readable report for Telegram.

        Creates a comprehensive progress report with emoji, formatted stat values,
        and visual progress indicators. Includes key insights and trends
        for the specified time period.

        Args:
            progress_data: Progress data from calculate_progress()
            agent_name: Name of the agent
            days: Number of days period

        Returns:
            Formatted string ready for Telegram message with HTML/Markdown
        """
        if 'error' in progress_data:
            return f"❌ <b>Error:</b> {progress_data['error']}"

        # Build report header
        faction_emoji = "💚" if progress_data.get('faction') == 'Enlightened' else "💙"
        level = progress_data.get('level', 'N/A')
        snapshot_count = progress_data.get('snapshot_count', 0)

        header = f"📈 <b>Progress Report for {agent_name}</b>\n\n"
        header += f"{faction_emoji} <b>Faction:</b> {progress_data.get('faction', 'Unknown')}\n"
        header += f"⭐ <b>Level:</b> {level}\n"
        header += f"📅 <b>Period:</b> Last {days} days\n"
        header += f"📊 <b>Data Points:</b> {snapshot_count} snapshots\n"
        header += f"{'═' * 35}\n\n"

        # Get progress information
        progress_stats = progress_data.get('progress', {})

        if not progress_stats:
            return header + "<b>No progress data available</b> for this period.\n\n" \
                          f"Try submitting your stats more regularly to track progress!"

        # Format progress stats
        progress_text = "<b>📊 Key Improvements:</b>\n\n"

        # Sort progress by amount (descending) and get top improvements
        sorted_progress = sorted(
            progress_stats.items(),
            key=lambda x: x[1].get('improvement', 0),
            reverse=True
        )

        # Show top 10 improvements
        for stat_idx, stat_info in sorted_progress[:10]:
            stat_def = get_stat_by_idx(stat_idx)
            if not stat_def:
                continue

            improvement = stat_info.get('improvement', 0)
            if improvement <= 0:
                continue

            # Format the stat name and improvement value
            stat_name = stat_def['name']
            formatted_improvement = format_stat_value(improvement, stat_idx)

            # Add progress rate if available
            rate_text = ""
            progress_rate = stat_info.get('progress_rate', 0)
            if progress_rate > 0:
                if stat_idx in [6]:  # AP
                    rate_text = f" ({progress_rate:,.0f} AP/day)"
                elif stat_idx in [8]:  # Portals
                    rate_text = f" ({progress_rate:.1f} portals/day)"
                elif stat_idx in [15]:  # Links
                    rate_text = f" ({progress_rate:.1f} links/day)"
                elif stat_idx in [16]:  # Fields
                    rate_text = f" ({progress_rate:.1f} fields/day)"

            progress_text += f"• <b>{stat_name}</b>: +{formatted_improvement}{rate_text}\n"

        if progress_text == "<b>📊 Key Improvements:</b>\n\n":
            progress_text += "<i>No positive progress in tracked stats this period</i>\n"

        # Add summary section
        total_improving_stats = sum(1 for stat_info in progress_stats.values()
                                   if stat_info.get('improvement', 0) > 0)

        summary_text = f"\n<b>📈 Summary:</b>\n\n"
        summary_text += f"• <b>{total_improving_stats}</b> stats showed improvement\n"
        summary_text += f"• <b>{len(progress_stats)}</b> stats tracked total\n"

        if total_improving_stats > 0:
            summary_text += f"• Keep up the great work! 🚀\n"

        return header + progress_text + summary_text

    def get_progress_leaderboard(self, stat_idx: int, days: int = 30,
                               limit: int = 20, faction: Optional[str] = None) -> List[Dict]:
        """
        Get progress leaderboard for a specific stat.

        Combines progress calculation with ranking to create a leaderboard
        showing which agents have improved the most in a specific stat
        over the given time period.

        Args:
            stat_idx: Index of the stat for leaderboard
            days: Number of days to look back
            limit: Maximum number of entries to return
            faction: Optional faction filter

        Returns:
            List of leaderboard entries sorted by progress (descending)
        """
        progress_list = self.calculate_progress_for_stat(stat_idx, days, faction)

        if progress_list and 'error' in progress_list[0]:
            return progress_list

        # Limit results and ensure rank information
        limited_results = progress_list[:limit]

        # Add additional leaderboard information
        stat_def = get_stat_by_idx(stat_idx)
        stat_name = stat_def['name'] if stat_def else f"Stat {stat_idx}"

        for entry in limited_results:
            entry['stat_name'] = stat_name
            entry['period_days'] = days
            entry['faction_filter'] = faction
            # Format progress for display
            entry['formatted_progress'] = format_stat_value(entry['progress'], stat_idx)

        return limited_results

    def get_multi_stat_progress_leaderboard(self, stat_indices: List[int],
                                          days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Get progress leaderboard combining multiple stats.

        Creates a comprehensive leaderboard that ranks agents by their
        combined improvement across multiple important stats. Useful for
        identifying well-rounded agents who are improving across categories.

        Args:
            stat_indices: List of stat indices to include in calculation
            days: Number of days to look back
            limit: Maximum number of results to return

        Returns:
            List of agents with their combined progress score
        """
        try:
            logger.info(f"Calculating multi-stat progress leaderboard for "
                       f"{len(stat_indices)} stats over {days} days")

            # Validate stat indices
            valid_stats = []
            for stat_idx in stat_indices:
                if get_stat_by_idx(stat_idx):
                    valid_stats.append(stat_idx)
                else:
                    logger.warning(f"Invalid stat index in multi-stat leaderboard: {stat_idx}")

            if not valid_stats:
                return [{'error': 'No valid stats provided'}]

            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Get all progress snapshots for the specified stats
            snapshots = self.session.query(ProgressSnapshot).filter(
                ProgressSnapshot.snapshot_date >= start_date,
                ProgressSnapshot.snapshot_date <= end_date,
                ProgressSnapshot.stat_idx.in_(valid_stats)
            ).all()

            # Group by agent and stat to calculate progress
            agent_stat_progress = {}

            for snapshot in snapshots:
                key = (snapshot.agent_id, snapshot.stat_idx)
                if key not in agent_stat_progress:
                    agent_stat_progress[key] = {
                        'first_value': snapshot.stat_value,
                        'first_date': snapshot.snapshot_date,
                        'last_value': snapshot.stat_value,
                        'last_date': snapshot.snapshot_date
                    }
                else:
                    # Update last value and date
                    if snapshot.snapshot_date > agent_stat_progress[key]['last_date']:
                        agent_stat_progress[key]['last_value'] = snapshot.stat_value
                        agent_stat_progress[key]['last_date'] = snapshot.snapshot_date

            # Group by agent and calculate total progress
            agent_totals = {}

            for (agent_id, stat_idx), progress_data in agent_stat_progress.items():
                progress = progress_data['last_value'] - progress_data['first_value']

                if progress > 0:  # Only count positive progress
                    if agent_id not in agent_totals:
                        agent_totals[agent_id] = {
                            'agent_id': agent_id,
                            'total_progress': 0,
                            'improving_stats': 0,
                            'stat_progress': {}
                        }

                    agent_totals[agent_id]['total_progress'] += progress
                    agent_totals[agent_id]['improving_stats'] += 1
                    agent_totals[agent_id]['stat_progress'][stat_idx] = progress

            # Get agent information and sort by total progress
            results = []

            for agent_id, data in agent_totals.items():
                # Get agent information
                agent = self.session.query(Agent).filter(
                    Agent.id == agent_id,
                    Agent.is_active == True
                ).first()

                if not agent:
                    continue

                # Only include agents improving in multiple stats
                if data['improving_stats'] >= len(valid_stats) * 0.5:  # At least 50% of stats
                    agent_data = {
                        'agent_id': agent_id,
                        'agent_name': agent.agent_name,
                        'faction': agent.faction,
                        'level': agent.level,
                        'total_progress': data['total_progress'],
                        'improving_stats': data['improving_stats'],
                        'total_stats': len(valid_stats),
                        'stat_progress': data['stat_progress']
                    }
                    results.append(agent_data)

            # Sort by total progress (descending) and add ranks
            results.sort(key=lambda x: x['total_progress'], reverse=True)

            for rank, entry in enumerate(results[:limit], 1):
                entry['rank'] = rank
                entry['period_days'] = days
                entry['stat_indices'] = valid_stats

            logger.info(f"Multi-stat progress leaderboard generated: "
                       f"{len(results)} agents, top {limit} returned")

            return results[:limit]

        except Exception as e:
            logger.error(f"Multi-stat progress leaderboard failed: {e}")
            return [{'error': f'Multi-stat progress calculation failed: {str(e)}'}]

    def _calculate_stat_progress(self, snapshots: List[ProgressSnapshot],
                                latest_submission: Optional[StatsSubmission]) -> Dict:
        """
        Calculate progress for each key stat.

        Internal method that processes snapshot data and latest submission
        to calculate progress for each tracked stat. Includes progress
        rate calculations and integrates current values.

        Args:
            snapshots: List of progress snapshots for the period
            latest_submission: Latest stats submission for current values

        Returns:
            Dictionary mapping stat_idx to progress information
        """
        progress_dict = {}

        # Group snapshots by stat_idx
        stat_snapshots = {}
        for snapshot in snapshots:
            stat_idx = snapshot.stat_idx
            if stat_idx not in stat_snapshots:
                stat_snapshots[stat_idx] = []
            stat_snapshots[stat_idx].append(snapshot)

        # Calculate progress for each stat
        for stat_idx, snap_list in stat_snapshots.items():
            if len(snap_list) < 1:
                continue

            # Sort by date
            snap_list.sort(key=lambda x: x.snapshot_date)

            first_snapshot = snap_list[0]
            last_snapshot = snap_list[-1]

            improvement = last_snapshot.stat_value - first_snapshot.stat_value

            # Calculate progress rate
            days_diff = (last_snapshot.snapshot_date - first_snapshot.snapshot_date).days
            progress_rate = improvement / days_diff if days_diff > 0 else improvement

            progress_dict[stat_idx] = {
                'improvement': improvement,
                'progress_rate': progress_rate,
                'first_value': first_snapshot.stat_value,
                'last_value': last_snapshot.stat_value,
                'first_date': first_snapshot.snapshot_date,
                'last_date': last_snapshot.snapshot_date,
                'snapshots_count': len(snap_list)
            }

        # Add information from latest submission if available
        if latest_submission:
            agent_stats = self.session.query(AgentStat).filter(
                AgentStat.submission_id == latest_submission.id,
                AgentStat.stat_idx.in_(self.KEY_PROGRESS_STATS)
            ).all()

            for agent_stat in agent_stats:
                stat_idx = agent_stat.stat_idx
                if stat_idx not in progress_dict:
                    progress_dict[stat_idx] = {
                        'improvement': 0,
                        'progress_rate': 0,
                        'latest_value': agent_stat.stat_value,
                        'latest_date': latest_submission.submission_date
                    }
                else:
                    progress_dict[stat_idx]['latest_value'] = agent_stat.stat_value
                    progress_dict[stat_idx]['latest_date'] = latest_submission.submission_date

        return progress_dict

    def get_agent_progress_summary(self, agent_name: str) -> Dict:
        """
        Get a comprehensive progress summary for an agent.

        Provides progress information across multiple time periods (7, 30, 90 days)
        to give agents a complete picture of their recent activity and improvement.
        Useful for enhanced /mystats command with progress trends.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary containing progress summaries for different periods
        """
        try:
            # Verify agent exists
            agent = self.session.query(Agent).filter(
                Agent.agent_name == agent_name,
                Agent.is_active == True
            ).first()

            if not agent:
                return {'error': f'Agent {agent_name} not found'}

            # Calculate progress for different periods
            periods = [7, 30, 90]
            summaries = {}

            for days in periods:
                progress_data = self.calculate_progress(agent_name, days)

                if 'error' not in progress_data:
                    # Count positive improvements
                    positive_progress = sum(
                        1 for stat_info in progress_data['progress'].values()
                        if stat_info.get('improvement', 0) > 0
                    )

                    # Calculate total improvement across all stats
                    total_improvement = sum(
                        stat_info.get('improvement', 0)
                        for stat_info in progress_data['progress'].values()
                    )

                    summaries[f'{days}_days'] = {
                        'period_days': days,
                        'improving_stats': positive_progress,
                        'total_stats': len(progress_data['progress']),
                        'total_improvement': total_improvement,
                        'snapshot_count': progress_data.get('snapshot_count', 0)
                    }
                else:
                    summaries[f'{days}_days'] = {
                        'error': progress_data['error']
                    }

            return {
                'agent_name': agent_name,
                'agent_id': agent.id,
                'faction': agent.faction,
                'level': agent.level,
                'periods': summaries,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Progress summary failed for {agent_name}: {e}")
            return {'error': f'Progress summary failed: {str(e)}'}

    @classmethod
    def resolve_stat_reference(cls, stat_ref: str) -> Optional[int]:
        """
        Resolve stat reference (name or index) to stat index.

        Args:
            stat_ref: Stat name (like 'ap', 'explorer') or index as string

        Returns:
            Stat index or None if not found
        """
        # Try stat mappings first (user-friendly names)
        stat_idx = cls.STAT_MAPPINGS.get(stat_ref.lower())
        if stat_idx:
            return stat_idx

        # Try parsing as integer
        try:
            stat_idx = int(stat_ref)
            if get_stat_by_idx(stat_idx):
                return stat_idx
        except ValueError:
            pass

        # Try exact name match
        stat_def = get_stat_by_name(stat_ref)
        if stat_def:
            return stat_def['idx']

        return None