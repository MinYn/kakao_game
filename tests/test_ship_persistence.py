import importlib.util
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from games.adventure import AdventureGame
from games.ship_system import ShipGrade, ShipProgress
from gold_system import GoldSystem


class SQLiteShipPersistenceTestCase(unittest.TestCase):
    def test_legacy_level_table_is_migrated_when_body_column_is_added(self):
        with tempfile.NamedTemporaryFile() as db_file:
            conn = sqlite3.connect(db_file.name)
            conn.execute(
                """
                CREATE TABLE enhancement_levels (
                    user_id TEXT PRIMARY KEY,
                    level INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "INSERT INTO enhancement_levels (user_id, level) VALUES (?, ?)",
                ("legacy", 5),
            )
            conn.commit()
            conn.close()

            system = GoldSystem(db_file.name)
            progress = system.get_ship_progress("legacy")

            self.assertEqual(progress.grade, ShipGrade.F)
            self.assertEqual(progress.body_enhance, 5)

    def test_existing_body_column_is_authoritative_on_reinit(self):
        with tempfile.NamedTemporaryFile() as db_file:
            system = GoldSystem(db_file.name)
            conn = sqlite3.connect(db_file.name)
            conn.execute(
                """
                INSERT INTO enhancement_levels (
                    user_id, level, ship_grade, body_enhance
                ) VALUES (?, ?, ?, ?)
                """,
                ("sold", 7, "E", 0),
            )
            conn.commit()
            conn.close()

            # 이미 신규 컬럼이 있는 DB에서는 level 값을 body_enhance 로 되살리지 않는다.
            restarted = GoldSystem(db_file.name)
            progress = restarted.get_ship_progress("sold")
            conn = sqlite3.connect(db_file.name)
            row = conn.execute(
                "SELECT level, body_enhance FROM enhancement_levels WHERE user_id = ?",
                ("sold",),
            ).fetchone()
            conn.close()

            self.assertEqual(progress.body_enhance, 0)
            self.assertEqual(row, (0, 0))
            del system

    def test_sell_preserves_parts_and_survives_reinit(self):
        with tempfile.NamedTemporaryFile() as db_file:
            system = GoldSystem(db_file.name)
            system.set_ship_progress(
                "pilot",
                ShipProgress(
                    grade=ShipGrade.E,
                    body_enhance=3,
                    equipped_ship_id="ion_falcon",
                    parts={"engine": 4, "sensor": 2, "armor": 1},
                ),
            )
            game = AdventureGame("pilot", point_system=system)
            game.start()

            response = game._sell()
            restarted = GoldSystem(db_file.name)
            progress = restarted.get_ship_progress("pilot")

            self.assertIn("정산 완료", response)
            self.assertIn("파츠 유지", response)
            self.assertEqual(progress.grade, ShipGrade.E)
            self.assertEqual(progress.body_enhance, 0)
            self.assertEqual(progress.equipped_ship_id, "ion_falcon")
            self.assertEqual(
                progress.parts,
                {"engine": 4, "sensor": 2, "armor": 1},
            )


POSTGRES_DEPS_AVAILABLE = all(
    importlib.util.find_spec(module) is not None
    for module in ("psycopg2", "kafka")
)


@unittest.skipUnless(
    POSTGRES_DEPS_AVAILABLE,
    "PostgreSQL/Kafka optional dependencies are not installed",
)
class PostgresShipPersistenceTestCase(unittest.TestCase):
    class FakeCursor:
        def __init__(self):
            self.records = {}
            self.result = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            sql = " ".join(query.split())
            if sql.startswith("SELECT user_id FROM enhancement_levels"):
                user_id = params[0]
                self.result = (user_id,) if user_id in self.records else None
            elif sql.startswith("UPDATE enhancement_levels SET level = %s"):
                body, grade, _, equipped, engine, sensor, armor, user_id = params
                self.records[user_id] = (
                    body,
                    grade,
                    body,
                    equipped,
                    engine,
                    sensor,
                    armor,
                )
                self.result = None
            elif sql.startswith("INSERT INTO enhancement_levels"):
                user_id, body, grade, _, equipped, engine, sensor, armor = params
                self.records[user_id] = (
                    body,
                    grade,
                    body,
                    equipped,
                    engine,
                    sensor,
                    armor,
                )
                self.result = None
            elif sql.startswith("SELECT level, ship_grade, body_enhance"):
                self.result = self.records.get(params[0])
            else:
                raise AssertionError(f"unexpected SQL: {sql}")

        def fetchone(self):
            return self.result

    class FakeConnection:
        def __init__(self):
            self.fake_cursor = PostgresShipPersistenceTestCase.FakeCursor()
            self.commits = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return self.fake_cursor

        def commit(self):
            self.commits += 1

    class FakeMigrationCursor:
        def __init__(self, existing_columns):
            self.existing_columns = set(existing_columns)
            self.result = None
            self.queries = []

        def execute(self, query, params=None):
            sql = " ".join(query.split())
            self.queries.append(sql)
            if sql.startswith("SELECT 1 FROM information_schema.columns"):
                self.result = (1,) if params[0] in self.existing_columns else None
            elif sql.startswith("ALTER TABLE enhancement_levels ADD COLUMN"):
                self.existing_columns.add(sql.split()[5])
                self.result = None

        def fetchone(self):
            return self.result

    def test_get_set_ship_progress_round_trip(self):
        from db.postgres import PostgreSQLManager
        from gold_system_postgres import GoldSystemPostgres

        conn = self.FakeConnection()
        system = GoldSystemPostgres.__new__(GoldSystemPostgres)
        expected = ShipProgress(
            grade=ShipGrade.B,
            body_enhance=12,
            equipped_ship_id="void_manta",
            parts={"engine": 7, "sensor": 5, "armor": 3},
        )

        with patch.object(PostgreSQLManager, "get_connection", return_value=conn):
            system.set_ship_progress("pilot", expected)
            actual = system.get_ship_progress("pilot")

        self.assertEqual(actual, expected)
        self.assertEqual(conn.commits, 1)

    def test_postgres_legacy_copy_only_runs_when_body_column_is_added(self):
        from db.postgres import PostgreSQLManager

        base_columns = {
            "ship_grade",
            "body_enhance",
            "equipped_ship_id",
            "part_engine",
            "part_sensor",
            "part_armor",
        }
        current = self.FakeMigrationCursor(base_columns)
        PostgreSQLManager._ensure_enhancement_columns(current)
        current_sql = "\n".join(current.queries)

        legacy = self.FakeMigrationCursor(set())
        PostgreSQLManager._ensure_enhancement_columns(legacy)
        legacy_sql = "\n".join(legacy.queries)

        legacy_copy = "SET body_enhance = GREATEST(COALESCE(level, 0), 0)"
        self.assertNotIn(legacy_copy, current_sql)
        self.assertIn(legacy_copy, legacy_sql)
        self.assertIn(
            "SET level = GREATEST(COALESCE(body_enhance, 0), 0)",
            current_sql,
        )


if __name__ == "__main__":
    unittest.main()
