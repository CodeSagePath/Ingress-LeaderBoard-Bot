"""
Enhanced bot handlers for progress tracking and comparison features.

This module provides comprehensive progress tracking commands including:
- /progress command for personal progress reports
- Enhanced /mystats command with progress trends
- /progressleaderboard command for improvement rankings
- Interactive callback handling for seamless navigation

All handlers integrate with the existing bot framework and maintain
consistent formatting, error handling, and user experience patterns.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from telegram.error import TelegramError

from .handlers import BotHandlers
from ..features.progress import ProgressTracker
from ..database.models import Agent, get_agent_by_telegram_id
from ..database.models import StatsSubmission, AgentStat

logger = logging.getLogger(__name__)


class ProgressHandlers(BotHandlers):
    """
    Enhanced bot handlers for progress tracking and comparison features.

    Extends the existing BotHandlers class to add progress-specific
    functionality while maintaining consistent patterns and error handling.
    """

    def __init__(self, db_connection=None):
        """
        Initialize ProgressHandlers with database connection.

        Args:
            db_connection: Database connection instance
        """
        super().__init__(db_connection)

    async def progress_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /progress command - Show personal progress report.

        Usage:
        /progress - Show 30-day progress for your agent
        /progress 7 - Show 7-day progress
        /progress 90 - Show 90-day progress

        Features:
        - Multiple time period support (7, 30, 90 days)
        - Interactive period selection via inline keyboard
        - Visual progress indicators with emoji
        - Integration with existing /mystats and /leaderboard commands
        """
        user = update.effective_user
        args = context.args if context.args else []

        try:
            # Parse arguments for time period
            days = 30  # Default
            if args:
                try:
                    days = int(args[0])
                    if days < 1 or days > 365:
                        days = 30
                except ValueError:
                    days = 30

            with self.db.session_scope() as session:
                tracker = ProgressTracker(session)
                
                # Get user's agent from database
                agent = get_agent_by_telegram_id(session, user.id)

                if not agent:
                    help_text = """
🔍 **Agent Not Found**

You haven't submitted any stats yet. To get started:

1. Open Ingress Prime 📱
2. Go to your Agent Profile 👤
3. Copy your ALL TIME stats 📊
4. Paste them here 💬

Once you've submitted stats, you can track your progress!
                    """
                    await update.message.reply_text(
                        help_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    return

                # Calculate progress for the specified period
                progress_data = tracker.calculate_progress(
                    agent.agent_name, days
                )

                # Format progress report
                progress_text = tracker.format_progress_report(
                    progress_data, agent.agent_name, days
                )

                # Add action buttons for navigation
                keyboard = [
                    [
                        InlineKeyboardButton("📊 My Stats", callback_data='mystats'),
                        InlineKeyboardButton("🏆 Leaderboards", callback_data='leaderboard')
                    ],
                    [
                        InlineKeyboardButton("⏰ 7 Days", callback_data=f'progress_7'),
                        InlineKeyboardButton("📅 30 Days", callback_data=f'progress_30'),
                        InlineKeyboardButton("📆 90 Days", callback_data=f'progress_90')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    progress_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )

                logger.info(f"Progress command for user {user.id}, agent {agent.agent_name}, period {days} days")

        except Exception as e:
            logger.error(f"Error in progress command for user {user.id}: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to calculate your progress. Please try again later.",
                parse_mode=ParseMode.HTML
            )

    async def enhanced_mystats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Enhanced /mystats command with progress trends.

        Shows:
        - Latest stats submission with formatted values
        - Progress trends over multiple periods (7, 30, 90 days)
        - Summary of improving stats for each period
        - Visual indicators and formatted display
        - Navigation buttons for progress views and leaderboards

        Replaces the basic /mystats functionality with comprehensive
        progress tracking integration.
        """
        user = update.effective_user
        
        try:
            with self.db.session_scope() as session:
                tracker = ProgressTracker(session)
                
                # Get user's agent
                agent = get_agent_by_telegram_id(session, user.id)

                if not agent:
                    help_text = """
🔍 **Agent Not Found**

You haven't submitted any stats yet. To get started:

1. Open Ingress Prime 📱
2. Go to your Agent Profile 👤
3. Copy your ALL TIME stats 📊
4. Paste them here 💬

Once you've submitted stats, you can view detailed progress reports!
                    """
                    await update.message.reply_text(
                        help_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    return

                # Get latest submission
                from ..database.models import StatsSubmission, AgentStat
                latest_submission = session.query(StatsSubmission).filter(
                    StatsSubmission.agent_id == agent.id
                ).order_by(StatsSubmission.submission_date.desc()).first()

                if not latest_submission:
                    help_text = """
📊 **No Stats Found**

You haven't submitted any stats yet. To get started:

1. Open Ingress Prime 📱
2. Copy your ALL TIME stats 📊
3. Paste them here 💬

Submit your stats to enable progress tracking!
                    """
                    await update.message.reply_text(
                        help_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    return

                # Get latest agent stats
                agent_stats = session.query(AgentStat).filter(
                    AgentStat.submission_id == latest_submission.id
                ).all()

                # Build enhanced stats report
                faction_emoji = "💚" if agent.faction == 'Enlightened' else "💙"
                header = f"{faction_emoji} **Agent Stats Report**\n\n"
                header += f"👤 **Agent:** {agent.agent_name}\n"
                header += f"🎯 **Level:** {agent.level or 'N/A'}\n"
                header += f"🏷️ **Faction:** {agent.faction}\n"
                header += f"📅 **Last Submission:** {latest_submission.submission_date.strftime('%Y-%m-%d')}\n\n"

                # Format key stats
                stats_text = "**📊 Latest Key Stats:**\n\n"

                # Key stat indices to display (user-friendly order)
                key_stats = [
                    (6, "Lifetime AP"),
                    (8, "Unique Portals Visited"),
                    (13, "Distance Walked"),
                    (14, "Resonators Deployed"),
                    (15, "Links Created"),
                    (16, "Control Fields Created"),
                    (17, "MU Captured"),
                    (20, "XM Recharged"),
                    (28, "Hacks")
                ]

                for stat_idx, stat_name in key_stats:
                    agent_stat = next((s for s in agent_stats if s.stat_idx == stat_idx), None)
                    if agent_stat:
                        from ..config.stats_config import format_stat_value
                        formatted_value = format_stat_value(agent_stat.stat_value, stat_idx)
                        stats_text += f"• **{stat_name}:** {formatted_value}\n"

                # Calculate progress summaries for different periods
                progress_text = "\n**📈 Recent Progress:**\n\n"

                # Get progress summary for multiple periods
                progress_summary = tracker.get_agent_progress_summary(agent.agent_name)

                if 'error' not in progress_summary:
                    periods = progress_summary.get('periods', {})

                    for days in [7, 30, 90]:
                        period_key = f'{days}_days'
                        if period_key in periods:
                            period_data = periods[period_key]
                            if 'error' not in period_data:
                                improving_stats = period_data.get('improving_stats', 0)
                                total_stats = period_data.get('total_stats', 0)

                                if improving_stats > 0:
                                    progress_text += f"• **Last {days} days:** {improving_stats}/{total_stats} stats improving ✅\n"
                                else:
                                    progress_text += f"• **Last {days} days:** No improvement detected ⏸\n"
                            else:
                                progress_text += f"• **Last {days} days:** Data unavailable ⚠️\n"
                        else:
                            progress_text += f"• **Last {days} days:** No data available ⏸\n"
                else:
                    progress_text += "• Progress data unavailable - submit more stats to track trends!\n"

                # Combine all sections
                full_text = header + stats_text + progress_text

                # Add action buttons
                keyboard = [
                    [
                        InlineKeyboardButton("📈 Progress (30 days)", callback_data='progress_30'),
                        InlineKeyboardButton("🏆 Leaderboards", callback_data='leaderboard')
                    ],
                    [
                        InlineKeyboardButton("📊 Submit Stats", callback_data='submit'),
                        InlineKeyboardButton("ℹ️ Help", callback_data='help')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    full_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )

                logger.info(f"Enhanced mystats command for user {user.id}, agent {agent.agent_name}")

        except Exception as e:
            logger.error(f"Error in enhanced mystats command for user {user.id}: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to retrieve your stats. Please try again later.",
                parse_mode=ParseMode.HTML
            )

    async def progress_leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle progress leaderboard requests.

        Shows top agents with most improvement in key stats over specified period.
        Supports both stat indices and user-friendly stat names.

        Usage:
        /progressleaderboard - Show AP progress leaderboard (30 days)
        /progressleaderboard ap 7 - Show AP progress over 7 days
        /progressleaderboard explorer 30 - Show portals visited progress over 30 days
        """
        args = context.args if context.args else []

        try:
            # Parse arguments
            days = 30  # Default
            stat_idx = 6  # Default to Lifetime AP
            stat_name = "Lifetime AP"

            # Parse stat index or name
            if args:
                first_arg = args[0]
                resolved_idx = ProgressTracker.resolve_stat_reference(first_arg)
                if resolved_idx:
                    stat_idx = resolved_idx
                    from ..config.stats_config import get_stat_by_idx
                    stat_def = get_stat_by_idx(stat_idx)
                    if stat_def:
                        stat_name = stat_def['name']
                else:
                    await update.message.reply_text(
                        f"❌ **Invalid Stat**\n\n"
                        f"'{first_arg}' is not a valid stat. Use stat names like:\n"
                        f"• `ap` (Lifetime AP)\n"
                        f"• `explorer` (Unique Portals Visited)\n"
                        f"• `builder` (Resonators Deployed)\n"
                        f"• `connector` (Links Created)\n"
                        f"• `mindcontroller` (Control Fields Created)\n"
                        f"• `trekker` (Distance Walked)\n"
                        f"• `recharger` (XM Recharged)\n"
                        f"• `hacker` (Hacks)",
                        parse_mode=ParseMode.HTML
                    )
                    return

            # Parse days if provided
            if len(args) > 1:
                try:
                    days = int(args[1])
                    if days < 1 or days > 365:
                        days = 30
                except ValueError:
                    days = 30

            # Get progress leaderboard
            with self.db.session_scope() as session:
                tracker = ProgressTracker(session)
                leaderboard = tracker.get_progress_leaderboard(
                    stat_idx, days, limit=15
                )

                if not leaderboard:
                    await update.message.reply_text(
                        "📊 **No Progress Data**\n\n"
                        "No agents have shown progress in this category yet. "
                        "Submit your stats regularly to see improvement rankings!",
                        parse_mode=ParseMode.HTML
                    )
                    return

                if 'error' in leaderboard[0] if leaderboard else False:
                    await update.message.reply_text(
                        "❌ **Error**\n\n"
                        "Failed to retrieve progress leaderboard. Please try again later.",
                        parse_mode=ParseMode.HTML
                    )
                    return

                # Format leaderboard
                faction_emoji = "🌐"
                header = f"🏆 {faction_emoji} **Progress Leaderboard**\n\n"
                header += f"📊 **Stat:** {stat_name}\n"
                header += f"📅 **Period:** Last {days} days\n"
                header += f"👥 **Showing:** Top {len(leaderboard)} agents\n\n"

                leaderboard_text = "**📈 Top Improvers:**\n\n"

                for entry in leaderboard[:10]:  # Show top 10
                    rank = entry.get('rank', 0)
                    agent_name = entry.get('agent_name', 'Unknown')
                    faction = entry.get('faction', 'Unknown')
                    progress = entry.get('progress', 0)

                    faction_emoji = "💚" if faction == 'Enlightened' else "💙"

                    # Add medal emojis for top 3
                    if rank == 1:
                        rank_emoji = "🥇"
                    elif rank == 2:
                        rank_emoji = "🥈"
                    elif rank == 3:
                        rank_emoji = "🥉"
                    else:
                        rank_emoji = f"#{rank:2d}"

                    # Format progress value
                    from ..config.stats_config import format_stat_value
                    formatted_progress = format_stat_value(progress, stat_idx)

                    leaderboard_text += f"{rank_emoji} {faction_emoji} **{agent_name}**: +{formatted_progress}\n"

                # Add stat summary
                if len(leaderboard) > 10:
                    remaining = len(leaderboard) - 10
                    leaderboard_text += f"\n... and {remaining} more agents"

                # Add action buttons for different stats
                keyboard = [
                    [
                        InlineKeyboardButton("📊 AP", callback_data='progress_lb_6'),
                        InlineKeyboardButton("🔍 Explorer", callback_data='progress_lb_8'),
                        InlineKeyboardButton("🚶 Trekker", callback_data='progress_lb_13'),
                        InlineKeyboardButton("🔨 Builder", callback_data='progress_lb_14')
                    ],
                    [
                        InlineKeyboardButton("🔗 Connector", callback_data='progress_lb_15'),
                        InlineKeyboardButton("🧠 Mind Controller", callback_data='progress_lb_16'),
                        InlineKeyboardButton("⚡ Recharger", callback_data='progress_lb_20'),
                        InlineKeyboardButton("💬 Hacker", callback_data='progress_lb_28')
                    ],
                    [
                        InlineKeyboardButton("📈 My Progress", callback_data='progress_30'),
                        InlineKeyboardButton("🏆 Regular Leaderboard", callback_data='leaderboard')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    header + leaderboard_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )

                logger.info(f"Progress leaderboard for stat {stat_idx} ({stat_name}), period {days} days")

        except Exception as e:
            logger.error(f"Error in progress leaderboard command: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to retrieve progress leaderboard. Please try again later.",
                parse_mode=ParseMode.HTML
            )

    async def handle_progress_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries from progress-related inline keyboards.

        Processes various callback patterns:
        - progress_X: Show progress report for X days
        - progress_lb_X: Show progress leaderboard for stat X
        - mystats, leaderboard, submit, help: Navigation callbacks
        """
        query = update.callback_query
        await query.answer()

        try:
            callback_data = query.data

            if callback_data.startswith('progress_'):
                # Progress report with specific days
                parts = callback_data.split('_')
                days = int(parts[1]) if len(parts) > 1 else 30

                # Calculate and format progress
                with self.db.session_scope() as session:
                    tracker = ProgressTracker(session)
                    agent = get_agent_by_telegram_id(session, user.id)

                    if not agent:
                        await query.edit_message_text(
                            "🔍 **Agent Not Found**\n\n"
                            "You haven't submitted any stats yet. Use /submit to get started!",
                            parse_mode=ParseMode.HTML
                        )
                        return

                    progress_data = tracker.calculate_progress(
                        agent.agent_name, days
                    )
                    progress_text = tracker.format_progress_report(
                        progress_data, agent.agent_name, days
                    )

                # Update navigation buttons
                keyboard = [
                    [
                        InlineKeyboardButton("⏰ 7 Days", callback_data='progress_7'),
                        InlineKeyboardButton("📅 30 Days", callback_data='progress_30'),
                        InlineKeyboardButton("📆 90 Days", callback_data='progress_90')
                    ],
                    [
                        InlineKeyboardButton("📊 My Stats", callback_data='mystats'),
                        InlineKeyboardButton("🏆 Leaderboards", callback_data='leaderboard')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    progress_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )

            elif callback_data.startswith('progress_lb_'):
                # Progress leaderboard for specific stat
                parts = callback_data.split('_')
                stat_idx = int(parts[2]) if len(parts) > 2 else 6

                from ..config.stats_config import get_stat_by_idx
                stat_def = get_stat_by_idx(stat_idx)
                if not stat_def:
                    await query.edit_message_text(
                        "❌ **Invalid Stat**\n\n"
                        "Please select a valid stat category.",
                        parse_mode=ParseMode.HTML
                    )
                    return

                # Get progress leaderboard
                with self.db.session_scope() as session:
                    tracker = ProgressTracker(session)
                    leaderboard = tracker.get_progress_leaderboard(
                        stat_idx, 30, limit=10
                    )

                # Format leaderboard
                faction_emoji = "🌐"
                header = f"🏆 {faction_emoji} **Progress Leaderboard**\n\n"
                header += f"📊 **Stat:** {stat_def['name']}\n"
                header += f"📅 **Period:** Last 30 days\n\n"

                leaderboard_text = "**📈 Top Improvers:**\n\n"

                for entry in leaderboard[:10]:
                    rank = entry.get('rank', 0)
                    agent_name = entry.get('agent_name', 'Unknown')
                    faction = entry.get('faction', 'Unknown')
                    progress = entry.get('progress', 0)

                    faction_emoji = "💚" if faction == 'Enlightened' else "💙"

                    # Add medal emojis
                    if rank == 1:
                        rank_emoji = "🥇"
                    elif rank == 2:
                        rank_emoji = "🥈"
                    elif rank == 3:
                        rank_emoji = "🥉"
                    else:
                        rank_emoji = f"#{rank:2d}"

                    # Format progress value
                    from ..config.stats_config import format_stat_value
                    formatted_progress = format_stat_value(progress, stat_idx)

                    leaderboard_text += f"{rank_emoji} {faction_emoji} **{agent_name}**: +{formatted_progress}\n"

                # Add navigation buttons
                keyboard = [
                    [
                        InlineKeyboardButton("📊 AP", callback_data='progress_lb_6'),
                        InlineKeyboardButton("🔍 Explorer", callback_data='progress_lb_8'),
                        InlineKeyboardButton("🚶 Trekker", callback_data='progress_lb_13'),
                        InlineKeyboardButton("🔨 Builder", callback_data='progress_lb_14')
                    ],
                    [
                        InlineKeyboardButton("🔗 Connector", callback_data='progress_lb_15'),
                        InlineKeyboardButton("🧠 Mind Controller", callback_data='progress_lb_16'),
                        InlineKeyboardButton("⚡ Recharger", callback_data='progress_lb_20'),
                        InlineKeyboardButton("💬 Hacker", callback_data='progress_lb_28')
                    ],
                    [
                        InlineKeyboardButton("📈 My Progress", callback_data='progress_30'),
                        InlineKeyboardButton("🏆 Regular Leaderboard", callback_data='leaderboard')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    header + leaderboard_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )

            # Handle other standard callbacks
            elif callback_data == 'mystats':
                # Trigger enhanced mystats command
                await self.enhanced_mystats_command(update, context)

            elif callback_data == 'leaderboard':
                # Trigger standard leaderboard command
                await self.leaderboard_command(update, context)

            elif callback_data in ['submit', 'help']:
                # Handle standard callbacks
                if callback_data == 'submit':
                    from .handlers import submit_command
                    await submit_command(update, context)
                elif callback_data == 'help':
                    await self.help_command(update, context)

        except Exception as e:
            logger.error(f"Error handling progress callback {query.data}: {e}")
            await query.edit_message_text(
                "❌ **Error**\n\n"
                "Failed to process your request. Please try again later.",
                parse_mode=ParseMode.HTML
            )


def register_progress_handlers(application) -> None:
    """
    Register all progress-related handlers with the application.

    Args:
        application: Telegram bot application instance
    """
    # Get database connection from application data
    db_connection = application.bot_data.get('db_connection')

    # Initialize handlers with database connection
    handlers = ProgressHandlers(db_connection)

    # Command handlers
    application.add_handler(CommandHandler("progress", handlers.progress_command))
    application.add_handler(CommandHandler("progressleaderboard", handlers.progress_leaderboard_command))

    # Replace existing mystats handler with enhanced version
    # Remove existing handler if present, then add enhanced one
    for handler in application.handlers:
        if hasattr(handler, 'command') and 'mystats' in handler.command:
            application.remove_handler(handler)
            break

    application.add_handler(CommandHandler("mystats", handlers.enhanced_mystats_command))

    # Callback query handlers for progress interactions
    application.add_handler(CallbackQueryHandler(
        handlers.handle_progress_callback,
        pattern=r'^(progress_|progress_lb_|mystats|leaderboard|submit|help)'
    ))

    logger.info("Progress handlers registered successfully with enhanced functionality")