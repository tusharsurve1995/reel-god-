"""
REEL GOD — Scheduler Unit Test Suite
======================================
Tests database persistence of weekly strategies, pending slot checks,
analytics aggregation, and autonomous scheduled loops.
"""

import os
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

# Adjust python path to find project modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import config
from brain.core import ReelGodBrain
from main import check_scheduled_posts
from instagram.publisher import InstagramPublisher


class TestSchedulerPipeline(unittest.TestCase):
    """
    Test suite for Content Scheduler and performance tracking.
    """

    def setUp(self):
        # Create a temporary workspace directory structure
        self.test_dir = Path(tempfile.mkdtemp(prefix="reelgod_test_"))
        self.db_path = self.test_dir / "test_memory.db"
        
        # Override config paths for testing
        self.original_db_path = config.DB_PATH
        config.DB_PATH = self.db_path
        
        # Set up a mock Gemini API key in env
        os.environ["GEMINI_API_KEY"] = "mock_api_key_for_testing"
        
        # Stub the slow video compilation method for unit testing
        self.original_generate_method = ReelGodBrain.generate_video_content
        
        def mock_generate_video_content(brain_self, idea_id):
            idea = brain_self.memory.get_idea(idea_id)
            post_id = brain_self.memory.save_post(
                idea_id=idea_id,
                video_path=f"data/content_archive/final_reel_{idea_id}_dark_cinematic.mp4",
                caption="Mock caption!",
                hashtags="#anime",
                music_track="Helix.mp3",
                title=idea["title"],
                style=idea["style"]
            )
            return f"data/content_archive/final_reel_{idea_id}_dark_cinematic.mp4"
            
        ReelGodBrain.generate_video_content = mock_generate_video_content
        
        # Stub the Instagram publisher to avoid real logins during unit testing
        self.original_publish_method = InstagramPublisher.publish_reel
        
        def mock_publish_reel(pub_self, video_path, caption):
            return "mock_instagram_media_id"
            
        InstagramPublisher.publish_reel = mock_publish_reel
        
        # Initialize Core Brain
        self.brain = ReelGodBrain()

    def tearDown(self):
        # Restore configuration
        config.DB_PATH = self.original_db_path
        
        # Restore stubbed methods
        ReelGodBrain.generate_video_content = self.original_generate_method
        InstagramPublisher.publish_reel = self.original_publish_method
        
        # Clean up temporary test files
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_database_schedule_persistence(self):
        """Test scheduling slots can be saved, retrieved and filtered."""
        memory = self.brain.memory
        
        # Save scheduled slots
        memory.save_schedule_day("Monday", "2026-06-29", "dark_cinematic", "Samurai Fight", "18:00")
        memory.save_schedule_day("Tuesday", "2026-06-30", "emotional", "Loss & Grief", "12:00")
        
        # Retrieve active schedule
        schedule = memory.get_active_schedule()
        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0]["day_name"], "Monday")
        self.assertEqual(schedule[0]["date_str"], "2026-06-29")
        self.assertEqual(schedule[0]["style"], "dark_cinematic")
        
        # Retrieve pending slots due at Monday 19:00 (Monday slot is due, Tuesday is not)
        pending = memory.get_pending_scheduled_slots("2026-06-29", "19:00")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["theme"], "Samurai Fight")
        
        # Mark slot published
        memory.mark_slot_published(pending[0]["id"], post_id=42)
        
        # Confirm no pending slots due now
        pending_after = memory.get_pending_scheduled_slots("2026-06-29", "19:00")
        self.assertEqual(len(pending_after), 0)

    def test_metrics_updates_and_aggregations(self):
        """Test posts analytics saving and style performance computation."""
        memory = self.brain.memory
        
        # 1. Record post in database
        post_id = memory.save_post(
            idea_id=1,
            video_path="mock/path/video.mp4",
            caption="Awesome edit!",
            hashtags="#anime",
            music_track="Helix.mp3",
            title="Mystical Ninja",
            style="dark_cinematic"
        )
        
        # 2. Update post metrics
        metrics = {
            "views": 1000,
            "likes": 80,
            "comments": 20,
            "saves": 10,
            "shares": 5,
            "reach": 900
        }
        memory.update_post_analytics(post_id, metrics)
        
        # Check post metrics
        with memory._connect() as conn:
            row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            post = dict(row)
            
        self.assertEqual(post["views"], 1000)
        self.assertEqual(post["likes"], 80)
        # Engagement rate = (80 + 20) / 1000 * 100 = 10%
        self.assertEqual(post["engagement_rate"], 10.0)
        
        # Check style performance aggregation table updates
        with memory._connect() as conn:
            row = conn.execute("SELECT * FROM style_performance WHERE style = 'dark_cinematic'").fetchone()
            perf = dict(row)
            
        self.assertEqual(perf["post_count"], 1)
        self.assertEqual(perf["avg_engagement"], 10.0)
        self.assertEqual(perf["avg_views"], 1000.0)

    def test_scheduled_posting_dry_run_loop(self):
        """Test that check_scheduled_posts triggers code generation and handles mock posting correctly."""
        memory = self.brain.memory
        
        # Set up a due scheduled slot for TODAY
        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        # Put posting time 1 minute ago so it triggers as due
        past_time = (now - timedelta(minutes=5)).strftime('%H:%M')
        
        slot_id = memory.save_schedule_day("TodaySlot", today_str, "dark_cinematic", "Test Cyberpunk", past_time)
        
        # Prepare an approved idea for the loop to select
        idea_id = memory.save_idea(
            title="E2E Cyberpunk Ninja",
            style="dark_cinematic",
            story="A ninja hacking a corporation portal. Glitching screen effects."
        )
        memory.approve_idea(idea_id)
        
        # Execute schedule checker loop (dry-run mode since INSTAGRAM_USERNAME not set in env)
        check_scheduled_posts(self.brain)
        
        # Verify schedule slot marked published
        with memory._connect() as conn:
            slot = conn.execute("SELECT * FROM content_schedule WHERE id = ?", (slot_id,)).fetchone()
            slot_dict = dict(slot)
            
        self.assertEqual(slot_dict["status"], "published")
        self.assertIsNotNone(slot_dict["post_id"])
        
        # Verify compiled Reel video saved in database
        post_id = slot_dict["post_id"]
        with memory._connect() as conn:
            post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            post_dict = dict(post)
            
        self.assertEqual(post_dict["idea_id"], idea_id)
        self.assertIn("final_reel_", post_dict["video_path"])


if __name__ == "__main__":
    unittest.main()
