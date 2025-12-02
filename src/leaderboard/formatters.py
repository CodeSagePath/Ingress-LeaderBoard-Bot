"""
Leaderboard formatters for Telegram display.

This module handles formatting of leaderboard data for Telegram messages,
including emoji formatting, badges, and responsive layouts.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from ..config.stats_config import get_stat_by_idx, format_stat_value, get_badge_level


logger = logging.getLogger(__name__)


class LeaderboardFormatter:
    """Formats leaderboard data for Telegram display."""

    def __init__(self):
        self.max_entries_per_message = 50  # Telegram message limit
        self.faction_emojis = {
            'Enlightened': '💚',
            'Resistance': '💙',
            'Enlightened': '💚',  # Handle typo
            'Resistance': '💙'    # Handle typo
        }

    def format_leaderboard(self, leaderboard_data: Dict, category: str,
                          faction: Optional[str] = None,
                          include_metadata: bool = True) -> str:
        """
        Format leaderboard data for Telegram display.

        Args:
            leaderboard_data: Data from LeaderboardGenerator.generate()
            category: Display category name
            faction: Faction filter if any
            include_metadata: Whether to include generation metadata

        Returns:
            Formatted message ready for Telegram
        """
        if 'error' in leaderboard_data:
            return f"❌ Error generating leaderboard: {leaderboard_data['error']}"

        stat_name = leaderboard_data.get('stat_name', category)
        period_type = leaderboard_data.get('period_type', 'unknown')
        entries = leaderboard_data.get('entries', [])
        total_entries = leaderboard_data.get('total_entries', 0)

        # Build header
        text = f"🏆 <b>{stat_name} Leaderboard</b>\n"

        # Add faction and period info
        if faction:
            faction_emoji = self.faction_emojis.get(faction, '🌐')
            text += f"{faction_emoji} <b>{faction.title()}</b>\n"

        if period_type != 'all_time':
            period_text = self._format_period_text(leaderboard_data)
            if period_text:
                text += f"📅 <b>{period_text}</b>\n"

        text += f"{'═' * 40}\n\n"

        if not entries:
            text += "No data available for this category yet.\n\n"
            text += "💡 <i>Submit your ALL TIME stats to appear on leaderboards!</i>"
            return text

        # Format entries
        text += self._format_entries(entries, stat_name, period_type)

        # Add footer metadata
        if include_metadata:
            text += self._format_footer(leaderboard_data, category)

        return text

    def format_agent_summary(self, agent_data: Dict, recent_data: Optional[Dict] = None) -> str:
        """
        Format personal agent statistics summary.

        Args:
            agent_data: Agent information and latest stats
            recent_data: Recent progress or activity data

        Returns:
            Formatted agent summary for Telegram
        """
        text = f"👤 <b>{agent_data.get('agent_name', 'Unknown Agent')}</b>\n\n"

        # Basic agent info
        faction = agent_data.get('faction', 'Unknown')
        faction_emoji = self.faction_emojis.get(faction, '🌐')
        level = agent_data.get('level', 1)

        text += f"{faction_emoji} <b>Faction:</b> {faction}\n"
        text += f"⭐ <b>Level:</b> {level}\n"

        # Lifetime stats
        lifetime_ap = agent_data.get('lifetime_ap', 0)
        if lifetime_ap:
            text += f"💫 <b>Lifetime AP:</b> {lifetime_ap:,}\n"

        current_ap = agent_data.get('current_ap', 0)
        if current_ap and current_ap != lifetime_ap:
            text += f"💰 <b>Current AP:</b> {current_ap:,}\n"

        text += "\n"

        # Recent activity
        if recent_data:
            text += self._format_recent_activity(recent_data)

        # Last submission info
        last_submission = agent_data.get('last_submission_date')
        if last_submission:
            days_ago = (datetime.now().date() - last_submission).days
            if days_ago == 0:
                text += f"📊 <b>Last submission:</b> Today\n"
            elif days_ago == 1:
                text += f"📊 <b>Last submission:</b> Yesterday\n"
            elif days_ago <= 7:
                text += f"📊 <b>Last submission:</b> {days_ago} days ago\n"
            elif days_ago <= 30:
                text += f"📊 <b>Last submission:</b> {days_ago} days ago\n"
            else:
                text += f"📊 <b>Last submission:</b> {last_submission.strftime('%Y-%m-%d')}\n"

        return text

    def format_progress_report(self, progress_data: List[Dict], agent_name: str,
                            period_days: int = 30) -> str:
        """
        Format agent progress report.

        Args:
            progress_data: List of progress improvements
            agent_name: Agent name for the report
            period_days: Number of days in the period

        Returns:
            Formatted progress report for Telegram
        """
        text = f"📈 <b>Progress Report for {agent_name}</b>\n"
        text += f"📅 <b>Period:</b> Last {period_days} days\n"
        text += f"{'═' * 40}\n\n"

        if not progress_data:
            text += "No progress data available for this period.\n\n"
            text += "💡 <i>Submit your stats regularly to track your progress!</i>"
            return text

        # Show top improvements
        for i, progress_item in enumerate(progress_data[:10], 1):
            stat_name = progress_item.get('stat_name', 'Unknown')
            improvement = progress_item.get('progress', 0)
            start_value = progress_item.get('start_value', 0)
            end_value = progress_item.get('end_value', 0)

            # Get stat definition for formatting
            stat_def = get_stat_by_idx(progress_item.get('stat_idx', 0))
            if stat_def:
                formatted_improvement = format_stat_value(stat_def['idx'], improvement)
                formatted_start = format_stat_value(stat_def['idx'], start_value)
                formatted_end = format_stat_value(stat_def['idx'], end_value)
            else:
                formatted_improvement = f"{improvement:,}"
                formatted_start = f"{start_value:,}"
                formatted_end = f"{end_value:,}"

            text += f"{i}. <b>{stat_name}</b>\n"
            text += f"   +{formatted_improvement} improvement\n"
            text += f"   {formatted_start} → {formatted_end}\n\n"

        return text

    def format_faction_comparison(self, faction_stats: Dict) -> str:
        """
        Format faction comparison statistics.

        Args:
            faction_stats: Statistics data for both factions

        Returns:
            Formatted faction comparison for Telegram
        """
        if 'error' in faction_stats:
            return f"❌ Error: {faction_stats['error']}"

        text = "🌐 <b>Faction Statistics</b>\n"
        text += f"{'═' * 40}\n\n"

        factions = faction_stats.get('factions', {})
        total_agents = faction_stats.get('total_agents', 0)

        for faction_name, data in factions.items():
            faction_emoji = self.faction_emojis.get(faction_name, '🌐')
            agent_count = data.get('agent_count', 0)
            avg_value = data.get('avg_value', 0)
            max_value = data.get('max_value', 0)
            total_value = data.get('total_value', 0)

            text += f"{faction_emoji} <b>{faction_name.title()}</b>\n"
            text += f"   👥 <b>Agents:</b> {agent_count}\n"

            # Calculate percentage of total
            if total_agents > 0:
                percentage = (agent_count / total_agents) * 100
                text += f"   📊 <b>Percentage:</b> {percentage:.1f}%\n"

            text += f"   📈 <b>Average:</b> {avg_value:,.0f}\n"
            text += f"   🏆 <b>Leader:</b> {max_value:,}\n"
            text += f"   💫 <b>Total:</b> {total_value:,}\n\n"

        return text

    def _format_entries(self, entries: List[Dict], stat_name: str,
                       period_type: str) -> str:
        """Format leaderboard entries."""
        text = ""
        stat_def = get_stat_by_idx(entries[0].get('stat_idx', 0)) if entries else None

        for entry in entries:
            rank = entry.get('rank', 0)
            agent_name = entry.get('agent_name', 'Unknown')
            faction = entry.get('faction', 'Unknown')
            value = entry.get('value', 0)
            level = entry.get('level')
            badge_level = entry.get('badge_level')

            # Rank medal for top 3
            if rank == 1:
                rank_display = "🥇"
            elif rank == 2:
                rank_display = "🥈"
            elif rank == 3:
                rank_display = "🥉"
            elif rank <= 10:
                rank_display = f"{rank}."
            else:
                rank_display = f"{rank}."

            faction_emoji = self.faction_emojis.get(faction, '🌐')

            # Format the stat value appropriately
            if stat_def:
                formatted_value = format_stat_value(stat_def['idx'], value)
            else:
                formatted_value = self._format_generic_value(value)

            # Badge info
            badge_text = f" ({badge_level})" if badge_level else ""

            # Progress indicator (for progress-based leaderboards)
            progress_info = ""
            if period_type in ['monthly', 'weekly'] and 'start_value' in entry:
                start_formatted = format_stat_value(stat_def['idx'], entry['start_value']) if stat_def else f"{entry['start_value']:,}"
                progress_info = f"\n    ↗️ {start_formatted} → {formatted_value}"

            text += f"{rank_display} {faction_emoji} <b>{agent_name}</b>{badge_text}\n"
            text += f"    {formatted_value}{progress_info}"

            # Add level if available and meaningful for this stat
            if level and stat_def and stat_def.get('show_level', False):
                text += f"\n    ⭐ Level {level}"

            text += "\n\n"

        return text.rstrip()

    def _format_period_text(self, leaderboard_data: Dict) -> str:
        """Format period information for header."""
        period_type = leaderboard_data.get('period_type', 'unknown')

        if period_type == 'monthly':
            period_start = leaderboard_data.get('period_start')
            if period_start:
                date_obj = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
                return f"{date_obj.strftime('%B %Y')}"
            return "Monthly"

        elif period_type == 'weekly':
            period_start = leaderboard_data.get('period_start')
            if period_start:
                date_obj = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
                return f"Week of {date_obj.strftime('%b %d')}"
            return "Weekly"

        elif period_type == 'daily':
            period_date = leaderboard_data.get('period_date')
            if period_date:
                date_obj = datetime.fromisoformat(period_date.replace('Z', '+00:00'))
                return date_obj.strftime('%A, %B %d, %Y')
            return "Daily"

        return period_type.title()

    def _format_footer(self, leaderboard_data: Dict, category: str) -> str:
        """Format footer with metadata."""
        text = "\n"

        # Entry count
        count = leaderboard_data.get('count', 0)
        total_entries = leaderboard_data.get('total_entries', 0)
        if total_entries > count:
            text += f"📊 Showing top {count} of {total_entries} agents\n\n"
        else:
            text += f"📊 Total agents: {count}\n\n"

        # Generation info
        generated_at = leaderboard_data.get('generated_at')
        from_cache = leaderboard_data.get('from_cache', False)

        if generated_at:
            try:
                gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                time_str = gen_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                cache_indicator = " (cached)" if from_cache else ""
                text += f"<i>Updated: {time_str}{cache_indicator}</i>"
            except:
                text += f"<i>Updated: Recently{cached if from_cache else ''}</i>"
        else:
            text += f"<i>Updated: Recently{cached if from_cache else ''}</i>"

        # Badge info for the stat
        stat_idx = leaderboard_data.get('stat_idx')
        if stat_idx is not None:
            badge_text = self._get_badge_description(stat_idx)
            if badge_text:
                text += f"\n\n💡 <i>{badge_text}</i>"

        return text

    def _format_recent_activity(self, recent_data: Dict) -> str:
        """Format recent activity information."""
        text = "📈 <b>Recent Activity:</b>\n"

        submissions = recent_data.get('submission_count', 0)
        if submissions:
            text += f"• {submissions} stats submissions (30 days)\n"

        improvements = recent_data.get('improvements', [])
        if improvements:
            top_improvement = improvements[0] if improvements else None
            if top_improvement:
                stat_name = top_improvement.get('stat_name', 'Unknown')
                improvement_value = top_improvement.get('progress', 0)
                text += f"• Best: +{improvement_value:,} {stat_name}\n"

        rankings = recent_data.get('rankings', {})
        if rankings:
            best_ranking = min(rankings.items(), key=lambda x: x[1])  # Lowest rank number
            stat_name, rank = best_ranking
            text += f"• Top rank: #{rank} in {stat_name}\n"

        text += "\n"
        return text

    def _format_generic_value(self, value: Union[int, float, str]) -> str:
        """Format a generic value with appropriate formatting."""
        if isinstance(value, (int, float)):
            # Try to convert to int if it's a whole number
            if isinstance(value, float) and value.is_integer():
                value = int(value)

            if isinstance(value, int):
                # Format with commas for large numbers
                if value >= 1000000:
                    return f"{value/1000000:.1f}M"
                elif value >= 1000:
                    return f"{value/1000:.1f}K"
                else:
                    return f"{value:,}"
            else:  # float
                return f"{value:,.1f}"
        else:
            return str(value)

    def _get_badge_description(self, stat_idx: int) -> Optional[str]:
        """Get badge description for a stat."""
        from ..config.stats_config import get_stat_by_idx
        stat_def = get_stat_by_idx(stat_idx)
        if not stat_def or 'badges' not in stat_def:
            return None

        badge_name = stat_def['badges']['name']
        levels = stat_def['badges']['levels']

        if len(levels) >= 3:
            return f"{badge_name} badges: Bronze ({levels[0]:,}), Silver ({levels[1]:,}), Gold ({levels[2]:,})"
        elif len(levels) >= 2:
            return f"{badge_name} badges: Bronze ({levels[0]:,}), Silver ({levels[1]:,})"
        elif len(levels) >= 1:
            return f"{badge_name} badge at {levels[0]:,}"
        else:
            return None

    def format_error_message(self, error_type: str, details: str = "") -> str:
        """
        Format error messages for various bot operations.

        Args:
            error_type: Type of error (parsing, validation, database, etc.)
            details: Additional error details

        Returns:
            Formatted error message for Telegram
        """
        error_messages = {
            'parsing_error': f"❌ <b>Stats Parsing Error</b>\n\n{details}\n\n"
                           "💡 Please copy your complete ALL TIME stats from Ingress Prime.",
            'validation_error': f"⚠️ <b>Invalid Stats Data</b>\n\n{details}\n\n"
                               "💡 Please check your stats for any formatting issues.",
            'database_error': f"🔧 <b>Database Error</b>\n\n"
                              "⚠️ Unable to save or retrieve data right now.\n\n"
                              "💡 Please try again in a few minutes.",
            'not_found': f"🔍 <b>Not Found</b>\n\n"
                        f"⚠️ {details}\n\n"
                        "💡 Please check the agent name or try a different search.",
            'permission_denied': f"🚫 <b>Access Denied</b>\n\n"
                                "⚠️ You don't have permission to perform this action.",
            'rate_limit': f"⏱️ <b>Please Wait</b>\n\n"
                         "⚠️ You're submitting stats too frequently.\n\n"
                         "💡 Please wait a few minutes before submitting again."
        }

        return error_messages.get(error_type, f"❌ <b>Error</b>\n\n{details}")

    def format_help_message(self, command: str) -> str:
        """
        Format help message for specific commands.

        Args:
            command: Command to get help for

        Returns:
            Formatted help message for Telegram
        """
        help_messages = {
            'submit': """
