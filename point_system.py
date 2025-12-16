import sqlite3
import os
from typing import Dict, Optional, Callable
from config import Config


class PointSystem:
    """골드 관리 시스템 (SQLite 사용)"""
    
    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or Config.POINTS_DATA_FILE
        self.point_callbacks: Dict[str, Callable[[str, int, str], None]] = {}
        self._init_database()
        self._migrate_from_json()
    
    def _init_database(self) -> None:
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 포인트 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points (
                user_id TEXT PRIMARY KEY,
                points INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 포인트 이력 테이블 생성 (선택사항)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_history (
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
        
        conn.commit()
        conn.close()
    
    def _migrate_from_json(self) -> None:
        """기존 JSON 파일에서 데이터 마이그레이션"""
        json_file = self.db_file.replace('.db', '.json')
        if os.path.exists(json_file):
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                if json_data:
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    
                    for user_id, points in json_data.items():
                        # 기존 데이터가 없을 때만 마이그레이션
                        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
                        if cursor.fetchone() is None:
                            cursor.execute(
                                'INSERT INTO points (user_id, points) VALUES (?, ?)',
                                (user_id, points)
                            )
                    
                    conn.commit()
                    conn.close()
                    
                    # 마이그레이션 완료 후 JSON 파일 백업
                    backup_file = json_file + '.backup'
                    if not os.path.exists(backup_file):
                        import shutil
                        shutil.copy2(json_file, backup_file)
                        print(f"✅ JSON 데이터를 SQLite로 마이그레이션했습니다. 원본 파일은 {backup_file}로 백업되었습니다.")
            except Exception as e:
                print(f"⚠️ JSON 마이그레이션 중 오류: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_points(self, user_id: str) -> int:
        """사용자 골드 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['points'] if result else 0
    
    def ensure_initial_points(self, user_id: str) -> bool:
        """사용자가 처음 접속한 경우 초기 골드 지급"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            conn.close()
            self.add_points(user_id, Config.INITIAL_POINTS, "신규 사용자 환영 골드")
            return True
        
        conn.close()
        return False
    
    def add_points(self, user_id: str, amount: int, reason: str = "") -> int:
        """골드 추가"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 기존 포인트 조회 또는 생성
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            new_points = result['points'] + amount
            cursor.execute(
                'UPDATE points SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (new_points, user_id)
            )
        else:
            new_points = amount
            cursor.execute(
                'INSERT INTO points (user_id, points) VALUES (?, ?)',
                (user_id, new_points)
            )
        
        # 이력 기록
        if reason:
            cursor.execute(
                'INSERT INTO point_history (user_id, amount, reason) VALUES (?, ?, ?)',
                (user_id, amount, reason)
            )
        
        conn.commit()
        conn.close()
        
        # 콜백 호출
        if 'add' in self.point_callbacks:
            self.point_callbacks['add'](user_id, amount, reason)
        
        return new_points
    
    def deduct_points(self, user_id: str, amount: int, reason: str = "") -> Optional[int]:
        """골드 차감 (잔액 부족 시 None 반환)"""
        current_points = self.get_points(user_id)
        
        if current_points < amount:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        new_points = current_points - amount
        cursor.execute(
            'UPDATE points SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
            (new_points, user_id)
        )
        
        # 이력 기록
        if reason:
            cursor.execute(
                'INSERT INTO point_history (user_id, amount, reason) VALUES (?, ?, ?)',
                (user_id, -amount, reason)
            )
        
        conn.commit()
        conn.close()
        
        # 콜백 호출
        if 'deduct' in self.point_callbacks:
            self.point_callbacks['deduct'](user_id, amount, reason)
        
        return new_points
    
    def set_points(self, user_id: str, amount: int) -> None:
        """골드 설정"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        amount = max(0, amount)
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                'UPDATE points SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (amount, user_id)
            )
        else:
            cursor.execute(
                'INSERT INTO points (user_id, points) VALUES (?, ?)',
                (user_id, amount)
            )
        
        conn.commit()
        conn.close()
    
    def has_points(self, user_id: str, amount: int) -> bool:
        """골드 보유 여부 확인"""
        return self.get_points(user_id) >= amount
    
    def register_callback(self, event_type: str, callback: Callable[[str, int, str], None]) -> None:
        """골드 이벤트 콜백 등록"""
        self.point_callbacks[event_type] = callback
    
    def transfer_points(self, from_user: str, to_user: str, amount: int, reason: str = "") -> Optional[int]:
        """골드 전송 (from_user → to_user)"""
        # 자기 자신에게 전송 불가
        if from_user == to_user:
            return None
        
        # 골드 확인
        if not self.has_points(from_user, amount):
            return None
        
        # 최소 전송 금액 체크
        if amount <= 0:
            return None
        
        # 골드 차감 및 추가
        deducted = self.deduct_points(from_user, amount, f"골드 전송 → {to_user}: {reason}")
        if deducted is None:
            return None
        
        result = self.add_points(to_user, amount, f"골드 수신 ← {from_user}: {reason}")
        return result
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """리더보드 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id, points FROM points ORDER BY points DESC LIMIT ?',
            (limit,)
        )
        results = cursor.fetchall()
        
        conn.close()
        return [(row['user_id'], row['points']) for row in results]
    
    def get_point_history(self, user_id: str, limit: int = 10) -> list:
        """골드 이력 조회 (새로운 기능)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT amount, reason, created_at 
               FROM point_history 
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
