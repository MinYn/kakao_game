import importlib
import importlib.util
import sys
import unittest
from unittest.mock import Mock, patch

from games.ship_system import ShipGrade, ShipProgress


API_DEPS_AVAILABLE = all(
    importlib.util.find_spec(module) is not None
    for module in ("fastapi", "pydantic", "psycopg2", "kafka")
)


@unittest.skipUnless(
    API_DEPS_AVAILABLE,
    "API/PostgreSQL optional dependencies are not installed",
)
class SpaceBadgeApiTestCase(unittest.TestCase):
    def test_http_badge_uses_stored_grade_and_body_enhance(self):
        from db.postgres import PostgreSQLManager
        from gold_system_postgres import GoldSystemPostgres

        with patch.object(PostgreSQLManager, "initialize"), patch.object(
            GoldSystemPostgres, "__init__", return_value=None
        ):
            sys.modules.pop("api.space_badges", None)
            module = importlib.import_module("api.space_badges")

        module.gold_system = Mock(
            get_ship_progress=Mock(
                return_value=ShipProgress(
                    grade=ShipGrade.S,
                    body_enhance=12,
                    equipped_ship_id="event_horizon",
                )
            )
        )
        response = module.get_space_badge("pilot")

        self.assertEqual(response.sub, "+12")
        self.assertIn(">S<", response.svg)
        self.assertIn(">+12<", response.svg)


if __name__ == "__main__":
    unittest.main()