📊 <b>How to Submit Stats</b>

1. Open Ingress Prime on your device 📱
2. Tap your agent profile icon 👤
3. Select "ALL TIME" stats 📈
4. Tap the share/copy button 📋
5. Paste the copied text here 💬

<b>Important Tips:</b>
• Only "ALL TIME" stats are accepted
• Make sure the text starts with "Time Span"
• Your agent name must match exactly
• Submit stats regularly for accurate rankings

<b>Common Issues:</b>
• "Invalid stats format" → Copy complete stats text
• "Not ALL TIME stats" → Select ALL TIME in Ingress Prime
• "Missing fields" → Ensure all stat lines are included

<b>Questions?</b>
Use /help to see all available commands.
            """,

            'leaderboard': """
🏆 <b>Leaderboard Guide</b>

Browse leaderboards by different categories:

📈 <b>Progress-Based Leaderboards:</b>
• Monthly - Top improvements this month
• Weekly - Best gains this week
• Daily - Top submissions today

🏅 <b>All-Time Leaderboards:</b>
• Lifetime AP - Overall progression
• Explorer - Unique portals visited
• Builder - Resonators deployed
• Connector - Links created
• Mind Controller - Control fields created
• Recharger - XM recharged
• Trekker - Distance walked
• Hacker - Total hacks performed

