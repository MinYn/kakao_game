"""
PostgreSQL + Kafka 기반 골드 관리 시스템
"""
from typing import Dict, Optional, Callable
from db.postgres import PostgreSQLManager
from events.kafka_producer import publish_event
from events.event_types import (
    EventType, EventTopics, create_gold_event
)
from config import Config
import logging

logger = logging.getLogger(__name__)


class GoldSystemPostgres:
    """골드 관리 시스템 (PostgreSQL + Kafka 사용)"""
    
    def __init__(self):
        PostgreSQLManager.initialize()
        self.gold_callbacks: Dict[str, Callable[[str, int, str], None]] = {}
    
    def get_gold(self, user_id: str) -> int:
        """사용자 골드 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def ensure_initial_gold(self, user_id: str) -> bool:
        """사용자가 처음 접속한 경우 초기 골드 지급"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result is None:
                    # 신규 사용자 - 골드 지급
                    self.add_gold(user_id, Config.INITIAL_GOLD, "신규 사용자 환영 골드")
                    return True
                
                return False
    
    def add_gold(self, user_id: str, amount: int, reason: str = "") -> int:
        """골드 추가"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                # 기존 골드 조회 또는 생성
                cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    new_gold = result[0] + amount
                    cursor.execute(
                        'UPDATE gold SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                        (new_gold, user_id)
                    )
                else:
                    new_gold = amount
                    cursor.execute(
                        'INSERT INTO gold (user_id, gold) VALUES (%s, %s)',
                        (user_id, new_gold)
                    )
                
                # 이력 기록 (비동기로 Kafka로 발행)
                if reason:
                    cursor.execute(
                        'INSERT INTO gold_history (user_id, amount, reason) VALUES (%s, %s, %s)',
                        (user_id, amount, reason)
                    )
                
                conn.commit()
        
        # Kafka 이벤트 발행 (비동기)
        if Config.USE_KAFKA:
            event = create_gold_event(
                EventType.GOLD_ADDED,
                user_id,
                amount,
                reason,
                {'new_balance': new_gold}
            )
            publish_event(EventTopics.GOLD_EVENTS, event, key=user_id)
        
        # 콜백 호출
        if 'add' in self.gold_callbacks:
            try:
                self.gold_callbacks['add'](user_id, amount, reason)
            except Exception as e:
                logger.error(f"Gold callback error: {e}")
        
        return new_gold
    
    def deduct_gold(self, user_id: str, amount: int, reason: str = "") -> Optional[int]:
        """골드 차감 (잔액 부족 시 None 반환)"""
        current_gold = self.get_gold(user_id)
        
        if current_gold < amount:
            return None
        
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                new_gold = current_gold - amount
                cursor.execute(
                    'UPDATE gold SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                    (new_gold, user_id)
                )
                
                # 이력 기록
                if reason:
                    cursor.execute(
                        'INSERT INTO gold_history (user_id, amount, reason) VALUES (%s, %s, %s)',
                        (user_id, -amount, reason)
                    )
                
                conn.commit()
        
        # Kafka 이벤트 발행
        if Config.USE_KAFKA:
            event = create_gold_event(
                EventType.GOLD_DEDUCTED,
                user_id,
                amount,
                reason,
                {'new_balance': new_gold}
            )
            publish_event(EventTopics.GOLD_EVENTS, event, key=user_id)
        
        # 콜백 호출
        if 'deduct' in self.gold_callbacks:
            try:
                self.gold_callbacks['deduct'](user_id, amount, reason)
            except Exception as e:
                logger.error(f"Gold callback error: {e}")
        
        return new_gold
    
    def set_gold(self, user_id: str, amount: int) -> None:
        """골드 설정"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                amount = max(0, amount)
                cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    cursor.execute(
                        'UPDATE gold SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                        (amount, user_id)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO gold (user_id, gold) VALUES (%s, %s)',
                        (user_id, amount)
                    )
                
                conn.commit()
    
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
        
        # 트랜잭션으로 처리
        with PostgreSQLManager.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    # 차감
                    cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (from_user,))
                    from_result = cursor.fetchone()
                    if not from_result or from_result[0] < amount:
                        return None
                    
                    new_from_gold = from_result[0] - amount
                    cursor.execute(
                        'UPDATE gold SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                        (new_from_gold, from_user)
                    )
                    
                    # 추가
                    cursor.execute('SELECT gold FROM gold WHERE user_id = %s', (to_user,))
                    to_result = cursor.fetchone()
                    
                    if to_result:
                        new_to_gold = to_result[0] + amount
                        cursor.execute(
                            'UPDATE gold SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                            (new_to_gold, to_user)
                        )
                    else:
                        new_to_gold = amount
                        cursor.execute(
                            'INSERT INTO gold (user_id, gold) VALUES (%s, %s)',
                            (to_user, new_to_gold)
                        )
                    
                    # 이력 기록
                    cursor.execute(
                        'INSERT INTO gold_history (user_id, amount, reason) VALUES (%s, %s, %s)',
                        (from_user, -amount, f"골드 전송 → {to_user}: {reason}")
                    )
                    cursor.execute(
                        'INSERT INTO gold_history (user_id, amount, reason) VALUES (%s, %s, %s)',
                        (to_user, amount, f"골드 수신 ← {from_user}: {reason}")
                    )
                    
                    conn.commit()
                    
                    # Kafka 이벤트 발행
                    if Config.USE_KAFKA:
                        event = create_gold_event(
                            EventType.GOLD_TRANSFERRED,
                            from_user,
                            amount,
                            reason,
                            {
                                'to_user': to_user,
                                'from_balance': new_from_gold,
                                'to_balance': new_to_gold
                            }
                        )
                        publish_event(EventTopics.GOLD_EVENTS, event, key=from_user)
                    
                    return new_to_gold
            except Exception as e:
                conn.rollback()
                logger.error(f"Gold transfer failed: {e}")
                return None
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """리더보드 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT user_id, gold FROM gold ORDER BY gold DESC LIMIT %s',
                    (limit,)
                )
                results = cursor.fetchall()
                return [(row[0], row[1]) for row in results]
    
    def get_gold_history(self, user_id: str, limit: int = 10) -> list:
        """골드 이력 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''SELECT amount, reason, created_at 
                       FROM gold_history 
                       WHERE user_id = %s 
                       ORDER BY created_at DESC 
                       LIMIT %s''',
                    (user_id, limit)
                )
                results = cursor.fetchall()
                return [
                    {
                        'amount': row[0],
                        'reason': row[1],
                        'created_at': row[2]
                    }
                    for row in results
                ]

    def add_ship_to_collection(self, user_id: str, ship_id: str) -> dict:
        """우주선 도감에 함선 추가. 중복 획득 시 카운트만 증가."""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO ship_collection (user_id, ship_id, acquired_count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (user_id, ship_id)
                    DO UPDATE SET
                        acquired_count = ship_collection.acquired_count + 1,
                        last_acquired_at = CURRENT_TIMESTAMP
                    RETURNING acquired_count
                    ''',
                    (user_id, ship_id),
                )
                new_count = cursor.fetchone()[0]
                conn.commit()
                return {'ship_id': ship_id, 'is_new': new_count == 1, 'count': new_count}

    def get_ship_collection(self, user_id: str) -> list[dict]:
        """사용자 우주선 도감 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT ship_id, acquired_count, first_acquired_at, last_acquired_at
                    FROM ship_collection
                    WHERE user_id = %s
                    ORDER BY first_acquired_at ASC
                    ''',
                    (user_id,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        'ship_id': row[0],
                        'count': row[1],
                        'first_acquired_at': row[2],
                        'last_acquired_at': row[3],
                    }
                    for row in rows
                ]
    
    def get_boss_tickets(self, user_id: str) -> int:
        """보스몹 입장권 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT tickets FROM boss_tickets WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def add_boss_ticket(self, user_id: str, amount: int = 1, reason: str = "") -> int:
        """보스몹 입장권 추가"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT tickets FROM boss_tickets WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    new_tickets = result[0] + amount
                    cursor.execute(
                        'UPDATE boss_tickets SET tickets = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                        (new_tickets, user_id)
                    )
                else:
                    new_tickets = amount
                    cursor.execute(
                        'INSERT INTO boss_tickets (user_id, tickets) VALUES (%s, %s)',
                        (user_id, new_tickets)
                    )
                
                conn.commit()
                return new_tickets
    
    def use_boss_ticket(self, user_id: str, amount: int = 1, reason: str = "") -> bool:
        """보스몹 입장권 사용 (잔액 부족 시 False 반환)"""
        current_tickets = self.get_boss_tickets(user_id)
        
        if current_tickets < amount:
            return False
        
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                new_tickets = current_tickets - amount
                cursor.execute(
                    'UPDATE boss_tickets SET tickets = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                    (new_tickets, user_id)
                )
                conn.commit()
                return True
    
    def get_enhancement_level(self, user_id: str) -> int:
        """강화 레벨 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT level FROM enhancement_levels WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def set_enhancement_level(self, user_id: str, level: int) -> None:
        """강화 레벨 설정"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                level = max(0, level)
                cursor.execute('SELECT level FROM enhancement_levels WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    cursor.execute(
                        'UPDATE enhancement_levels SET level = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s',
                        (level, user_id)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO enhancement_levels (user_id, level) VALUES (%s, %s)',
                        (user_id, level)
                    )
                
                conn.commit()
    
    def get_game_stats(self, user_id: str) -> dict:
        """게임 통계 조회"""
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT enhancement_attempts, enhancement_successes, enhancement_failures,
                           hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward
                    FROM game_stats WHERE user_id = %s
                ''', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'enhancement_attempts': result[0],
                        'enhancement_successes': result[1],
                        'enhancement_failures': result[2],
                        'hunt_normal': result[3],
                        'hunt_special': result[4],
                        'hunt_boss': result[5],
                        'total_hunts': result[6],
                        'total_hunt_reward': result[7]
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
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM game_stats WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    new_attempts = result[1] + enhancement_attempts
                    new_successes = result[2] + enhancement_successes
                    new_failures = result[3] + enhancement_failures
                    new_normal = result[4] + hunt_normal
                    new_special = result[5] + hunt_special
                    new_boss = result[6] + hunt_boss
                    new_total_hunts = result[7] + total_hunts
                    new_total_reward = result[8] + total_hunt_reward
                    
                    cursor.execute('''
                        UPDATE game_stats SET
                            enhancement_attempts = %s,
                            enhancement_successes = %s,
                            enhancement_failures = %s,
                            hunt_normal = %s,
                            hunt_special = %s,
                            hunt_boss = %s,
                            total_hunts = %s,
                            total_hunt_reward = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    ''', (new_attempts, new_successes, new_failures, new_normal, new_special,
                          new_boss, new_total_hunts, new_total_reward, user_id))
                else:
                    cursor.execute('''
                        INSERT INTO game_stats (
                            user_id, enhancement_attempts, enhancement_successes, enhancement_failures,
                            hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (user_id, enhancement_attempts, enhancement_successes, enhancement_failures,
                          hunt_normal, hunt_special, hunt_boss, total_hunts, total_hunt_reward))
                
                conn.commit()
                
                # Kafka 이벤트 발행
                if Config.USE_KAFKA:
                    from events.event_types import create_stats_event
                    event = create_stats_event(
                        user_id,
                        'game_stats',
                        {
                            'enhancement_attempts': enhancement_attempts,
                            'enhancement_successes': enhancement_successes,
                            'enhancement_failures': enhancement_failures,
                            'hunt_normal': hunt_normal,
                            'hunt_special': hunt_special,
                            'hunt_boss': hunt_boss,
                            'total_hunts': total_hunts,
                            'total_hunt_reward': total_hunt_reward
                        }
                    )
                    publish_event(EventTopics.STATS_EVENTS, event, key=user_id)
    
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
        with PostgreSQLManager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM game_stats WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    attempts = enhancement_attempts if enhancement_attempts is not None else result[1]
                    successes = enhancement_successes if enhancement_successes is not None else result[2]
                    failures = enhancement_failures if enhancement_failures is not None else result[3]
                    normal = hunt_normal if hunt_normal is not None else result[4]
                    special = hunt_special if hunt_special is not None else result[5]
                    boss = hunt_boss if hunt_boss is not None else result[6]
                    total_hunts_val = total_hunts if total_hunts is not None else result[7]
                    total_reward = total_hunt_reward if total_hunt_reward is not None else result[8]
                    
                    cursor.execute('''
                        UPDATE game_stats SET
                            enhancement_attempts = %s,
                            enhancement_successes = %s,
                            enhancement_failures = %s,
                            hunt_normal = %s,
                            hunt_special = %s,
                            hunt_boss = %s,
                            total_hunts = %s,
                            total_hunt_reward = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    ''', (attempts, successes, failures, normal, special, boss, total_hunts_val, total_reward, user_id))
                else:
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
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (user_id, attempts, successes, failures, normal, special, boss, total_hunts_val, total_reward))
                
                conn.commit()
