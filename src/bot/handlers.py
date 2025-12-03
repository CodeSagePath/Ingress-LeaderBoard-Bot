"""
Telegram bot handlers for Ingress Prime leaderboard bot.

This module contains all command and message handlers for the bot.
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError

from ..parsers.stats_parser import StatsParser
from ..parsers.validator import StatsValidator
from ..database.models import (
    User, Agent, StatsSubmission, AgentStat, FactionChange, ProgressSnapshot,
    get_agent_by_telegram_id, get_latest_submission_for_agent, get_leaderboard_for_stat
)
from ..database.stats_database import StatsDatabase
from ..config.stats_config import get_stat_by_idx, format_stat_value, get_leaderboard_stats


logger = logging.getLogger(__name__)


class BotHandlers:
    """Main handler class for all bot commands and messages."""

    def __init__(self, db_connection=None):
        self.parser = StatsParser()
        self.validator = StatsValidator()
        self.stats_db = StatsDatabase(db_connection) if db_connection else None

        # Mapping of callback data to stat indices for leaderboard categories
        # This matches the task requirements for stat identification
        self.STAT_MAPPING = {
            'ap': 6,           # Lifetime AP
            'explorer': 8,     # Unique Portals Visited
            'connector': 15,    # Links Created
            'mindcontroller': 16, # Control Fields Created
            'recharger': 20,    # XM Recharged
            'builder': 14,       # Resonators Deployed
            'hacker': 28,        # Hacks
            'trekker': 13,        # Distance Walked
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command - Welcome message and basic instructions.
        """
        welcome_text = """
🎮 <b>Welcome to Ingress Prime Leaderboard Bot!</b>

I can help you track your Ingress stats and compete with other agents.

<b>Commands:</b>
• /submit - Submit your stats (or just paste them)
• /leaderboard - View leaderboards by category
• /mystats - View your stats history and progress
• /help - Show detailed help information

<b>How to submit stats:</b>
1. Open Ingress Prime 📱
2. Go to your Agent Profile 👤
3. Tap on "ALL TIME" stats 📊
4. Copy the stats text 📋
5. Paste it here in this chat 💬

<b>Important:</b>
• Only ALL TIME stats are accepted
• Make sure the text starts with "Time Span"
• Your agent name must match exactly

Ready to start? Just paste your stats!
        """

        try:
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"Start command from user {update.effective_user.id}")
        except TelegramError as e:
            logger.error(f"Error sending welcome message: {e}")
            await update.message.reply_text(
                "Welcome! I can help track your Ingress stats. Use /help for more information."
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command - Detailed help information.
        """
        help_text = """
📚 <b>Ingress Prime Leaderboard Bot - Help</b>

🔥 <b>Core Features:</b>
• <b>Stats Submission</b> - Submit your ALL TIME stats from Ingress Prime
• <b>Leaderboards</b> - Compete in 25+ different categories
• <b>Progress Tracking</b> - Monitor your improvements over time
• <b>Personal Stats</b> - View your complete submission history

📊 <b>Submitting Stats:</b>
1. Go to your Agent Profile in Ingress Prime
2. Select "ALL TIME" stats view
3. Copy the entire stats text (starts with "Time Span")
4. Paste it directly in this chat
5. The bot will automatically parse and save your stats

🏆 <b>Leaderboard Categories:</b>
• <b>AP (Access Points)</b> - Overall progress ranking
• <b>Explorer</b> - Unique Portals Visited
• <b>Builder</b> - Resonators Deployed
• <b>Connector</b> - Links Created
• <b>Mind Controller</b> - Control Fields Created
• <b>Recharger</b> - XM Recharged
• <b>Trekker</b> - Distance Walked
• <b>Hacker</b> - Total Hacks
• And 20+ more categories!

💬 <b>Bot Commands:</b>
• <code>/start</code> - Show welcome message
• <code>/help</code> - Show this help text
• <code>/leaderboard</code> - Browse leaderboard categories
• <code>/mystats</code> - View your personal stats
• <code>/submit</code> - Get stats submission help

📱 <b>Pro Tips:</b>
• Submit your stats regularly for accurate leaderboards
• Use ALL TIME stats (not monthly/weekly)
• Check your progress with /mystats
• Join your faction leaderboard for friendly competition

⚠️ <b>Common Issues:</b>
• Make sure you're copying ALL TIME stats
• Ensure the text starts with "Time Span"
• Check that your agent name is correct
• Verify your faction (Enlightened/Resistance)

<b>Questions or Issues?</b>
If you encounter any problems, try submitting your stats again or contact the bot admin.
        """

        try:
            await update.message.reply_text(
                help_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"Help command from user {update.effective_user.id}")
        except TelegramError as e:
            logger.error(f"Error sending help message: {e}")
            await update.message.reply_text(
                "Use /start to get started and /leaderboard to view stats."
            )

    async def mystats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /mystats command - Show user's personal stats and history.
        """
        user = update.effective_user
        session = context.bot_data.get('session')

        if not session:
            await update.message.reply_text(
                "⚠️ Database error. Please try again later."
            )
            return

        try:
            # Get agent associated with this user
            agent = get_agent_by_telegram_id(session, user.id)

            if not agent:
                await update.message.reply_text(
                    "🔍 You haven't submitted any stats yet.\n\n"
                    "To get started, paste your ALL TIME stats from Ingress Prime!"
                )
                return

            # Get latest submission
            latest_submission = get_latest_submission_for_agent(session, agent.id)

            if not latest_submission:
                await update.message.reply_text(
                    f"🤖 Agent <b>{agent.agent_name}</b> ({agent.faction}) found, "
                    f"but no stats submissions yet.\n\n"
                    f"Submit your ALL TIME stats to get started!"
                )
                return

            # Get some key stats for display
            lifetime_ap = latest_submission.lifetime_ap or 0
            level = latest_submission.level or 1
            submission_date = latest_submission.submission_date

            # Get recent submissions count
            recent_submissions = session.query(StatsSubmission).filter(
                StatsSubmission.agent_id == agent.id,
                StatsSubmission.submission_date >= datetime.now().date() - timedelta(days=30)
            ).count()

            # Format the response
            stats_text = f"""
👤 <b>Your Agent Stats</b>

🏷️ <b>Agent:</b> {agent.agent_name}
🌐 <b>Faction:</b> {'💚 Enlightened' if agent.faction == 'Enlightened' else '💙 Resistance'}
⭐ <b>Level:</b> {level}
💫 <b>Lifetime AP:</b> {lifetime_ap:,}

📅 <b>Last Submission:</b> {submission_date.strftime('%Y-%m-%d') if submission_date else 'Unknown'}
📈 <b>Recent Submissions:</b> {recent_submissions} (30 days)

💡 <b>Quick Actions:</b>
• Submit new stats: Just paste them here
• View leaderboards: /leaderboard
• Get help: /help

Keep your stats up to date to improve your leaderboard rankings!
            """

            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"MyStats command from user {user.id} for agent {agent.agent_name}")

        except Exception as e:
            logger.error(f"Error in mystats command for user {user.id}: {e}")
            await update.message.reply_text(
                "⚠️ Error retrieving your stats. Please try again later."
            )

    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /leaderboard command - Show leaderboard category selection.
        """
        # Create inline keyboard for popular leaderboard categories
        keyboard = [
            [
                InlineKeyboardButton("🏆 Lifetime AP", callback_data='lb_6'),
                InlineKeyboardButton("🔍 Unique Portals", callback_data='lb_8')
            ],
            [
                InlineKeyboardButton("🔗 Links Created", callback_data='lb_15'),
                InlineKeyboardButton("🧠 Control Fields", callback_data='lb_16')
            ],
            [
                InlineKeyboardButton("⚡ XM Recharged", callback_data='lb_20'),
                InlineKeyboardButton("🔨 Resonators", callback_data='lb_14')
            ],
            [
                InlineKeyboardButton("👟 Distance Walked", callback_data='lb_13'),
                InlineKeyboardButton("💬 Hacks", callback_data='lb_28')
            ],
            [
                InlineKeyboardButton("💚 Enlightened", callback_data='faction_enl'),
                InlineKeyboardButton("💙 Resistance", callback_data='faction_res'),
                InlineKeyboardButton("🌐 All Factions", callback_data='faction_all')
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        leaderboard_text = """
📊 <b>Ingress Prime Leaderboard</b>