🌐 <b>Faction Filters:</b>
• View all agents together
• Compare within Enlightened 💚
• Compare within Resistance 💙

💡 <b>Pro Tips:</b>
• Check your rank with /mystats
• Submit regularly to improve rankings
• Track your progress over time

Use /leaderboard to start browsing!
            """,

            'mystats': """
👤 <b>Personal Statistics Guide</b>

View your agent's complete performance history:

📊 <b>Available Information:</b>
• Latest stats submission
• Historical progression data
• Badge level progress
• Rank across different categories
• Recent activity summary

📈 <b>Progress Tracking:</b>
• Monthly and weekly improvements
• Badge level advancement tracking
• Faction ranking changes
• Submission history timeline

💡 <b>How to Use:</b>
1. Ensure you've submitted stats at least once
2. Type /mystats anytime to view your data
3. Regular submissions improve accuracy
4. Use leaderboards to compare with others

⚠️ <b>No Stats Yet?</b>
If you haven't submitted any stats:
1. Copy your ALL TIME stats from Ingress Prime
2. Paste them in this chat
3. Your data will be saved automatically
4. Use /mystats to view your progress

Your stats are stored securely and can be updated anytime!
            """
        }

        base_help = help_messages.get(command, "")
        if not base_help:
            return f"ℹ️ No specific help available for '/{command}'.\n\nUse /help to see all commands."

        return base_help + f"\n\n<b>Quick Actions:</b>\n• /start - Main menu\n• /help - All commands\n• /leaderboard - Browse stats"
