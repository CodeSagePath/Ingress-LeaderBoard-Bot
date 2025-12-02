"""
Telegram bot handlers for Ingress Prime leaderboard bot.

This module contains all command and message handlers for the bot.
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError

from ..parsers.stats_parser import StatsParser
from ..parsers.validator import StatsValidator
from ..database.models import (
    User, Agent, StatsSubmission, AgentStat, get_agent_by_telegram_id,
    get_latest_submission_for_agent, get_leaderboard_for_stat
)
from ..config.stats_config import get_stat_by_idx, format_stat_value, get_leaderboard_stats


logger = logging.getLogger(__name__)


class BotHandlers:
    """Main handler class for all bot commands and messages."""

    def __init__(self):
        self.parser = StatsParser()
        self.validator = StatsValidator()

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

            # Save to database (would need session implementation)
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
        session = context.bot_data.get('session')

        if not session:
            await query.edit_message_text("⚠️ Database error. Please try again later.")
            return

        try:
            if callback_data.startswith('lb_'):
                # Individual stat leaderboard
                stat_idx = int(callback_data.replace('lb_', ''))
                await self._show_stat_leaderboard(query, stat_idx, session)

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
        """
        # This is a placeholder - actual database operations would be implemented
        # based on the SQLAlchemy models created earlier
        return {'success': True, 'submission_id': 1}

    async def _show_stat_leaderboard(self, query, stat_idx: int, session) -> None:
        """
        Display leaderboard for a specific stat.
        """
        stat_def = get_stat_by_idx(stat_idx)
        if not stat_def:
            await query.edit_message_text("⚠️ Invalid stat category.")
            return

        try:
            # Get leaderboard data
            leaderboard_data = get_leaderboard_for_stat(session, stat_idx, limit=15)

            if not leaderboard_data:
                await query.edit_message_text(
                    f"📊 No data available for <b>{stat_def['name']}</b> yet."
                )
                return

            # Format leaderboard
            text = f"🏆 <b>{stat_def['name']} Leaderboard</b>\n"
            text += f"{'═' * 45}\n\n"

            for entry in leaderboard_data:
                rank = entry['rank']
                agent = entry['agent_name']
                faction = entry['faction']
                value = entry['value']
                date = entry['date']

                # Medals for top 3
                if rank == 1:
                    medal = "🥇"
                elif rank == 2:
                    medal = "🥈"
                elif rank == 3:
                    medal = "🥉"
                else:
                    medal = f"{rank}."

                faction_emoji = '💚' if faction == 'Enlightened' else '💙'
                formatted_value = format_stat_value(stat_idx, value)

                text += f"{medal} {faction_emoji} <b>{agent}</b>\n"
                text += f"    {formatted_value}\n\n"

            text += f"<i>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"

            # Add back button
            keyboard = [[InlineKeyboardButton("« Back", callback_data='back_to_lb_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"Error generating leaderboard for stat {stat_idx}: {e}")
            await query.edit_message_text(
                "⚠️ Error generating leaderboard. Please try again."
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
    handlers = BotHandlers()

    # Command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("mystats", handlers.mystats_command))
    application.add_handler(CommandHandler("leaderboard", handlers.leaderboard_command))

    # Message handler for stats submission
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handlers.handle_leaderboard_callback, pattern='^(lb_|faction_)'))

    logger.info("Bot handlers registered successfully")