Select a category to view the leaderboard:

�� <b>Popular Categories:</b>
• Lifetime AP - Overall progress
• Unique Portals - Explorer badge
• Links Created - Connector badge
• Control Fields - Mind Controller badge
• XM Recharged - Recharger badge
• Resonators - Builder badge
• Distance Walked - Trekker badge
• Hacks - Hacker badge

🌐 <b>Faction Filter:</b>
• View your faction only or all agents
• Compare within your faction for local competition
        """

        try:
            await update.message.reply_text(
                leaderboard_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Leaderboard command from user {update.effective_user.id}")
        except TelegramError as e:
            logger.error(f"Error sending leaderboard menu: {e}")
            await update.message.reply_text("Use /help for available commands.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle regular text messages - likely stats submissions.
        """
        text = update.message.text

        # Check if this looks like stats
        if not (text.startswith('Time Span') and '\n' in text):
            await update.message.reply_text(
                "This doesn't look like Ingress stats. 🤔\n\n"
                "Please copy your ALL TIME stats from Ingress Prime and paste them here.\n\n"
                "Use /help if you need instructions!"
            )
            return

        # Send processing message
        processing_msg = await update.message.reply_text("⏳ Processing your stats...")

        try:
            # Parse the stats
            parsed_data = self.parser.parse(text)

            # Check for parsing errors
            if 'error' in parsed_data:
                error_msg = self._get_parsing_error_message(parsed_data)
                await processing_msg.edit_text(f"❌ {error_msg}")
                return

            # Validate the parsed data
            is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

            if not is_valid:
                error_text = self._format_validation_errors(warnings)
                await processing_msg.edit_text(f"❌ Invalid stats:\n\n{error_text}")
                return

            # Save to database using new StatsDatabase class
            save_result = await self._save_stats_to_database(
                update.effective_user,
                parsed_data,
                context
            )

            if save_result.get('error'):
                await processing_msg.edit_text(f"⚠️ Database error: {save_result['error']}")
                return

            # Get summary information
            summary = self.parser.get_stat_summary(parsed_data)
            faction_emoji = '💚' if summary['faction'] == 'Enlightened' else '💙'

            # Format success message
            success_text = f"""
✅ <b>Stats Submitted Successfully!</b>

🏷️ <b>Agent:</b> {summary['agent_name']}
{faction_emoji} <b>Faction:</b> {summary['faction']}
⭐ <b>Level:</b> {summary['level']}
💫 <b>Lifetime AP:</b> {summary['lifetime_ap']:,}

📊 <b>Stats Processed:</b> {summary['valid_numeric_stats']} valid stats
            """

            # Add warnings if any
            if summary['warnings']:
                warning_text = "\n⚠️ <b>Warnings:</b>\n"
                for warning in summary['warnings'][:3]:  # Show first 3 warnings
                    warning_text += f"• {warning.get('message', 'Unknown warning')}\n"
                success_text += warning_text

            success_text += f"\n💡 Check your progress with <b>/mystats</b>"
            success_text += f"\n🏆 View leaderboards with <b>/leaderboard</b>"

            await processing_msg.edit_text(
                success_text,
                parse_mode=ParseMode.HTML
            )

            logger.info(
                f"Stats submitted by user {update.effective_user.id} "
                f"for agent {summary['agent_name']}"
            )

        except Exception as e:
            logger.error(f"Error processing stats from user {update.effective_user.id}: {e}")
            await processing_msg.edit_text(
                "❌ An error occurred while processing your stats. Please try again."
            )

    async def handle_leaderboard_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle leaderboard category selection callbacks.
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        db_connection = context.bot_data.get('db_connection')

        if not db_connection:
            await query.edit_message_text("⚠️ Database error. Please try again later.")
            return

        try:
            if callback_data.startswith('lb_'):
                # Individual stat leaderboard
                stat_type = callback_data.replace('lb_', '')

                # Try to parse as integer first, then use STAT_MAPPING
                try:
                    stat_idx = int(stat_type)
                except ValueError:
                    # Use STAT_MAPPING for descriptive names
                    stat_idx = self.STAT_MAPPING.get(stat_type.lower())
                    if stat_idx is None:
                        logger.warning(f"Unknown stat type in callback: {callback_data}")
                        await query.edit_message_text("❌ Invalid stat category.")
                        return

                await self._show_stat_leaderboard(query, stat_idx, db_connection)

            elif callback_data.startswith('faction_'):
                # Faction-based leaderboards
                faction = callback_data.replace('faction_', '')
                if faction == 'enl':
                    faction = 'Enlightened'
                elif faction == 'res':
                    faction = 'Resistance'
                else:
                    faction = None

                # Show main leaderboard menu filtered by faction
                await query.edit_message_text(
                    f"🌐 <b>{faction or 'All'} Faction Leaderboards</b>\n\n"
                    f"Select a category:",
                    reply_markup=self._get_leaderboard_keyboard(faction),
                    parse_mode=ParseMode.HTML
                )

        except Exception as e:
            logger.error(f"Error handling leaderboard callback {callback_data}: {e}")
            await query.edit_message_text(
                "⚠️ Error loading leaderboard. Please try again."
            )

    async def _save_stats_to_database(self, user, parsed_data: Dict, context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """
        Save parsed stats to database.

        This is the core function that connects parsed stats to the database.
        """
        from ..database.models import User, Agent, StatsSubmission, AgentStat, FactionChange, ProgressSnapshot
        from ..database.connection import DatabaseConnection
        from datetime import datetime, date, time
        from sqlalchemy.exc import SQLAlchemyError

        # Get database connection and create session
        db_connection = context.bot_data.get('db_connection')
        if not db_connection:
            return {'error': 'Database not available'}

        session = db_connection.get_session()
        if not session:
            return {'error': 'Could not create database session'}

        try:
            # Extract required fields from parsed data
            agent_name = parsed_data.get(1, {}).get('value', '').strip()
            faction = parsed_data.get(2, {}).get('value', '').strip()
            date_str = parsed_data.get(3, {}).get('value', '').strip()
            time_str = parsed_data.get(4, {}).get('value', '').strip()
            level_str = parsed_data.get(5, {}).get('value', '0').replace(',', '')
            lifetime_ap_str = parsed_data.get(6, {}).get('value', '0').replace(',', '')
            current_ap_str = parsed_data.get(7, {}).get('value', '0').replace(',', '')
            xm_collected_str = parsed_data.get(11, {}).get('value', '0').replace(',', '')

            # Validate required fields
            if not agent_name:
                return {'error': 'Agent name is required'}
            if not faction:
                return {'error': 'Faction is required'}
            if not date_str or not time_str:
                return {'error': 'Date and time are required'}

            # Parse and validate data
            try:
                level = int(level_str) if level_str else None
                lifetime_ap = int(lifetime_ap_str) if lifetime_ap_str else None
                current_ap = int(current_ap_str) if current_ap_str else None
                xm_collected = int(xm_collected_str) if xm_collected_str else None

                submission_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                submission_time = time.fromisoformat(time_str)

            except ValueError as e:
                return {'error': f'Invalid data format: {e}'}

            # Get or create User
            telegram_user = user
            user_obj = session.query(User).filter(User.telegram_id == telegram_user.id).first()

            if not user_obj:
                user_obj = User(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name
                )
                session.add(user_obj)
                session.flush()  # Get the ID without committing

            # Get or create Agent
            agent_obj = session.query(Agent).filter(
                Agent.agent_name == agent_name
            ).first()

            is_new_agent = agent_obj is None
            old_faction = None

            if not agent_obj:
                agent_obj = Agent(
                    user_id=user_obj.id,
                    agent_name=agent_name,
                    faction=faction,
                    level=level
                )
                session.add(agent_obj)
                session.flush()
            else:
                # Check for faction change
                old_faction = agent_obj.faction
                if old_faction != faction:
                    # Record faction change
                    faction_change = FactionChange(
                        agent_id=agent_obj.id,
                        old_faction=old_faction,
                        new_faction=faction,
                        reason='user_submission'
                    )
                    session.add(faction_change)

                    # Update agent faction
                    agent_obj.faction = faction

                # Update agent level if provided
                if level is not None:
                    agent_obj.level = level

                agent_obj.updated_at = datetime.utcnow()

            # Check for duplicate submission
            existing_submission = session.query(StatsSubmission).filter(
                StatsSubmission.agent_id == agent_obj.id,
                StatsSubmission.submission_date == submission_date,
                StatsSubmission.stats_type == 'ALL TIME'
            ).first()

            if existing_submission:
                return {
                    'error': f'Stats already submitted for {agent_name} on {submission_date}',
                    'existing': True
                }

            # Create main stats submission
            stats_submission = StatsSubmission(
                agent_id=agent_obj.id,
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
            session.flush()  # Get the submission ID

            # Create individual stat records
            stats_count = 0
            for stat_idx, stat_data in parsed_data.items():
                if isinstance(stat_idx, int) and stat_idx > 0:  # Skip index 0 and non-int keys
                    stat_name = stat_data.get('name', '')
                    stat_value_str = stat_data.get('value', '0')
                    stat_type = stat_data.get('type', 'N')
                    original_pos = stat_data.get('original_pos', 0)

                    # Parse numeric values
                    stat_value = 0
                    if stat_type == 'N':
                        try:
                            stat_value = int(stat_value_str.replace(',', ''))
                        except ValueError:
                            logger.warning(f"Invalid numeric value for {stat_name}: {stat_value_str}")
                            continue

                    agent_stat = AgentStat(
                        submission_id=stats_submission.id,
                        stat_idx=stat_idx,
                        stat_name=stat_name,
                        stat_value=stat_value,
                        stat_type=stat_type,
                        original_position=original_pos
                    )
                    session.add(agent_stat)
                    stats_count += 1

            # Create progress snapshot for monthly tracking
            # This helps with monthly leaderboards
            for stat_idx in [6, 8, 11, 13, 14, 15, 16, 17]:  # Key stats to track
                if stat_idx in parsed_data:
                    stat_data = parsed_data[stat_idx]
                    try:
                        stat_value = int(stat_data.get('value', '0').replace(',', ''))

                        progress_snapshot = ProgressSnapshot(
                            agent_id=agent_obj.id,
                            snapshot_date=submission_date,
                            stat_idx=stat_idx,
                            stat_value=stat_value
                        )
                        session.add(progress_snapshot)
                    except (ValueError, TypeError):
                        continue  # Skip invalid values

            # Commit everything
            session.commit()

            # Update cache if needed (this would integrate with leaderboard generator)
            self._invalidate_leaderboard_cache(context, agent_obj.faction)

            logger.info(
                f"Successfully saved stats for {agent_name} ({agent_obj.id}) "
                f"- {stats_count} stats, faction: {faction}"
            )

            return {
                'success': True,
                'submission_id': stats_submission.id,
                'agent_name': agent_name,
                'faction': faction,
                'stats_count': stats_count,
                'is_new_agent': is_new_agent,
                'faction_changed': old_faction != faction and old_faction is not None
            }

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving stats: {e}")
            return {'error': f'Database error: {str(e)}'}

        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error saving stats: {e}")
            return {'error': f'Save error: {str(e)}'}

        finally:
            session.close()

    def _invalidate_leaderboard_cache(self, context: ContextTypes.DEFAULT_TYPE, faction: str) -> None:
        """
        Invalidate leaderboard cache for a faction when new stats are submitted.

        This ensures leaderboards stay up-to-date with fresh data.

        Args:
            context: Bot application context
            faction: Faction that submitted new stats
        """
        try:
            db_connection = context.bot_data.get('db_connection')
            if not db_connection:
                return

            with db_connection.session_scope() as session:
                # Delete expired cache entries
                from datetime import datetime, timedelta
                from ..database.models import LeaderboardCache

                cutoff_time = datetime.utcnow() - timedelta(hours=1)

                session.query(LeaderboardCache).filter(
                    LeaderboardCache.expires_at < cutoff_time
                ).delete()

                session.commit()

                logger.info(f"Invalidated leaderboard cache for {faction}")

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    async def _show_stat_leaderboard(self, query, stat_idx: int, db_connection) -> None:
        """
        Display leaderboard for a specific stat.
        """
        from ..leaderboard.formatters import LeaderboardFormatter

        stat_def = get_stat_by_idx(stat_idx)
        if not stat_def:
            await query.edit_message_text("⚠️ Invalid stat category.")
            return

        try:
            # Use database connection to get session and leaderboard data
            with db_connection.session_scope() as session:
                leaderboard_data = get_leaderboard_for_stat(session, stat_idx, limit=15)

                if not leaderboard_data:
                    await query.edit_message_text(
                        f"📊 No data available for <b>{stat_def['name']}</b> yet."
                    )
                    return

            # Use LeaderboardFormatter for consistent display
            formatter = LeaderboardFormatter()

            # Create leaderboard data structure that formatter expects
            formatted_data = {
                'stat_name': stat_def['name'],
                'stat_idx': stat_idx,
                'period_type': 'all_time',
                'entries': leaderboard_data,
                'total_entries': len(leaderboard_data),
                'count': len(leaderboard_data),
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'from_cache': False
            }

            # Format the leaderboard
            text = formatter.format_leaderboard(formatted_data, f"{stat_def['name']} (All Time)")

            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"Error showing leaderboard for stat {stat_idx}: {e}")
            await query.edit_message_text(
                "⚠️ Error loading leaderboard. Please try again."
            )

    def _get_parsing_error_message(self, error_data: Dict) -> str:
        """Get user-friendly error message for parsing errors."""
        error_code = error_data.get('error_code', 0)
        error_message = error_data.get('error', 'Unknown error')

        error_messages = {
            1: "This doesn't look like valid Ingress stats. Make sure you're copying the full stats text starting with 'Time Span'.",
            3: "Invalid tabulated format. Please check that you've copied the complete stats.",
            4: "Only ALL TIME stats are accepted. Please make sure you're selecting 'ALL TIME' in Ingress Prime.",
            5: "Not enough values in the stats line. Please check that you've copied the complete stats.",
            6: "Could not find a valid date in your stats. Please check the format.",
            7: "Not enough stats found. Please copy all stats from Ingress Prime.",
            8: "Missing required fields. Please check your stats submission.",
            9: "Invalid faction. Please ensure your faction is 'Enlightened' or 'Resistance'.",
            10: "Invalid numeric values found. Please check your stats for any formatting issues.",
            99: f"Technical error: {error_message}"
        }

        return error_messages.get(error_code, error_message)

    def _format_validation_errors(self, warnings: List[Dict]) -> str:
        """Format validation errors for display."""
        error_texts = []

        for warning in warnings:
            if warning.get('severity') == 'error':
                error_texts.append(f"• {warning.get('message', 'Unknown error')}")

        if not error_texts:
            return "Invalid stats data detected."

        return "\n".join(error_texts[:5])  # Show first 5 errors

    def _get_leaderboard_keyboard(self, faction: Optional[str] = None) -> InlineKeyboardMarkup:
        """Get leaderboard selection keyboard with optional faction filter."""
        keyboard = [
            [
                InlineKeyboardButton("🏆 Lifetime AP", callback_data=f'lb_6_f{faction}' if faction else 'lb_6'),
                InlineKeyboardButton("🔍 Unique Portals", callback_data=f'lb_8_f{faction}' if faction else 'lb_8')
            ],
            [
                InlineKeyboardButton("🔗 Links Created", callback_data=f'lb_15_f{faction}' if faction else 'lb_15'),
                InlineKeyboardButton("🧠 Control Fields", callback_data=f'lb_16_f{faction}' if faction else 'lb_16')
            ],
            [
                InlineKeyboardButton("⚡ XM Recharged", callback_data=f'lb_20_f{faction}' if faction else 'lb_20'),
                InlineKeyboardButton("🔨 Resonators", callback_data=f'lb_14_f{faction}' if faction else 'lb_14')
            ]
        ]

        # Add back button if faction filtered
        if faction:
            keyboard.append([InlineKeyboardButton("« All Factions", callback_data='faction_all')])

        return InlineKeyboardMarkup(keyboard)


def register_handlers(application) -> None:
    """Register all handlers with the application."""
    # Get database connection from application data
    db_connection = application.bot_data.get('db_connection')

    # Initialize handlers with database connection
    handlers = BotHandlers(db_connection)

    # Command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("mystats", handlers.mystats_command))
    application.add_handler(CommandHandler("leaderboard", handlers.leaderboard_command))

    # Message handler for stats submission
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    # Enhanced callback query handlers with STAT_MAPPING support
    # The existing handler now supports both numeric and descriptive callback data
    application.add_handler(CallbackQueryHandler(
        handlers.handle_leaderboard_callback,
        pattern='^(lb_|faction_)'
    ))

    logger.info("Bot handlers registered successfully with enhanced STAT_MAPPING support")


async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /submit command - provide stats submission help."""
    submit_text = """
📊 <b>Stats Submission Help</b>

To submit your Ingress Prime stats:

1. Open Ingress Prime on your device
2. Go to your Agent Profile
3. Tap on "ALL TIME" stats
4. Copy the entire stats text (starts with "Time Span")
5. Paste it directly in this chat

<b>Requirements:</b>
• Only ALL TIME stats are accepted
• Text must start with "Time Span"
• Include all stats lines
• Agent name must match exactly

<b>Pro Tips:</b>
• Submit regularly for accurate leaderboards
• Check your progress with /mystats
• View leaderboards with /leaderboard

Ready? Just paste your stats here!
    """

    await update.message.reply_text(
        submit_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


def register_simple_handlers(application) -> None:
    """
    Register handlers for the simplified framework interface.

    This function provides the simplified handler registration that matches
    the user's requested framework structure while using the existing
    robust BotHandlers implementation.
    """
    handlers = BotHandlers()

    # Command handlers matching the simplified framework structure
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("submit", submit_command))
    application.add_handler(CommandHandler("leaderboard", handlers.leaderboard_command))
    application.add_handler(CommandHandler("mystats", handlers.mystats_command))

    # Handle text messages (for stats submission)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    # Callback query handlers for interactive leaderboards
    application.add_handler(CallbackQueryHandler(handlers.handle_leaderboard_callback, pattern='^(lb_|faction_)'))

    logger.info("Simple framework handlers registered successfully")