"""
Telegram bot callback handlers for Ingress Prime leaderboard bot.

This module contains all callback query handlers for interactive bot features.
"""

import logging
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..leaderboard.generator import LeaderboardGenerator
from ..leaderboard.formatters import LeaderboardFormatter
from ..config.stats_config import get_stat_by_idx, format_stat_value

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """Handles all bot callback queries for interactive features."""

    def __init__(self):
        """Initialize callback handlers."""
        # Initialize LeaderboardGenerator with session (will be set at runtime)
        self.lb_generator = None
        self.lb_formatter = LeaderboardFormatter()

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

    async def handle_leaderboard_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle leaderboard selection callbacks.
        
        This is the main callback handler that processes user interactions
        with leaderboard buttons and generates appropriate responses.
        
        Args:
            update: Telegram update containing the callback query
            context: Bot context containing database session and other data
        """
        query = update.callback_query
        await query.answer()
        
        # Extract the callback data to determine what action to take
        callback_data = query.data
        logger.debug(f"Processing callback: {callback_data}")

        try:
            if callback_data.startswith('lb_'):
                # Handle individual stat leaderboard requests
                await self._handle_stat_leaderboard(query, callback_data, context)

            elif callback_data.startswith('faction_'):
                # Handle faction filtering requests
                await self._handle_faction_filter(query, callback_data, context)

            elif callback_data.startswith('period_'):
                # Handle time period selection for leaderboards
                await self._handle_period_selection(query, callback_data, context)

            elif callback_data == 'back_to_main':
                # Handle navigation back to main leaderboard menu
                await self._handle_back_to_main(query, context)

            else:
                # Handle unknown callback data
                logger.warning(f"Unknown callback data received: {callback_data}")
                await query.edit_message_text(
                    "❌ Invalid selection. Please try again with /leaderboard"
                )

        except Exception as e:
            logger.error(f"Error processing callback {callback_data}: {e}")
            await query.edit_message_text(
                "⚠️ An error occurred while processing your request. Please try again."
            )

    async def _handle_stat_leaderboard(self, query, callback_data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle individual stat leaderboard requests.
        
        This method generates and displays leaderboards for specific stats
        based on the callback data received from user interactions.
        
        Args:
            query: Telegram callback query object
            callback_data: The callback data string (e.g., 'lb_6', 'lb_8')
            context: Bot context containing database session
        """
        # Extract stat type from callback data (e.g., 'lb_6' -> '6')
        stat_type = callback_data.replace('lb_', '')

        # Convert to integer stat index, handling potential errors
        try:
            stat_idx = int(stat_type)
        except ValueError:
            # Try to map from descriptive names if available
            stat_idx = self.STAT_MAPPING.get(stat_type.lower())
            if stat_idx is None:
                logger.error(f"Invalid stat type in callback: {callback_data}")
                await query.edit_message_text("❌ Invalid stat category selected.")
                return

        # Validate that this stat is supported for leaderboards
        stat_def = get_stat_by_idx(stat_idx)
        if not stat_def:
            logger.error(f"Stat definition not found for index: {stat_idx}")
            await query.edit_message_text("❌ This stat is not available for leaderboards.")
            return

        # Get database session from context
        db_connection = context.bot_data.get('db_connection')
        if not db_connection:
            logger.error("No database connection available in bot context")
            await query.edit_message_text("⚠️ Database error. Please try again later.")
            return

        try:
            # Initialize leaderboard generator with session if needed
            if not self.lb_generator:
                self.lb_generator = LeaderboardGenerator(db_connection.get_session())

            # Generate the leaderboard using the configured generator
            leaderboard = self.lb_generator.generate(
                stat_idx=stat_idx,
                limit=20,  # Show top 20 entries
                use_cache=True  # Use cached results for performance
            )

            if 'error' in leaderboard:
                logger.error(f"Error generating leaderboard for stat {stat_idx}: {leaderboard['error']}")
                await query.edit_message_text(
                    f"⚠️ Error generating leaderboard: {leaderboard['error']}"
                )
                return

            # Format the leaderboard for display using the formatter
            formatted_text = self.lb_formatter.format_leaderboard(
                leaderboard_data=leaderboard,
                category=stat_def['name']
            )

            # Add navigation buttons to the response
            reply_markup = self._create_leaderboard_navigation_markup(stat_idx)

            await query.edit_message_text(
                formatted_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

            logger.info(f"Successfully displayed leaderboard for stat {stat_idx} ({stat_def['name']})")

        except Exception as e:
            logger.error(f"Error displaying leaderboard for stat {stat_idx}: {e}")
            await query.edit_message_text(
                "⚠️ Error loading leaderboard. Please try again later."
            )

    async def _handle_faction_filter(self, query, callback_data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle faction filtering requests for leaderboards.

        This method processes user requests to filter leaderboards
        by faction (Enlightened, Resistance, or all factions).

        Args:
            query: Telegram callback query object
            callback_data: The callback data string (e.g., 'faction_enl', 'faction_res')
            context: Bot context containing database session
        """
        # Extract faction type from callback data
        faction_type = callback_data.replace('faction_', '')

        # Map faction codes to full names
        faction_mapping = {
            'enl': 'Enlightened',
            'res': 'Resistance',
            'all': None
        }

        faction = faction_mapping.get(faction_type.lower())
        faction_display = faction or 'All Factions'

        # Create filtered leaderboard menu
        keyboard = self._create_faction_filtered_keyboard(faction_type.lower())
        reply_markup = InlineKeyboardMarkup(keyboard)

        faction_emoji = '💚' if faction == 'Enlightened' else '💙' if faction == 'Resistance' else '🌐'

        menu_text = f"""
{faction_emoji} <b>{faction_display} Leaderboards</b>

Select a category to view the leaderboard:

🏆 <b>Popular Categories:</b>
• Lifetime AP - Overall progression
• Unique Portals - Explorer badge
• Links Created - Connector badge
• Control Fields - Mind Controller badge
• XM Recharged - Recharger badge
• Resonators - Builder badge
• Distance Walked - Trekker badge
• Hacks - Hacker badge

💡 <b>Tip:</b> These leaderboards are filtered to show only {faction_display.lower()} agents.
        """

        await query.edit_message_text(
            menu_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        logger.info(f"Displayed faction-filtered menu for: {faction_display}")

    async def handle_faction_leaderboard_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle faction-specific leaderboard callbacks from the factionleaderboard command.

        This method processes callbacks that include both faction and stat information
        to generate filtered leaderboards.

        Args:
            update: Telegram update containing the callback query
            context: Bot context containing database session
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        logger.debug(f"Processing faction leaderboard callback: {callback_data}")

        try:
            # Parse callback data format: 'lb_{stat_idx}_{faction}'
            if callback_data.startswith('lb_'):
                parts = callback_data.split('_')
                if len(parts) >= 3:
                    stat_idx_str = parts[1]
                    faction_type = parts[2]

                    # Convert stat index to integer
                    try:
                        stat_idx = int(stat_idx_str)
                    except ValueError:
                        # Try to map from descriptive names
                        stat_idx = self.STAT_MAPPING.get(stat_idx_str.lower())
                        if stat_idx is None:
                            await query.edit_message_text("❌ Invalid stat category selected.")
                            return

                    # Map faction type to full name
                    faction_mapping = {
                        'enl': 'Enlightened',
                        'res': 'Resistance',
                        'all': None
                    }
                    faction = faction_mapping.get(faction_type.lower())
                    faction_display = faction or 'All Factions'

                    # Get database session from context
                    db_connection = context.bot_data.get('db_connection')
                    if not db_connection:
                        await query.edit_message_text("⚠️ Database error. Please try again later.")
                        return

                    # Initialize leaderboard generator with session if needed
                    if not self.lb_generator:
                        from ..leaderboard.generator import LeaderboardGenerator
                        self.lb_generator = LeaderboardGenerator(db_connection.get_session())

                    # Generate faction-specific leaderboard
                    leaderboard = self.lb_generator.generate(
                        stat_idx=stat_idx,
                        limit=20,
                        faction=faction,
                        use_cache=True
                    )

                    if 'error' in leaderboard:
                        await query.edit_message_text(
                            f"⚠️ Error generating {faction_display} leaderboard: {leaderboard['error']}"
                        )
                        return

                    # Get stat definition for formatting
                    stat_def = get_stat_by_idx(stat_idx)
                    if not stat_def:
                        await query.edit_message_text("❌ This stat is not available for leaderboards.")
                        return

                    # Format the leaderboard for display
                    formatted_text = self.lb_formatter.format_leaderboard(
                        leaderboard_data=leaderboard,
                        category=f"{stat_def['name']} ({faction_display})"
                    )

                    # Add navigation buttons
                    reply_markup = self._create_faction_leaderboard_navigation(stat_idx, faction_type)

                    await query.edit_message_text(
                        formatted_text,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )

                    logger.info(f"Displayed {faction_display} leaderboard for stat {stat_idx} ({stat_def['name']})")
                else:
                    # Handle regular faction filter without stat
                    await self._handle_faction_filter(query, callback_data, context)
            else:
                # Handle regular faction filter
                await self._handle_faction_filter(query, callback_data, context)

        except Exception as e:
            logger.error(f"Error processing faction leaderboard callback {callback_data}: {e}")
            await query.edit_message_text(
                "⚠️ An error occurred while processing your request. Please try again."
            )

    def _create_faction_leaderboard_navigation(self, stat_idx: int, faction_type: str) -> InlineKeyboardMarkup:
        """
        Create navigation markup for faction leaderboards.

        Args:
            stat_idx: The stat index for the current leaderboard
            faction_type: The faction type ('enl', 'res', 'all')

        Returns:
            InlineKeyboardMarkup with navigation buttons
        """
        faction_emoji = '💚' if faction_type == 'enl' else '💙' if faction_type == 'res' else '🌐'
        faction_suffix = f'_{faction_type}' if faction_type != 'all' else ''

        keyboard = [
            [
                InlineKeyboardButton("📅 All Time", callback_data=f'lb_{stat_idx}{faction_suffix}'),
                InlineKeyboardButton("📊 Monthly", callback_data=f'period_monthly_lb_{stat_idx}{faction_suffix}')
            ],
            [
                InlineKeyboardButton("📈 Weekly", callback_data=f'period_weekly_lb_{stat_idx}{faction_suffix}'),
                InlineKeyboardButton("⏰ Daily", callback_data=f'period_daily_lb_{stat_idx}{faction_suffix}')
            ],
            [
                InlineKeyboardButton(f"{faction_emoji} Back to Faction Menu", callback_data=f'faction_{faction_type}'),
                InlineKeyboardButton("🌐 All Factions", callback_data='faction_all')
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    async def _handle_period_selection(self, query, callback_data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle time period selection for leaderboards.
        
        This method processes user requests to view leaderboards
        for different time periods (all-time, monthly, weekly, daily).
        
        Args:
            query: Telegram callback query object
            callback_data: The callback data string (e.g., 'period_monthly_lb_6')
            context: Bot context containing database session
        """
        # Parse the callback data: format 'period_{period}_{type}_{stat}'
        parts = callback_data.split('_')
        if len(parts) < 4:
            logger.error(f"Invalid period callback format: {callback_data}")
            await query.edit_message_text("❌ Invalid time period selection.")
            return
        
        period = parts[1]  # monthly, weekly, daily
        stat_type = parts[3]  # the stat index or name
        
        # Convert stat type to index
        try:
            stat_idx = int(stat_type)
        except ValueError:
            stat_idx = self.STAT_MAPPING.get(stat_type.lower())
            if stat_idx is None:
                await query.edit_message_text("❌ Invalid stat category.")
                return
        
        # Get database session
        session = context.bot_data.get('session')
        if not session:
            await query.edit_message_text("⚠️ Database error. Please try again later.")
            return
        
        try:
            # Generate leaderboard for the specific period
            leaderboard = self.lb_generator.generate(
                stat_idx=stat_idx,
                period=period,
                limit=20,
                use_cache=True
            )
            
            if 'error' in leaderboard:
                await query.edit_message_text(
                    f"⚠️ Error generating {period} leaderboard: {leaderboard['error']}"
                )
                return
            
            # Format and display the leaderboard
            stat_def = get_stat_by_idx(stat_idx)
            category_name = f"{stat_def['name']} ({period.title()})"
            
            formatted_text = self.lb_formatter.format_leaderboard(
                leaderboard_data=leaderboard,
                category=category_name
            )
            
            reply_markup = self._create_period_navigation_markup(stat_idx, period)
            
            await query.edit_message_text(
                formatted_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            logger.info(f"Displayed {period} leaderboard for stat {stat_idx}")
            
        except Exception as e:
            logger.error(f"Error generating {period} leaderboard: {e}")
            await query.edit_message_text(
                "⚠️ Error loading leaderboard. Please try again later."
            )

    async def _handle_back_to_main(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle navigation back to the main leaderboard menu.
        
        This method displays the main leaderboard selection menu
        when users navigate back from other screens.
        
        Args:
            query: Telegram callback query object
            context: Bot context
        """
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
        
        main_menu_text = """
📊 <b>Ingress Prime Leaderboard</b>

Select a category to view the leaderboard:

🏆 <b>Popular Categories:</b>
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
        
        await query.edit_message_text(
            main_menu_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        logger.info("User navigated back to main leaderboard menu")

    def _create_leaderboard_navigation_markup(self, stat_idx: int) -> InlineKeyboardMarkup:
        """
        Create navigation markup for leaderboard screens.
        
        Args:
            stat_idx: The stat index for the current leaderboard
            
        Returns:
            InlineKeyboardMarkup with navigation buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("📅 All Time", callback_data=f'period_all_time_stat_{stat_idx}'),
                InlineKeyboardButton("📊 Monthly", callback_data=f'period_monthly_stat_{stat_idx}')
            ],
            [
                InlineKeyboardButton("📈 Weekly", callback_data=f'period_weekly_stat_{stat_idx}'),
                InlineKeyboardButton("⏰ Daily", callback_data=f'period_daily_stat_{stat_idx}')
            ],
            [
                InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_main')
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

    def _create_faction_filtered_keyboard(self, faction: str) -> InlineKeyboardMarkup:
        """
        Create keyboard for faction-filtered leaderboards.
        
        Args:
            faction: The faction filter ('enl', 'res', 'all')
            
        Returns:
            InlineKeyboardMarkup with faction-filtered stat buttons
        """
        faction_suffix = f'_{faction}' if faction != 'all' else ''
        
        keyboard = [
            [
                InlineKeyboardButton("🏆 Lifetime AP", callback_data=f'lb_6{faction_suffix}'),
                InlineKeyboardButton("🔍 Unique Portals", callback_data=f'lb_8{faction_suffix}')
            ],
            [
                InlineKeyboardButton("🔗 Links Created", callback_data=f'lb_15{faction_suffix}'),
                InlineKeyboardButton("🧠 Control Fields", callback_data=f'lb_16{faction_suffix}')
            ],
            [
                InlineKeyboardButton("⚡ XM Recharged", callback_data=f'lb_20{faction_suffix}'),
                InlineKeyboardButton("🔨 Resonators", callback_data=f'lb_14{faction_suffix}')
            ],
            [
                InlineKeyboardButton("👟 Distance Walked", callback_data=f'lb_13{faction_suffix}'),
                InlineKeyboardButton("💬 Hacks", callback_data=f'lb_28{faction_suffix}')
            ],
            [
                InlineKeyboardButton("« All Factions", callback_data='faction_all')
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

    def _create_period_navigation_markup(self, stat_idx: int, current_period: str) -> InlineKeyboardMarkup:
        """
        Create navigation markup for time period selection.
        
        Args:
            stat_idx: The stat index for the current leaderboard
            current_period: The currently selected period
            
        Returns:
            InlineKeyboardMarkup with period selection buttons
        """
        periods = ['all_time', 'monthly', 'weekly', 'daily']
        keyboard = []
        
        # Create row with all period options
        period_buttons = []
        for period in periods:
            display_name = {
                'all_time': '📅 All Time',
                'monthly': '📊 Monthly',
                'weekly': '📈 Weekly',
                'daily': '⏰ Daily'
            }[period]
            
            # Highlight current period
            if period == current_period:
                display_name = f"• {display_name} •"
            
            period_buttons.append(InlineKeyboardButton(
                display_name,
                callback_data=f'period_{period}_stat_{stat_idx}'
            ))
        
        # Split into rows of 2 buttons each
        for i in range(0, len(period_buttons), 2):
            row = period_buttons[i:i+2]
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_main')])
        
        return InlineKeyboardMarkup(keyboard)


# Create global instance for easy import
callback_handlers = CallbackHandlers()


# Convenience function for importing in main handler registration
def get_callback_handlers() -> CallbackHandlers:
    """
    Get the callback handlers instance.
    
    Returns:
        CallbackHandlers instance for use in bot registration
    """
    return callback_handlers