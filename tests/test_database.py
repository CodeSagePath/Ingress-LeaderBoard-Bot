"""
Comprehensive tests for StatsDatabase class.

This module tests the core database functionality of the Ingress
Prime leaderboard bot, including stats saving, retrieval, and queries.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, date, time
from unittest.mock import Mock, patch

from src.database.stats_database import StatsDatabase
from src.database.connection import DatabaseConnection
from src.database.models import Base, User, Agent, StatsSubmission, AgentStat
from tests.data_generator import TestDataGenerator


class TestStatsDatabase(unittest.TestCase):
    """Test all StatsDatabase functionality with isolated test database."""

    def setUp(self):
        """Set up isolated test database for each test."""
        # Create temporary SQLite database for testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)

        # Create test database connection
        test_db_url = f"sqlite:///{self.db_path}"
        self.db_connection = DatabaseConnection(test_db_url)
        self.db_connection.initialize()

        # Create database tables
        Base.metadata.create_all(self.db_connection.engine)

        # Initialize StatsDatabase with test connection
        self.stats_db = StatsDatabase(self.db_connection)

        # Initialize test data generator
        self.data_gen = TestDataGenerator()

        # Test user information
        self.test_telegram_id = 12345
        self.test_user_info = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en'
        }

    def tearDown(self):
        """Clean up test database after each test."""
        # Close database connection
        if hasattr(self.db_connection, 'engine'):
            self.db_connection.engine.dispose()

        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_save_and_retrieve_stats(self):
        """Test saving and retrieving stats successfully."""
        # Generate valid test data
        parsed_stats = self.data_gen.generate_valid_submission('TestAgent', 'Enlightened')

        # Save stats to database
        result = self.stats_db.save_stats(self.test_telegram_id, parsed_stats, self.test_user_info)

        # Verify save was successful
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['submission_id'])
        self.assertEqual(result['agent_name'], 'TestAgent')
        self.assertEqual(result['faction'], 'Enlightened')
        self.assertEqual(result['user_id'], self.test_telegram_id)
        self.assertTrue(result['is_new_agent'])
        self.assertFalse(result['faction_changed'])

        # Retrieve the saved submission
        with self.db_connection.session_scope() as session:
            submission = session.query(StatsSubmission).filter(
                StatsSubmission.id == result['submission_id']
            ).first()

            # Verify submission data
            self.assertIsNotNone(submission)
            self.assertEqual(submission.agent.agent_name, 'TestAgent')
            self.assertEqual(submission.agent.faction, 'Enlightened')
            self.assertEqual(submission.agent.user.telegram_id, self.test_telegram_id)

            # Verify individual stats were saved
            stats = session.query(AgentStat).filter(
                AgentStat.submission_id == submission.id
            ).all()

            self.assertGreater(len(stats), 5)  # Should have multiple individual stats

            # Check specific stat values
            level_stat = next((s for s in stats if s.stat_idx == 5), None)
            self.assertIsNotNone(level_stat)
            self.assertEqual(level_stat.stat_name, 'Level')
            self.assertEqual(level_stat.stat_value, parsed_stats[5]['value'])

    def test_duplicate_submission_handling(self):
        """Test that duplicate submissions are detected."""
        # Generate valid test data
        parsed_stats = self.data_gen.generate_valid_submission('TestAgent2', 'Resistance')

        # Save first submission
        result1 = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Save identical submission again
        result2 = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # First should succeed, second should be detected as duplicate
        self.assertTrue(result1['success'])
        self.assertFalse(result2['success'])
        self.assertTrue(result2.get('duplicate', False))
        self.assertIn('already submitted', result2['error'])

    def test_faction_change_tracking(self):
        """Test that faction changes are tracked properly."""
        # Create initial submission with Enlightened faction
        parsed_stats1 = self.data_gen.generate_valid_submission('TestAgent3', 'Enlightened')
        result1 = self.stats_db.save_stats(self.test_telegram_id, parsed_stats1)

        # Create second submission with Resistance faction
        parsed_stats2 = self.data_gen.generate_valid_submission('TestAgent3', 'Resistance')
        result2 = self.stats_db.save_stats(self.test_telegram_id, parsed_stats2)

        # First should create agent, second should track faction change
        self.assertTrue(result1['success'])
        self.assertTrue(result2['success'])
        self.assertTrue(result1['is_new_agent'])
        self.assertFalse(result2['is_new_agent'])
        self.assertFalse(result1['faction_changed'])
        self.assertTrue(result2['faction_changed'])

        # Verify faction change was recorded
        with self.db_connection.session_scope() as session:
            from src.database.models import FactionChange
            faction_change = session.query(FactionChange).filter(
                FactionChange.agent_id == result2['agent_id']
            ).first()

            self.assertIsNotNone(faction_change)
            self.assertEqual(faction_change.old_faction, 'Enlightened')
            self.assertEqual(faction_change.new_faction, 'Resistance')

    def test_agent_history_retrieval(self):
        """Test retrieving agent submission history."""
        agent_name = 'TestAgent4'

        # Create multiple submissions for the same agent
        submissions = []
        for i in range(3):
            parsed_stats = self.data_gen.generate_valid_submission(agent_name, 'Resistance')
            # Use different dates to ensure proper ordering
            parsed_stats[3]['value'] = f'2024-01-{i+1:02d}'
            parsed_stats[4]['value'] = f'{10+i}:00:00'

            result = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)
            submissions.append(result)

        # Retrieve agent history
        history = self.stats_db.get_agent_history(agent_name)

        # Should have 3 submissions in reverse chronological order
        self.assertEqual(len(history), 3)

        # Verify ordering (most recent first)
        dates = [entry['submission_date'] for entry in history]
        self.assertEqual(dates, sorted(dates, reverse=True))

        # Verify all submissions belong to the correct agent
        for entry in history:
            self.assertEqual(entry['agent_name'], agent_name)

    def test_agent_history_with_limit(self):
        """Test agent history retrieval with limit parameter."""
        agent_name = 'TestAgent5'

        # Create 5 submissions
        for i in range(5):
            parsed_stats = self.data_gen.generate_valid_submission(agent_name, 'Enlightened')
            parsed_stats[3]['value'] = f'2024-01-{i+1:02d}'
            self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Retrieve history with limit of 3
        history = self.stats_db.get_agent_history(agent_name, limit=3)

        # Should only return 3 most recent submissions
        self.assertEqual(len(history), 3)

    def test_agent_history_nonexistent_agent(self):
        """Test history retrieval for non-existent agent."""
        history = self.stats_db.get_agent_history('NonExistentAgent')
        self.assertEqual(history, [])

    def test_get_agent_latest_stats(self):
        """Test retrieving latest stats for an agent."""
        agent_name = 'TestAgent6'

        # Create multiple submissions
        parsed_stats1 = self.data_gen.generate_valid_submission(agent_name, 'Resistance')
        parsed_stats1[6]['value'] = '1000000'  # Set specific AP

        parsed_stats2 = self.data_gen.generate_valid_submission(agent_name, 'Resistance')
        parsed_stats2[6]['value'] = '2000000'  # Higher AP for latest

        # Save with different dates
        parsed_stats1[3]['value'] = '2024-01-01'
        parsed_stats2[3]['value'] = '2024-01-15'

        self.stats_db.save_stats(self.test_telegram_id, parsed_stats1)
        self.stats_db.save_stats(self.test_telegram_id, parsed_stats2)

        # Get latest stats
        latest = self.stats_db.get_agent_latest_stats(agent_name)

        # Should return the second (latest) submission
        self.assertIsNotNone(latest)
        self.assertEqual(latest['agent_name'], agent_name)
        self.assertEqual(latest['lifetime_ap'], 2000000)  # Latest AP value

        # Should include all individual stats
        self.assertIn('stats', latest)
        self.assertGreater(len(latest['stats']), 5)

    def test_get_agent_latest_stats_nonexistent(self):
        """Test latest stats for non-existent agent."""
        latest = self.stats_db.get_agent_latest_stats('NonExistentAgent')
        self.assertIsNone(latest)

    def test_leaderboard_data_generation(self):
        """Test leaderboard data generation."""
        # Create multiple agents with different AP values
        agents_data = [
            ('AgentA', 'Enlightened', 1000000),
            ('AgentB', 'Resistance', 2000000),
            ('AgentC', 'Enlightened', 1500000),
            ('AgentD', 'Resistance', 3000000),
        ]

        for agent_name, faction, lifetime_ap in agents_data:
            parsed_stats = self.data_gen.generate_valid_submission(agent_name, faction)
            parsed_stats[6]['value'] = str(lifetime_ap)  # Set specific AP
            self.stats_db.save_stats(self.test_telegram_id + len(agent_name), parsed_stats)

        # Get leaderboard for lifetime AP (stat_idx = 6)
        leaderboard = self.stats_db.get_leaderboard_data(6)

        # Should return 4 agents ordered by AP (highest first)
        self.assertEqual(len(leaderboard), 4)

        # Verify ordering (highest AP first)
        ap_values = [entry['stat_value'] for entry in leaderboard]
        self.assertEqual(ap_values, sorted(ap_values, reverse=True))

        # Verify top agent
        self.assertEqual(leaderboard[0]['agent_name'], 'AgentD')
        self.assertEqual(leaderboard[0]['stat_value'], 3000000)

    def test_leaderboard_faction_filtering(self):
        """Test leaderboard data with faction filtering."""
        # Create agents from both factions
        agents_data = [
            ('AgentA', 'Enlightened', 1000000),
            ('AgentB', 'Resistance', 2000000),
            ('AgentC', 'Enlightened', 1500000),
        ]

        for agent_name, faction, lifetime_ap in agents_data:
            parsed_stats = self.data_gen.generate_valid_submission(agent_name, faction)
            parsed_stats[6]['value'] = str(lifetime_ap)
            self.stats_db.save_stats(self.test_telegram_id + len(agent_name), parsed_stats)

        # Get leaderboard for Enlightened only
        enlighted_leaderboard = self.stats_db.get_leaderboard_data(6, faction='Enlightened')

        # Should only return Enlightened agents
        self.assertEqual(len(enlighted_leaderboard), 2)
        for entry in enlighted_leaderboard:
            self.assertEqual(entry['faction'], 'Enlightened')

    def test_get_user_agents(self):
        """Test retrieving all agents for a user."""
        # Create multiple agents for the same user
        agent_names = ['UserAgent1', 'UserAgent2', 'UserAgent3']

        for i, agent_name in enumerate(agent_names):
            parsed_stats = self.data_gen.generate_valid_submission(agent_name, 'Enlightened')
            self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Get user's agents
        user_agents = self.stats_db.get_user_agents(self.test_telegram_id)

        # Should return 3 agents
        self.assertEqual(len(user_agents), 3)

        returned_names = [agent['agent_name'] for agent in user_agents]
        for name in agent_names:
            self.assertIn(name, returned_names)

    def test_get_user_agents_nonexistent_user(self):
        """Test getting agents for non-existent user."""
        user_agents = self.stats_db.get_user_agents(99999)
        self.assertEqual(user_agents, [])

    def test_get_database_stats(self):
        """Test getting overall database statistics."""
        # Create some test data
        for i in range(5):
            parsed_stats = self.data_gen.generate_valid_submission(f'StatsAgent{i}', 'Enlightened')
            # Make some Resistance agents too
            if i % 2 == 0:
                parsed_stats[2]['value'] = 'Resistance'

            self.stats_db.save_stats(self.test_telegram_id + i, parsed_stats)

        # Get database statistics
        db_stats = self.stats_db.get_database_stats()

        # Verify basic statistics
        self.assertGreater(db_stats['users'], 0)
        self.assertGreater(db_stats['agents'], 0)
        self.assertGreater(db_stats['submissions'], 0)
        self.assertGreater(db_stats['individual_stats'], 0)

        # Verify faction breakdown exists
        self.assertIn('factions', db_stats)
        self.assertIn('Enlightened', db_stats['factions'])
        self.assertIn('Resistance', db_stats['factions'])

    def test_level_update_existing_agent(self):
        """Test updating level for existing agent."""
        agent_name = 'LevelUpdateAgent'

        # Create initial submission with level 5
        parsed_stats1 = self.data_gen.generate_valid_submission(agent_name, 'Enlightened')
        parsed_stats1[5]['value'] = '5'
        self.stats_db.save_stats(self.test_telegram_id, parsed_stats1)

        # Create second submission with level 8
        parsed_stats2 = self.data_gen.generate_valid_submission(agent_name, 'Enlightened')
        parsed_stats2[5]['value'] = '8'
        parsed_stats2[3]['value'] = '2024-01-15'  # Different date
        result2 = self.stats_db.save_stats(self.test_telegram_id, parsed_stats2)

        # Verify level was updated
        self.assertTrue(result2['success'])
        self.assertFalse(result2['is_new_agent'])
        self.assertEqual(result2['level'], 8)

        # Check agent's current level
        with self.db_connection.session_scope() as session:
            agent = session.query(Agent).filter(Agent.agent_name == agent_name).first()
            self.assertEqual(agent.level, 8)

    def test_validation_required_fields(self):
        """Test validation of required fields."""
        # Test missing agent name
        invalid_stats = {
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:00:00', 'type': 'S'},
        }

        with self.assertRaises(ValueError) as context:
            self.stats_db.save_stats(self.test_telegram_id, invalid_stats)

        self.assertIn('Missing required field', str(context.exception))

    def test_validation_faction_values(self):
        """Test validation of faction values."""
        # Test invalid faction
        parsed_stats = self.data_gen.generate_valid_submission('TestAgent', 'InvalidFaction')

        with self.assertRaises(ValueError) as context:
            self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        self.assertIn('Invalid faction', str(context.exception))

    def test_validation_insufficient_stats(self):
        """Test validation of minimum stats count."""
        # Test with only header fields (insufficient stats)
        insufficient_stats = {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:00:00', 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '10', 'type': 'N'},
        }

        with self.assertRaises(ValueError) as context:
            self.stats_db.save_stats(self.test_telegram_id, insufficient_stats)

        self.assertIn('Insufficient stats', str(context.exception))

    def test_error_handling_database_connection(self):
        """Test error handling when database connection fails."""
        # Create database connection with invalid URL
        invalid_db = StatsDatabase(DatabaseConnection('sqlite:///invalid/path'))

        parsed_stats = self.data_gen.generate_valid_submission('TestAgent', 'Enlightened')

        # Should handle database errors gracefully
        with self.assertRaises(Exception):
            invalid_db.save_stats(self.test_telegram_id, parsed_stats)

    def test_progress_snapshots_creation(self):
        """Test that progress snapshots are created for key stats."""
        agent_name = 'ProgressAgent'
        parsed_stats = self.data_gen.generate_valid_submission(agent_name, 'Enlightened')

        result = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Verify progress snapshots were created
        with self.db_connection.session_scope() as session:
            from src.database.models import ProgressSnapshot

            snapshots = session.query(ProgressSnapshot).filter(
                ProgressSnapshot.agent_id == result['agent_id']
            ).all()

            # Should have snapshots for key stats (AP, portals visited, etc.)
            self.assertGreater(len(snapshots), 0)

            # Check specific snapshot
            ap_snapshot = next((s for s in snapshots if s.stat_idx == 6), None)
            self.assertIsNotNone(ap_snapshot)
            self.assertEqual(ap_snapshot.stat_idx, 6)

    def test_multi_user_data_isolation(self):
        """Test that data is properly isolated between different users."""
        user1_id = 11111
        user2_id = 22222

        # Create agents for different users
        parsed_stats1 = self.data_gen.generate_valid_submission('User1Agent', 'Enlightened')
        parsed_stats2 = self.data_gen.generate_valid_submission('User2Agent', 'Resistance')

        result1 = self.stats_db.save_stats(user1_id, parsed_stats1)
        result2 = self.stats_db.save_stats(user2_id, parsed_stats2)

        # Verify user 1 only sees their agent
        user1_agents = self.stats_db.get_user_agents(user1_id)
        self.assertEqual(len(user1_agents), 1)
        self.assertEqual(user1_agents[0]['agent_name'], 'User1Agent')

        # Verify user 2 only sees their agent
        user2_agents = self.stats_db.get_user_agents(user2_id)
        self.assertEqual(len(user2_agents), 1)
        self.assertEqual(user2_agents[0]['agent_name'], 'User2Agent')

    def test_stat_value_parsing(self):
        """Test parsing of different stat value types."""
        # Test with comma-separated numbers
        parsed_stats = self.data_gen.generate_valid_submission('ParseTestAgent', 'Enlightened')
        parsed_stats[6]['value'] = '1,234,567'  # Lifetime AP with commas
        parsed_stats[7]['value'] = '987,654'    # Current AP with commas

        result = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Verify values were parsed correctly
        with self.db_connection.session_scope() as session:
            ap_stats = session.query(AgentStat).filter(
                AgentStat.submission_id == result['submission_id'],
                AgentStat.stat_idx.in_([6, 7])
            ).all()

            for stat in ap_stats:
                if stat.stat_idx == 6:  # Lifetime AP
                    self.assertEqual(stat.stat_value, 1234567)
                elif stat.stat_idx == 7:  # Current AP
                    self.assertEqual(stat.stat_value, 987654)

    def test_edge_case_zero_values(self):
        """Test handling of zero values in stats."""
        parsed_stats = self.data_gen.generate_valid_submission('ZeroValueAgent', 'Enlightened')

        # Set some stats to zero
        parsed_stats[6]['value'] = '0'      # Lifetime AP = 0
        parsed_stats[7]['value'] = '0'      # Current AP = 0
        parsed_stats[11]['value'] = '0'     # XM Collected = 0

        result = self.stats_db.save_stats(self.test_telegram_id, parsed_stats)

        # Verify save was successful
        self.assertTrue(result['success'])
        self.assertEqual(result['lifetime_ap'], 0)
        self.assertEqual(result['current_ap'], 0)
        self.assertEqual(result['xm_collected'], 0)

    def test_database_session_transaction_rollback(self):
        """Test that transactions are rolled back on errors."""
        parsed_stats = self.data_gen.generate_valid_submission('RollbackTest', 'Enlightened')

        # Mock the session to raise an exception during commit
        with patch.object(self.db_connection, 'session_scope') as mock_scope:
            mock_session = Mock()
            mock_scope.return_value.__enter__.return_value = mock_session
            mock_scope.return_value.__exit__.return_value = None

            # Simulate an exception during database operations
            mock_session.query.side_effect = Exception("Database error")

            with self.assertRaises(Exception):
                self.stats_db.save_stats(self.test_telegram_id, parsed_stats)


if __name__ == '__main__':
    unittest.main()