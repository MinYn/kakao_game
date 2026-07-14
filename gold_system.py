import sqlite3
from typing import Dict, Optional, Callable
from config import Config


class GoldSystem:
    """골드 관리 시스템 (SQLite 사용)"""
    
    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or Config.DATA_FILE
        self.gold_callbacks: Dict[str, Callable[[str, int, str], None]] = {}
        self._init_database()
    
    def _init_database(self) -> None:
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 골드 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold (
                user_id TEXT PRIMARY KEY,
                gold INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 골드 이력 테이블 생성 (선택사항)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 보스몹 입장권 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boss_tickets (
                user_id TEXT PRIMARY KEY,
                tickets INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 강화 레벨 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhancement_levels (
                user_id TEXT PRIMARY KEY,
                level INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 게임 통계 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id TEXT PRIMARY KEY,
                enhancement_attempts INTEGER NOT NULL DEFAULT 0,
                enhancement_successes INTEGER NOT NULL DEFAULT 0,
                enhancement_failures INTEGER NOT NULL DEFAULT 0,
                hunt_normal INTEGER NOT NULL DEFAULT 0,
                hunt_special INTEGER NOT NULL DEFAULT 0,
                hunt_boss INTEGER NOT NULL DEFAULT 0,
                total_hunts INTEGER NOT NULL DEFAULT 0,
                total_hunt_reward INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 우주선 수집 도감 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ship_collection (
                user_id TEXT NOT NULL,
                ship_id TEXT NOT NULL,
                acquired_count INTEGER NOT NULL DEFAULT 1,
                first_acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, ship_id)
            )
        ''')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_ship_collection_user_id ON ship_collection(user_id)'
        )
        
        conn.commit()
        conn.close()

    def add_ship_to_collection(self, user_id: str, ship_id: str) -> dict:
        """우주선 도감에 함선 추가. 중복 획득 시 카운트만 증가."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT acquired_count FROM ship_collection WHERE user_id = ? AND ship_id = ?',
            (user_id, ship_id),
        )
        result = cursor.fetchone()

        if result:
            new_count = result['acquired_count'] + 1
            cursor.execute(
                '''
                UPDATE ship_collection
                SET acquired_count = ?, last_acquired_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND ship_id = ?
                ''',
                (new_count, user_id, ship_id),
            )
            is_new = False
        else:
            new_count = 1
            cursor.execute(
                'INSERT INTO ship_collection (user_id, ship_id, acquired_count) VALUES (?, ?, ?)',
                (user_id, ship_id, new_count),
            )
            is_new = True

        conn.commit()
        conn.close()
        return {'ship_id': ship_id, 'is_new': is_new, 'count': new_count}

    def get_ship_collection(self, user_id: str) -> list[dict]:
        """사용자 우주선 도감 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT ship_id, acquired_count, first_acquired_at, last_acquired_at
            FROM ship_collection
            WHERE user_id = ?
            ORDER BY first_acquired_at ASC
            ''',
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'ship_id': row['ship_id'],
                'count': row['acquired_count'],
                'first_acquired_at': row['first_acquired_at'],
                'last_acquired_at': row['last_acquired_at'],
            }
            for row in rows
        ]
    
    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_gold(self, user_id: str) -> int:
        """사용자 골드 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT gold FROM gold WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['gold'] if result else 0
    
    def ensure_initial_gold(self, user_id: str) -> bool:
        """사용자가 처음 접속한 경우 초기 골드 지급"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT gold FROM gold WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            conn.close()
            self.add_gold(user_id, Config.INITIAL_GOLD, "신규 사용자 환영 골드")
            return True
        
        conn.close()
        return False
    
    def add_gold(self, user_id: str, amount: int, reason: str = "") -> int:
        """골드 추가"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 기존 골드 조회 또는 생성
        cursor.execute('SELECT gold FROM gold WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            new_gold = result['gold'] + amount
            cursor.execute(
                'UPDATE gold SET gold = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (new_gold, user_id)
            )
        else:
            new_gold = amount
            cursor.execute(
                'INSERT INTO gold (user_id, gold) VALUES (?, ?)',
                (user_id, new_gold)
            )
        
        # 이력 기록
        if reason:
            cursor.execute(
                'INSERT INTO gold_history (user_id, amount, reason) VALUES (?, ?, ?)',
                (user_id, amount, reason)
            )
        
        conn.commit()
        conn.close()
        
        # 콜백 호출
        if 'add' in self.gold_callbacks:
            self.gold_callbacks['add'](user_id, amount, reason)
        
        return new_gold
    
    def deduct_gold(self, user_id: str, amount: int, reason: str = "") -> Optional[int]:
        """골드 차감 (잔액 부족 시 None 반환)"""
        current_gold = self.get_gold(user_id)
        
        if current_gold < amount:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        new_gold = current_gold - amount
        cursor.execute(
            'UPDATE gold SET gold = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
            (new_gold, user_id)
        )
        
        # 이력 기록
        if reason:
            cursor.execute(
                'INSERT INTO gold_history (user_id, amount, reason) VALUES (?, ?, ?)',
                (user_id, -amount, reason)
            )
        
        conn.commit()
        conn.close()
        
        # 콜백 호출
        if 'deduct' in self.gold_callbacks:
            self.gold_callbacks['deduct'](user_id, amount, reason)
        
        return new_gold
    
    def set_gold(self, user_id: str, amount: int) -> None:
        """골드 설정"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        amount = max(0, amount)
        cursor.execute('SELECT gold FROM gold WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                'UPDATE gold SET gold = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (amount, user_id)
            )
        else:
            cursor.execute(
                'INSERT INTO gold (user_id, gold) VALUES (?, ?)',
                (user_id, amount)
            )
        
        conn.commit()
        conn.close()
    
    def has_gold(self, user_id: str, amount: int) -> bool:
        """골드 보유 여부 확인"""
        return self.get_gold(user_id) >= amount
    
    def register_callback(self, event_type: str, callback: Callable[[str, int, str], None]) -> None:
        """골드 이벤트 콜백 등록"""
        self.gold_callbacks[event_type] = callback
    
    def transfer_gold(self, from_user: str, to_user: str, amount: int, reason: str = "") -> Optional[int]:
        """골드 전송 (from_user → to_user)"""
        # 자기 자신에게 전송 불가
        if from_user == to_user:
            return None
        
        # 골드 확인
        if not self.has_gold(from_user, amount):
            return None
        
        # 최소 전송 금액 체크
        if amount <= 0:
            return None
        
        # 골드 차감 및 추가
        deducted = self.deduct_gold(from_user, amount, f"골드 전송 → {to_user}: {reason}")
        if deducted is None:
            return None
        
        result = self.add_gold(to_user, amount, f"골드 수신 ← {from_user}: {reason}")
        return result
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """리더보드 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id, gold FROM gold ORDER BY gold DESC LIMIT ?',
            (limit,)
        )
        results = cursor.fetchall()
        
        conn.close()
        return [(row['user_id'], row['gold']) for row in results]
    
    def get_gold_history(self, user_id: str, limit: int = 10) -> list:
        """골드 이력 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT amount, reason, created_at 
               FROM gold_history 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?''',
            (user_id, limit)
        )
        results = cursor.fetchall()
        
        conn.close()
        return [
            {
                'amount': row['amount'],
                'reason': row['reason'],
                'created_at': row['created_at']
            }
            for row in results
        ]
    
    def get_boss_tickets(self, user_id: str) -> int:
        """보스몹 입장권 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT tickets FROM boss_tickets WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['tickets'] if result else 0
    
    def add_boss_ticket(self, user_id: str, amount: int = 1, reason: str = "") -> int:
        """보스몹 입장권 추가"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT tickets FROM boss_tickets WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            new_tickets = result['tickets'] + amount
            cursor.execute(
                'UPDATE boss_tickets SET tickets = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (new_tickets, user_id)
            )
        else:
            new_tickets = amount
            cursor.execute(
                'INSERT INTO boss_tickets (user_id, tickets) VALUES (?, ?)',
                (user_id, new_tickets)
            )
        
        conn.commit()
        conn.close()
        return new_tickets
    
    def use_boss_ticket(self, user_id: str, amount: int = 1, reason: str = "") -> bool:
        """보스몹 입장권 사용 (잔액 부족 시 False 반환)"""
        current_tickets = self.get_boss_tickets(user_id)
        
        if current_tickets < amount:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        new_tickets = current_tickets - amount
        cursor.execute(
            'UPDATE boss_tickets SET tickets = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
            (new_tickets, user_id)
        )
        
        conn.commit()
        conn.close()
        return True
    
    def get_enhancement_level(self, user_id: str) -> int:
        """강화 레벨 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT level FROM enhancement_levels WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['level'] if result else 0
    
    def set_enhancement_level(self, user_id: str, level: int) -> None:
        """강화 레벨 설정"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        level = max(0, level)  # 최소 0
        cursor.execute('SELECT level FROM enhancement_levels WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                'UPDATE enhancement_levels SET level = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (level, user_id)
            )
        else:
            cursor.execute(
                'INSERT INTO enhancement_levels (user_id, level) VALUES (?, ?)',
                (user_id, level)
            )
        
        conn.commit()
        conn.close()
    
    def get_game_stats(self, user_id: str) -> dict:
        """게임 통계 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT enhancement_attempts, enhancement_successes, enhancement_failures,
                   hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward
            FROM game_stats WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'enhancement_attempts': result['enhancement_attempts'],
                'enhancement_successes': result['enhancement_successes'],
                'enhancement_failures': result['enhancement_failures'],
                'hunt_normal': result['hunt_normal'],
                'hunt_special': result['hunt_special'],
                'hunt_boss': result['hunt_boss'],
                'total_hunts': result['total_hunts'],
                'total_hunt_reward': result['total_hunt_reward']
            }
        else:
            return {
                'enhancement_attempts': 0,
                'enhancement_successes': 0,
                'enhancement_failures': 0,
                'hunt_normal': 0,
                'hunt_special': 0,
                'hunt_boss': 0,
                'total_hunts': 0,
                'total_hunt_reward': 0
            }
    
    def update_game_stats(
        self,
        user_id: str,
        enhancement_attempts: int = 0,
        enhancement_successes: int = 0,
        enhancement_failures: int = 0,
        hunt_normal: int = 0,
        hunt_special: int = 0,
        hunt_boss: int = 0,
        total_hunts: int = 0,
        total_hunt_reward: int = 0
    ) -> None:
        """게임 통계 업데이트 (증가값으로 업데이트)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 기존 통계 조회
        cursor.execute('SELECT * FROM game_stats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            # 기존 값에 증가값 추가
            new_attempts = result['enhancement_attempts'] + enhancement_attempts
            new_successes = result['enhancement_successes'] + enhancement_successes
            new_failures = result['enhancement_failures'] + enhancement_failures
            new_normal = result['hunt_normal'] + hunt_normal
            new_special = result['hunt_special'] + hunt_special
            new_boss = result['hunt_boss'] + hunt_boss
            new_total_hunts = result['total_hunts'] + total_hunts
            new_total_reward = result['total_hunt_reward'] + total_hunt_reward
            
            cursor.execute('''
                UPDATE game_stats SET
                    enhancement_attempts = ?,
                    enhancement_successes = ?,
                    enhancement_failures = ?,
                    hunt_normal = ?,
                    hunt_special = ?,
                    hunt_boss = ?,
                    total_hunts = ?,
                    total_hunt_reward = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_attempts, new_successes, new_failures, new_normal, new_special,
                  new_boss, new_total_hunts, new_total_reward, user_id))
        else:
            # 새로 생성
            cursor.execute('''
                INSERT INTO game_stats (
                    user_id, enhancement_attempts, enhancement_successes, enhancement_failures,
                    hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, enhancement_attempts, enhancement_successes, enhancement_failures,
                  hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward))
        
        conn.commit()
        conn.close()
    
    def set_game_stats(
        self,
        user_id: str,
        enhancement_attempts: int = None,
        enhancement_successes: int = None,
        enhancement_failures: int = None,
        hunt_normal: int = None,
        hunt_special: int = None,
        hunt_boss: int = None,
        total_hunts: int = None,
        total_hunt_reward: int = None
    ) -> None:
        """게임 통계 설정 (절대값으로 설정)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 기존 통계 조회
        cursor.execute('SELECT * FROM game_stats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            # 기존 값 유지하거나 새 값으로 업데이트
            attempts = enhancement_attempts if enhancement_attempts is not None else result['enhancement_attempts']
            successes = enhancement_successes if enhancement_successes is not None else result['enhancement_successes']
            failures = enhancement_failures if enhancement_failures is not None else result['enhancement_failures']
            normal = hunt_normal if hunt_normal is not None else result['hunt_normal']
            special = hunt_special if hunt_special is not None else result['hunt_special']
            boss = hunt_boss if hunt_boss is not None else result['hunt_boss']
            total_hunts_val = total_hunts if total_hunts is not None else result['total_hunts']
            total_reward = total_hunt_reward if total_hunt_reward is not None else result['total_hunt_reward']
            
            cursor.execute('''
                UPDATE game_stats SET
                    enhancement_attempts = ?,
                    enhancement_successes = ?,
                    enhancement_failures = ?,
                    hunt_normal = ?,
                    hunt_special = ?,
                    hunt_boss = ?,
                    total_hunts = ?,
                    total_hunt_reward = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (attempts, successes, failures, normal, special, boss, total_hunts_val, total_reward, user_id))
        else:
            # 새로 생성 (None인 경우 0으로 설정)
            attempts = enhancement_attempts or 0
            successes = enhancement_successes or 0
            failures = enhancement_failures or 0
            normal = hunt_normal or 0
            special = hunt_special or 0
            boss = hunt_boss or 0
            total_hunts_val = total_hunts or 0
            total_reward = total_hunt_reward or 0
            
            cursor.execute('''
                INSERT INTO game_stats (
                    user_id, enhancement_attempts, enhancement_successes, enhancement_failures,
                    hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, attempts, successes, failures, normal, special, boss, total_hunts_val, total_reward))
        
        conn.commit()
        conn.close()
