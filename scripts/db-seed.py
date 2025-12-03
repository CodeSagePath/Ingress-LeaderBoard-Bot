#!/usr/bin/env python3
"""
Development Database Seeding Script
This script generates sample data for development and testing purposes.
"""

import os
import sys
import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.models import Base, User, Agent, StatsSubmission, AgentStat, Faction
from database.database import get_async_session, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# Sample data constants
FACTIONS = ["Enlightened", "Resistance"]
AGENTS = [
    "MaxVerstappen", "LewisHamilton", "CharlesLeclerc", "CarlosSainz",
    "LandoNorris", "GeorgeRussell", "SergioPerez", "FernandoAlonso",
    "EstebanOcon", "PierreGasly", "ValtteriBottas", "ZhouGuanyu",
    "YukiTsunoda", "LiamLawson", "OscarPiastri", "LoganSargeant"
]

# Sample statistics (simplified for development)
SAMPLE_STATS = [
    "ap", "explorer_points", "seer_points", "banked_points",
    "player_level", "recursions", "mission_count", "unique_portals_visited",
    "time_worked", "distance_walked", "resonators_deployed", "links_created",
    "control_fields_created", "xm_collected", "xm_recharged", "portals_captured",
    "portals_neutralized", "mods_deployed", "resonators_destroyed",
    "links_destroyed", "control_fields_destroyed"
]

def generate_random_stats():
    """Generate random stats for an agent."""
    return {
        "ap": random.randint(100000, 50000000),
        "explorer_points": random.randint(1000, 50000),
        "seer_points": random.randint(100, 10000),
        "banked_points": random.randint(0, 50000),
        "player_level": random.randint(1, 16),
        "recursions": random.randint(0, 5),
        "mission_count": random.randint(0, 1000),
        "unique_portals_visited": random.randint(100, 50000),
        "time_worked": random.randint(86400, 15552000),  # 1 day to 180 days in seconds
        "distance_walked": random.randint(100, 10000),  # kilometers
        "resonators_deployed": random.randint(100, 50000),
        "links_created": random.randint(50, 25000),
        "control_fields_created": random.randint(25, 15000),
        "xm_collected": random.randint(1000000, 50000000),
        "xm_recharged": random.randint(500000, 25000000),
        "portals_captured": random.randint(100, 20000),
        "portals_neutralized": random.randint(50, 15000),
        "mods_deployed": random.randint(200, 30000),
        "resonators_destroyed": random.randint(150, 40000),
        "links_destroyed": random.randint(25, 20000),
        "control_fields_destroyed": random.randint(10, 15000),
    }

async def create_sample_data():
    """Create sample data for development."""

    print("🌱 Creating development sample data...")

    async with get_async_session() as session:
        # Check if data already exists
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("⚠️ Sample data already exists. Skipping creation.")
            return

        # Create sample users and agents
        for i, agent_name in enumerate(AGENTS):
            # Create user
            user = User(
                telegram_id=1000000 + i,
                telegram_username=agent_name.lower(),
                telegram_first_name=agent_name.split()[0],
                telegram_last_name=agent_name.split()[1] if len(agent_name.split()) > 1 else None,
                is_active=True,
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            session.add(user)
            await session.flush()  # Get the user ID

            # Create agent
            agent = Agent(
                user_id=user.id,
                agent_name=agent_name,
                faction=random.choice(FACTIONS),
                level=random.randint(1, 16),
                is_active=True,
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            session.add(agent)
            await session.flush()

            # Create a recent stats submission
            submission = StatsSubmission(
                agent_id=agent.id,
                submission_data="Sample development data",
                validated=True,
                created_at=datetime.now() - timedelta(hours=random.randint(1, 168))
            )
            session.add(submission)
            await session.flush()

            # Create stats
            stats = generate_random_stats()
            for stat_name, stat_value in stats.items():
                agent_stat = AgentStat(
                    agent_id=agent.id,
                    stat_name=stat_name,
                    stat_value=stat_value,
                    submission_id=submission.id,
                    created_at=submission.created_at
                )
                session.add(agent_stat)

        await session.commit()
        print(f"✅ Created sample data for {len(AGENTS)} agents")

async def main():
    """Main function."""
    try:
        # Create database tables
        print("🗄️ Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create sample data
        await create_sample_data()

        print("")
        print("🎉 Development database seeded successfully!")
        print("📊 Summary:")
        print(f"   • Agents created: {len(AGENTS)}")
        print(f"   • Statistics per agent: {len(SAMPLE_STATS)}")
        print("   • Database: ingress_leaderboard_dev")
        print("")
        print("🔍 You can now test the bot with sample data:")
        print("   • Try the /leaderboard command")
        print("   • Test /mystats functionality")
        print("   • Browse different stat categories")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())