"""
Test no-delimiter stats parsing (Telegram strips tabs).

Uses REAL data from an actual user submission to verify the parser
handles the most common real-world input format.
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.stats_parser import StatsParser


class TestNoDelimiterParsing(unittest.TestCase):
    """Test parsing of stats where Telegram has stripped all tab characters."""

    def setUp(self):
        self.parser = StatsParser()

        # Real data from H1GHT0WER — exactly as Telegram delivers it (no tabs)
        self.header_line = (
            "Time SpanAgent NameAgent FactionDate (yyyy-mm-dd)"
            "Time (hh:mm:ss)LevelLifetime APCurrent APUnique Portals Visited"
            "Unique Portals Drone VisitedFurthest Drone DistanceSeer Points"
            "XM CollectedOPR AgreementsPortal Scans UploadedUniques Scout Controlled"
            "Resonators DeployedLinks CreatedControl Fields CreatedMind Units Captured"
            "Longest Link Ever CreatedLargest Control FieldXM Recharged"
            "Portals CapturedUnique Portals CapturedMods DeployedHacksDrone Hacks"
            "Glyph Hack PointsOverclock Hack PointsCompleted Hackstreaks"
            "Longest Sojourner StreakResonators DestroyedPortals Neutralized"
            "Enemy Links DestroyedEnemy Fields DestroyedDrones Returned"
            "Machina Links DestroyedMachina Resonators DestroyedMachina Portals Neutralized"
            "Machina Portals ReclaimedMax Time Portal HeldMax Time Link Maintained"
            "Max Link Length x DaysMax Time Field HeldLargest Field MUs x Days"
            "Forced Drone RecallsDistance WalkedKinetic Capsules Completed"
            "Unique Missions CompletedResearch Bounties CompletedResearch Days Completed"
            "NL-1331 Meetup(s) AttendedFirst Saturday EventsSecond Sunday Events"
            "+Gamma Tokens+Gamma Link PointsAgents RecruitedMonths Subscribed"
        )

        self.values_line = (
            "ALL TIMEH1GHT0WEREnlightened2026-02-1815:28:2914184971281849712831312"
            "345359141751210682079719410317620883115807712428368216919355744512245"
            "290412971117614432253811760539499863559316240327040321214810475133228"
            "749404737842831112091671235250023481"
            "1"
        )

        # Full two-line message as would arrive from Telegram
        self.full_stats_text = self.header_line + "\n" + self.values_line

    def test_header_splitting(self):
        """Test that the no-delimiter header splitter finds all known stat names."""
        headers = self.parser._split_no_delimiter_header(self.header_line)

        # Should find many stat names
        self.assertGreaterEqual(len(headers), 40, f"Expected 40+ headers, got {len(headers)}: {headers[:10]}...")

        # Verify key headers are present
        header_set = {h.lower() for h in headers}
        expected = [
            'time span', 'agent name', 'agent faction',
            'lifetime ap', 'unique portals visited',
            'links created', 'xm recharged', 'hacks',
            'distance walked'
        ]
        for name in expected:
            found = any(name in h for h in header_set)
            self.assertTrue(found, f"Expected header '{name}' not found in: {headers[:20]}...")

    def test_full_parse(self):
        """Test end-to-end parsing of real no-delimiter stats."""
        result = self.parser.parse(self.full_stats_text)

        # Should NOT have an error
        self.assertNotIn('error', result,
                         f"Parse failed with: {result.get('error', '')} (code {result.get('error_code', '?')})")

        # Verify key parsed values via summary
        summary = self.parser.get_stat_summary(result)
        self.assertEqual(summary['agent_name'], 'H1GHT0WER', f"Agent name wrong: {summary['agent_name']}")
        self.assertEqual(summary['faction'], 'Enlightened', f"Faction wrong: {summary['faction']}")

    def test_value_splitting_key_fields(self):
        """Test that known value fields are correctly extracted."""
        headers = self.parser._split_no_delimiter_header(self.header_line)
        values = self.parser._split_no_delimiter_values(self.values_line, headers)

        # Build a dict for easier checking
        paired = dict(zip([h.lower() for h in headers], values))

        # Time Span
        self.assertIn('all time', paired.get('time span', '').lower(),
                       f"Time Span: {paired.get('time span')}")

        # Agent Name
        self.assertEqual(paired.get('agent name', ''), 'H1GHT0WER',
                         f"Agent Name: {paired.get('agent name')}")

        # Faction
        self.assertEqual(paired.get('agent faction', ''), 'Enlightened',
                         f"Faction: {paired.get('agent faction')}")

        # Date
        self.assertEqual(paired.get('date (yyyy-mm-dd)', ''), '2026-02-18',
                         f"Date: {paired.get('date (yyyy-mm-dd)')}")

        # Time
        self.assertEqual(paired.get('time (hh:mm:ss)', ''), '15:28:29',
                         f"Time: {paired.get('time (hh:mm:ss)')}")

        # Level
        self.assertEqual(paired.get('level', ''), '14',
                         f"Level: {paired.get('level')}")

    def test_looks_like_stats(self):
        """Verify the text passes the initial stats detection."""
        self.assertTrue(self.parser.is_valid_stats(self.full_stats_text))

    def test_tab_separated_still_works(self):
        """Ensure tab-separated format (original) still works."""
        tab_text = (
            "Time Span\tAgent Name\tAgent Faction\tDate (yyyy-mm-dd)\tTime (hh:mm:ss)\t"
            "Level\tLifetime AP\tCurrent AP\tUnique Portals Visited\n"
            "ALL TIME\tTestAgent\tResistance\t2026-01-01\t12:00:00\t16\t50000000\t1000000\t5000"
        )
        result = self.parser.parse(tab_text)
        self.assertNotIn('error', result,
                         f"Tab parse failed: {result.get('error', '')}")


if __name__ == '__main__':
    unittest.main()
