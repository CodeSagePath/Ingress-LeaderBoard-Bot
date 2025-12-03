"""
Leaderboard generator for Ingress Prime statistics.

This module handles generation of leaderboards for different stats,
time periods, and faction filters.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session

from ..database.models import (
    Agent, StatsSubmission, AgentStat, LeaderboardCache, ProgressSnapshot,
    get_latest_submission_for_agent
)
from ..config.stats_config import get_stat_by_idx, get_leaderboard_stats, format_stat_value


logger = logging.getLogger(__name__)


class LeaderboardGenerator:
    """Generates leaderboards from database data."""

    def __init__(self, session: Session):
        self.session = session
        self.cache_timeout = 300  # 5 minutes

    def generate(self, stat_idx: int, limit: int = 20,
                 faction: Optional[str] = None,
                 period: str = 'all_time',
                 use_cache: bool = True) -> Dict:
        """
        Generate leaderboard for a specific stat.

        Args:
            stat_idx: Index of the stat to generate leaderboard for
            limit: Maximum number of entries to return
            faction: Filter by faction ('Enlightened', 'Resistance', or None)
            period: Time period ('all_time', 'monthly', 'weekly', 'daily')
            use_cache: Whether to use cached results

        Returns:
            Dictionary containing leaderboard metadata and entries
        """
        stat_def = get_stat_by_idx(stat_idx)
        if not stat_def:
            return {'error': f'Invalid stat index: {stat_idx}'}

        # Check cache first
        if use_cache:
            cached_result = self._get_cached_leaderboard(stat_idx, faction, period)
            if cached_result:
                logger.debug(f"Using cached leaderboard for stat {stat_idx}")
                cached_result['from_cache'] = True
                return cached_result

        try:
            # Generate fresh leaderboard
            if period == 'all_time':
                result = self._generate_all_time_leaderboard(stat_idx, limit, faction)
            elif period == 'monthly':
                result = self._generate_monthly_leaderboard(stat_idx, limit, faction)
            elif period == 'weekly':
                result = self._generate_weekly_leaderboard(stat_idx, limit, faction)
            elif period == 'daily':
                result = self._generate_daily_leaderboard(stat_idx, limit, faction)
            else:
                return {'error': f'Invalid period: {period}'}

            # Add metadata
            result.update({
                'stat_idx': stat_idx,
                'stat_name': stat_def['name'],
                'stat_type': stat_def['type'],
                'period': period,
                'faction': faction,
                'generated_at': datetime.utcnow().isoformat(),
                'from_cache': False,
                'total_entries': result.get('count', 0)
            })

            # Cache the result
            if use_cache and result.get('entries'):
                self._cache_leaderboard(result, stat_idx, faction, period)

            return result

        except Exception as e:
            logger.error(f"Error generating leaderboard for stat {stat_idx}: {e}")
            return {'error': f'Database error: {str(e)}'}

    def _generate_all_time_leaderboard(self, stat_idx: int, limit: int,
                                     faction: Optional[str]) -> Dict:
        """Generate all-time leaderboard using latest submissions per agent."""
        # Subquery to get latest submission for each agent
        latest_submissions = self.session.query(
            StatsSubmission.agent_id,
            func.max(StatsSubmission.submission_date).label('max_date')
        ).group_by(StatsSubmission.agent_id).subquery()

        # Main query with joins
        query = self.session.query(
            Agent.agent_name,
            Agent.faction,
            AgentStat.stat_value,
            StatsSubmission.submission_date,
            StatsSubmission.level,
            StatsSubmission.lifetime_ap
        ).join(AgentStat, StatsSubmission.id == AgentStat.submission_id)\
         .join(Agent, StatsSubmission.agent_id == Agent.id)\
         .join(
             latest_submissions,
             and_(
                 StatsSubmission.agent_id == latest_submissions.c.agent_id,
                 StatsSubmission.submission_date == latest_submissions.c.max_date
             )
         ).filter(
            AgentStat.stat_idx == stat_idx,
            Agent.is_active == True
         )

        if faction:
            query = query.filter(Agent.faction == faction)

        # Order by stat value (descending for most stats)
        stat_def = get_stat_by_idx(stat_idx)
        order_by = desc(AgentStat.stat_value) if stat_def.get('type') == 'N' else asc(AgentStat.stat_value)
        query = query.order_by(order_by)

        results = query.limit(limit).all()

        entries = []
        for i, row in enumerate(results, 1):
            entries.append({
                'rank': i,
                'agent_name': row.agent_name,
                'faction': row.faction,
                'value': row.stat_value,
                'submission_date': row.submission_date,
                'level': row.level,
                'lifetime_ap': row.lifetime_ap,
                'badge_level': self._get_badge_level(stat_idx, row.stat_value)
            })

        return {
            'entries': entries,
            'count': len(entries),
            'period_type': 'all_time'
        }

    def _generate_monthly_leaderboard(self, stat_idx: int, limit: int,
                                    faction: Optional[str]) -> Dict:
        """Generate monthly leaderboard based on progress."""
        current_date = datetime.utcnow().date()
        month_start = current_date.replace(day=1)

        # Get agent progress for current month
        progress_data = self._get_progress_in_period(
            stat_idx, month_start, current_date, faction
        )

        entries = []
        for i, agent_data in enumerate(progress_data[:limit], 1):
            entries.append({
                'rank': i,
                'agent_name': agent_data['agent_name'],
                'faction': agent_data['faction'],
                'value': agent_data['progress'],
                'start_value': agent_data['start_value'],
                'end_value': agent_data['end_value'],
                'submission_count': agent_data['submission_count'],
                'badge_level': self._get_badge_level(stat_idx, agent_data['progress'])
            })

        return {
            'entries': entries,
            'count': len(entries),
            'period_type': 'monthly',
            'period_start': month_start.isoformat(),
            'period_end': current_date.isoformat()
        }

    def _generate_weekly_leaderboard(self, stat_idx: int, limit: int,
                                    faction: Optional[str]) -> Dict:
        """Generate weekly leaderboard based on progress."""
        current_date = datetime.utcnow().date()
        week_start = current_date - timedelta(days=current_date.weekday())

        # Get agent progress for current week
        progress_data = self._get_progress_in_period(
            stat_idx, week_start, current_date, faction
        )

        entries = []
        for i, agent_data in enumerate(progress_data[:limit], 1):
            entries.append({
                'rank': i,
                'agent_name': agent_data['agent_name'],
                'faction': agent_data['faction'],
                'value': agent_data['progress'],
                'start_value': agent_data['start_value'],
                'end_value': agent_data['end_value'],
                'submission_count': agent_data['submission_count'],
                'badge_level': self._get_badge_level(stat_idx, agent_data['progress'])
            })

        return {
            'entries': entries,
            'count': len(entries),
            'period_type': 'weekly',
            'period_start': week_start.isoformat(),
            'period_end': current_date.isoformat()
        }

    def _generate_daily_leaderboard(self, stat_idx: int, limit: int,
                                   faction: Optional[str]) -> Dict:
        """Generate daily leaderboard (for today's submissions only)."""
        today = datetime.utcnow().date()

        # Query for today's submissions
        query = self.session.query(
            Agent.agent_name,
            Agent.faction,
            AgentStat.stat_value,
            StatsSubmission.submission_date,
            StatsSubmission.level
        ).join(AgentStat, StatsSubmission.id == AgentStat.submission_id)\
         .join(Agent, StatsSubmission.agent_id == Agent.id)\
         .filter(
            AgentStat.stat_idx == stat_idx,
            StatsSubmission.submission_date == today,
            Agent.is_active == True
         )

        if faction:
            query = query.filter(Agent.faction == faction)

        stat_def = get_stat_by_idx(stat_idx)
        order_by = desc(AgentStat.stat_value) if stat_def.get('type') == 'N' else asc(AgentStat.stat_value)
        query = query.order_by(order_by)

        results = query.limit(limit).all()

        entries = []
        for i, row in enumerate(results, 1):
            entries.append({
                'rank': i,
                'agent_name': row.agent_name,
                'faction': row.faction,
                'value': row.stat_value,
                'submission_date': row.submission_date,
                'level': row.level,
                'badge_level': self._get_badge_level(stat_idx, row.stat_value)
            })

        return {
            'entries': entries,
            'count': len(entries),
            'period_type': 'daily',
            'period_date': today.isoformat()
        }

    def _get_progress_in_period(self, stat_idx: int, start_date: date,
                                end_date: date, faction: Optional[str]) -> List[Dict]:
        """
        Get agent progress within a specific period.

        Returns agents with the most improvement in the given stat during the period.
        """
        # Complex query to calculate progress for each agent
        period_submissions = self.session.query(
            AgentStat.submission_id,
            AgentStat.stat_idx,
            AgentStat.stat_value,
            StatsSubmission.agent_id,
            StatsSubmission.submission_date,
            Agent.agent_name,
            Agent.faction
        ).join(StatsSubmission, AgentStat.submission_id == StatsSubmission.id)\
         .join(Agent, StatsSubmission.agent_id == Agent.id)\
         .filter(
            AgentStat.stat_idx == stat_idx,
            StatsSubmission.submission_date >= start_date,
            StatsSubmission.submission_date <= end_date,
            Agent.is_active == True
         )

        if faction:
            period_submissions = period_submissions.filter(Agent.faction == faction)

        # Get the first and last submission for each agent in the period
        submissions_by_agent = {}
        for row in period_submissions.all():
            agent_id = row.agent_id
            if agent_id not in submissions_by_agent:
                submissions_by_agent[agent_id] = {
                    'agent_name': row.agent_name,
                    'faction': row.faction,
                    'submissions': []
                }
            submissions_by_agent[agent_id]['submissions'].append({
                'date': row.submission_date,
                'value': row.stat_value
            })

        # Calculate progress for each agent
        progress_data = []
        for agent_data in submissions_by_agent.values():
            submissions = sorted(agent_data['submissions'], key=lambda x: x['date'])
            if len(submissions) < 2:
                continue  # Need at least 2 submissions to measure progress

            start_value = submissions[0]['value']
            end_value = submissions[-1]['value']
            progress = end_value - start_value

            if progress <= 0:
                continue  # Only include agents with positive progress

            progress_data.append({
                'agent_name': agent_data['agent_name'],
                'faction': agent_data['faction'],
                'progress': progress,
                'start_value': start_value,
                'end_value': end_value,
                'submission_count': len(submissions)
            })

        # Sort by progress (descending)
        progress_data.sort(key=lambda x: x['progress'], reverse=True)
        return progress_data

    def _get_cached_leaderboard(self, stat_idx: int, faction: Optional[str],
                                period: str) -> Optional[Dict]:
        """Get cached leaderboard if available and not expired."""
        cache_entry = self.session.query(LeaderboardCache).filter(
            LeaderboardCache.stat_idx == stat_idx,
            LeaderboardCache.period == period,
            LeaderboardCache.faction == faction,
            LeaderboardCache.expires_at > datetime.utcnow()
        ).first()

        if not cache_entry:
            return None

        # Parse cached JSON data
        try:
            import json
            cached_data = json.loads(cache_entry.cache_data)
            logger.debug(f"Cache hit for stat {stat_idx}, period {period}")
            return cached_data
        except Exception as e:
            logger.error(f"Error parsing cached leaderboard: {e}")
            return None

    def _cache_leaderboard(self, result: Dict, stat_idx: int,
                          faction: Optional[str], period: str) -> None:
        """Cache the generated leaderboard."""
        try:
            import json
            cache_data = json.dumps(result)

            # Calculate expiry time
            expires_at = datetime.utcnow() + timedelta(seconds=self.cache_timeout)

            # Remove existing cache entry
            self.session.query(LeaderboardCache).filter(
                LeaderboardCache.stat_idx == stat_idx,
                LeaderboardCache.period == period,
                LeaderboardCache.faction == faction
            ).delete()

            # Create new cache entry
            cache_entry = LeaderboardCache(
                stat_idx=stat_idx,
                stat_name=result.get('stat_name', f'Stat {stat_idx}'),
                period=period,
                faction=faction,
                cache_data=cache_data,
                cache_size=result.get('count', 0),
                min_value=self._get_min_value(result),
                max_value=self._get_max_value(result),
                expires_at=expires_at
            )

            self.session.add(cache_entry)
            self.session.commit()

            logger.debug(f"Cached leaderboard for stat {stat_idx}, period {period}")

        except Exception as e:
            logger.error(f"Error caching leaderboard: {e}")
            self.session.rollback()

    def _get_min_value(self, result: Dict) -> Optional[int]:
        """Get minimum value from leaderboard entries."""
        entries = result.get('entries', [])
        if not entries:
            return None

        values = [entry.get('value', 0) for entry in entries if entry.get('value') is not None]
        return min(values) if values else None

    def _get_max_value(self, result: Dict) -> Optional[int]:
        """Get maximum value from leaderboard entries."""
        entries = result.get('entries', [])
        if not entries:
            return None

        values = [entry.get('value', 0) for entry in entries if entry.get('value') is not None]
        return max(values) if values else None

    def _get_badge_level(self, stat_idx: int, value: int) -> Optional[str]:
        """Get badge level for a stat value."""
        from ..config.stats_config import get_badge_level
        badge_level, _ = get_badge_level(stat_idx, value)
        return badge_level

    def get_agent_rank(self, agent_id: int, stat_idx: int,
                      period: str = 'all_time') -> Optional[Dict]:
        """
        Get an agent's rank for a specific stat.

        Args:
            agent_id: Database ID of the agent
            stat_idx: Index of the stat to check
            period: Time period for ranking

        Returns:
            Dictionary with rank information or None if not found
        """
        try:
            # Get agent's latest value for this stat
            agent_stat = self.session.query(AgentStat.stat_value)\
                .join(StatsSubmission)\
                .filter(
                    StatsSubmission.agent_id == agent_id,
                    AgentStat.stat_idx == stat_idx
                )\
                .order_by(StatsSubmission.submission_date.desc())\
                .first()

            if not agent_stat:
                return None

            agent_value = agent_stat.stat_value

            # Count agents with better values
            better_agents_count = self._count_better_agents(stat_idx, agent_value)

            # Get agent's faction
            agent = self.session.query(Agent).filter(Agent.id == agent_id).first()
            agent_faction = agent.faction if agent else None

            return {
                'agent_id': agent_id,
                'stat_idx': stat_idx,
                'agent_value': agent_value,
                'rank': better_agents_count + 1,
                'total_agents': better_agents_count + 1,
                'faction': agent_faction,
                'period': period,
                'calculated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating agent rank: {e}")
            return None

    def _count_better_agents(self, stat_idx: int, agent_value: int) -> int:
        """Count number of agents with better values for a stat."""
        # Get latest submission for each agent with better value
        better_query = self.session.query(StatsSubmission.agent_id)\
            .join(AgentStat)\
            .filter(
                AgentStat.stat_idx == stat_idx,
                AgentStat.stat_value > agent_value
            )\
            .distinct()

        return better_query.count()

    def get_faction_summary(self, stat_idx: int) -> Dict:
        """
        Get summary statistics by faction for a stat.

        Args:
            stat_idx: Index of the stat to analyze

        Returns:
            Dictionary with faction statistics
        """
        try:
            # Query faction averages, counts, etc.
            stats = self.session.query(
                Agent.faction,
                func.count(Agent.id).label('agent_count'),
                func.avg(AgentStat.stat_value).label('avg_value'),
                func.min(AgentStat.stat_value).label('min_value'),
                func.max(AgentStat.stat_value).label('max_value'),
                func.sum(AgentStat.stat_value).label('total_value')
            ).join(AgentStat, StatsSubmission.id == AgentStat.submission_id)\
             .join(Agent, StatsSubmission.agent_id == Agent.id)\
             .filter(
                AgentStat.stat_idx == stat_idx,
                Agent.is_active == True
             )\
             .group_by(Agent.faction)\
             .all()

            summary = {'factions': {}, 'total_agents': 0}
            total_agents = 0

            for row in stats:
                faction_data = {
                    'agent_count': row.agent_count,
                    'avg_value': float(row.avg_value) if row.avg_value else 0,
                    'min_value': row.min_value,
                    'max_value': row.max_value,
                    'total_value': row.total_value
                }
                summary['factions'][row.faction] = faction_data
                total_agents += row.agent_count

            summary['total_agents'] = total_agents
            summary['stat_idx'] = stat_idx
            summary['calculated_at'] = datetime.utcnow().isoformat()

            return summary

        except Exception as e:
            logger.error(f"Error calculating faction summary: {e}")
            return {'error': f'Database error: {str(e)}'}

    def get_leaderboard_for_faction(self, stat_idx: int, limit: int = 20,
                                    faction: Optional[str] = None,
                                    period: str = 'all_time') -> Dict:
        """
        Generate faction-specific leaderboard.

        Args:
            stat_idx: Index of the stat to generate leaderboard for
            limit: Maximum number of entries to return
            faction: Filter by faction ('Enlightened', 'Resistance', or None for all)
            period: Time period ('all_time', 'monthly', 'weekly', 'daily')

        Returns:
            Dictionary containing faction-specific leaderboard data
        """
        return self.generate(stat_idx, limit, faction, period, use_cache=True)

    def get_faction_summary(self, stat_idx: int) -> Dict:
        """
        Get faction participation statistics for a stat.

        Args:
            stat_idx: Index of the stat to analyze

        Returns:
            Dictionary with faction participation statistics
        """
        return self.get_action_summary(stat_idx)

    def get_top_agents_by_faction(self, stat_idx: int, faction: str,
                                 limit: int = 20, period: str = 'all_time') -> Dict:
        """
        Get top agents filtered by specific faction.

        Args:
            stat_idx: Index of the stat to generate leaderboard for
            faction: Faction to filter by ('Enlightened' or 'Resistance')
            limit: Maximum number of entries to return
            period: Time period ('all_time', 'monthly', 'weekly', 'daily')

        Returns:
            Dictionary containing top agents from the specified faction
        """
        if faction not in ['Enlightened', 'Resistance']:
            return {'error': f'Invalid faction: {faction}. Must be Enlightened or Resistance'}

        return self.generate(stat_idx, limit, faction, period, use_cache=True)

    def clear_expired_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of cache entries removed
        """
        try:
            count = self.session.query(LeaderboardCache)\
                .filter(LeaderboardCache.expires_at <= datetime.utcnow())\
                .count()

            self.session.query(LeaderboardCache)\
                .filter(LeaderboardCache.expires_at <= datetime.utcnow())\
                .delete()

            self.session.commit()

            if count > 0:
                logger.info(f"Cleared {count} expired leaderboard cache entries")

            return count

        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            self.session.rollback()
            return 0