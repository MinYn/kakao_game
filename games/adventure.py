import random
from typing import Optional
from games.base_game import Game
from config import Config


class MonsterType:
    """몬스터 타입 클래스"""
    
    def __init__(self, name: str, base_reward: int, reward_range: tuple, multiplier: float = None, 
                 name_pool: list = None, kill_messages: list = None):
        self.name = name  # 타입 이름 (일반몹, 특수몹, 보스몹)
        self.base_reward = base_reward
        self.reward_range = reward_range  # (최소, 최대) 기본 보상 범위
        self.multiplier = multiplier  # 레벨당 배율 (None이면 기본값 사용)
        self.name_pool = name_pool or []  # 랜덤 몬스터 이름 풀
        self.kill_messages = kill_messages or []  # 처치 메시지 풀


class AdventureGame(Game):
    """모험 게임 - 강화 + 몬스터 사냥 통합"""
    
    def __init__(self, user_id: str, point_system=None):
        super().__init__(user_id, point_system)
        self.max_level = None  # 최대 레벨 제한 없음
        self.current_level = 0
        self.enhancement_cost_base = Config.ENHANCEMENT_BASE_COST
        self.enhancement_cost_multiplier = Config.ENHANCEMENT_COST_MULTIPLIER
        self.sell_multiplier = Config.ENHANCEMENT_SELL_MULTIPLIER
        self.level_bonus = Config.ENHANCEMENT_LEVEL_BONUS
        
        # 몬스터 관련
        self.monster_types = self._init_monster_types()
        self.hunted_count = 0
        self.total_reward = 0
        self.hunt_stats = {'일반몹': 0, '특수몹': 0, '보스몹': 0}
        self.monster_names = {}  # 타입별 현재 선택된 몬스터 이름 저장
    
    def _init_monster_types(self) -> list:
        """몬스터 타입 초기화"""
        return [
            MonsterType(
                "일반몹", 30, (20, 50), 0.08,
                name_pool=["슬라임", "고블린", "오크", "좀비", "스켈레톤", "박쥐", "거미", "늑대", "쥐", "박쥐"],
                kill_messages=[
                    "{name}을(를) 처치했습니다!",
                    "{name}을(를) 물리쳤습니다!",
                    "{name}을(를) 제압했습니다!",
                    "{name}을(를) 쓰러뜨렸습니다!",
                    "{name}을(를) 격퇴했습니다!",
                    "{name}을(를) 무찔렀습니다!",
                ]
            ),
            MonsterType(
                "특수몹", 100, (80, 150), 0.12,
                name_pool=["오거", "트롤", "미노타우로스", "하피", "사이클롭스", "그리폰", "와이번", "히드라", "켄타우로스", "고르곤"],
                kill_messages=[
                    "{name}을(를) 처치했습니다!",
                    "{name}을(를) 물리쳤습니다!",
                    "{name}을(를) 제압했습니다!",
                    "{name}을(를) 쓰러뜨렸습니다!",
                    "{name}을(를) 격퇴했습니다!",
                    "{name}을(를) 무찔렀습니다!",
                    "{name}을(를) 완전히 제압했습니다!",
                    "{name}과(와)의 전투에서 승리했습니다!",
                ]
            ),
            MonsterType(
                "보스몹", 250, (200, 350), 0.15,
                name_pool=["드래곤", "데몬", "고대신", "리치", "발키리", "베헤모스", "레비아탄", "바알", "루시퍼", "크툴루"],
                kill_messages=[
                    "{name}을(를) 처치했습니다!",
                    "{name}을(를) 물리쳤습니다!",
                    "{name}을(를) 제압했습니다!",
                    "{name}을(를) 쓰러뜨렸습니다!",
                    "{name}을(를) 격퇴했습니다!",
                    "{name}을(를) 무찔렀습니다!",
                    "{name}을(를) 완전히 제압했습니다!",
                    "{name}과(와)의 전투에서 승리했습니다!",
                    "전설적인 {name}을(를) 쓰러뜨렸습니다!",
                    "{name}을(를) 영웅적으로 처치했습니다!",
                    "{name}과(와)의 치열한 전투 끝에 승리했습니다!",
                ]
            ),
        ]
    
    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        # DB에서 강화 레벨 및 통계 로드
        if self.point_system:
            self.current_level = self.point_system.get_enhancement_level(self.user_id)
            # 통계 로드
            stats = self.point_system.get_game_stats(self.user_id)
            self.game_data = {
                'level': self.current_level,
                'attempts': stats['enhancement_attempts'],
                'successes': stats['enhancement_successes'],
                'failures': stats['enhancement_failures'],
                'hunted_count': stats['total_hunts'],
                'total_reward': stats['total_hunt_reward'],
                'hunt_stats': {
                    '일반몹': stats['hunt_normal'],
                    '특수몹': stats['hunt_special'],
                    '보스몹': stats['hunt_boss']
                }
            }
            self.hunted_count = stats['total_hunts']
            self.total_reward = stats['total_hunt_reward']
            self.hunt_stats = self.game_data['hunt_stats'].copy()
        else:
            self.current_level = 0
            self.hunted_count = 0
            self.total_reward = 0
            self.hunt_stats = {'일반몹': 0, '특수몹': 0, '보스몹': 0}
            self.game_data = {
                'level': self.current_level,
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'hunted_count': 0,
                'total_reward': 0,
                'hunt_stats': self.hunt_stats
            }
        self.monster_names = {}
        
        boss_tickets = self._get_boss_tickets()
        
        return f"""⚔️ 모험 게임 시작!

현재 강화 레벨: +{self.current_level}
보스몹 입장권: {boss_tickets}장

명령어:
🔨 강화 관련:
- '강화' 또는 'enhance': 강화 시도
- '판매' 또는 'sell': 현재 아이템 판매
- '상태' 또는 'status': 현재 상태 확인

🗡️ 사냥 관련:
- '일반몹' 또는 'normal': 일반몹 사냥
- '특수몹' 또는 'special': 특수몹 사냥 (입장권 드랍 가능!)
- '보스몹' 또는 'boss': 보스몹 사냥 (입장권 필요)
- '입장권' 또는 'ticket': 입장권 확인

💡 강화 레벨이 높을수록 몬스터 사냥 보상이 증가합니다!
💡 특수몹을 잡으면 보스몹 입장권을 드랍할 수 있습니다!"""
    
    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '시작' 명령을 사용하세요."
        
        command = command.strip().lower()
        
        if command in ['종료', 'quit', 'exit']:
            return self.end()
        
        # 강화 관련 명령
        if command in ['상태', 'status', 'info']:
            return self._get_status()
        
        if command in ['강화', 'enhance', '강화하기']:
            return self._enhance()
        
        if command in ['판매', 'sell', '팔기']:
            return self._sell()
        
        # 몬스터 사냥 관련 명령
        if command in ['입장권', 'ticket', 'tickets', 't']:
            return self._show_tickets()
        
        if command in ['일반몹', 'normal', 'n', '1']:
            return self._hunt_monster('일반몹')
        if command in ['특수몹', 'special', 's', '2']:
            return self._hunt_monster('특수몹')
        if command in ['보스몹', 'boss', 'b', '3']:
            return self._hunt_monster('보스몹')
        
        return f"알 수 없는 명령입니다.\n사용 가능한 명령: '강화', '판매', '일반몹', '특수몹', '보스몹', '입장권', '상태', '종료'"
    
    # ========== 강화 관련 메서드 ==========
    
    def _calculate_cost(self) -> int:
        """강화 비용 계산"""
        cost = int(self.enhancement_cost_base * (self.enhancement_cost_multiplier ** self.current_level))
        return max(cost, 10)  # 최소 10G
    
    def _calculate_success_rate(self) -> float:
        """성공 확률 계산"""
        base_rate = 100 - (self.current_level * 6)
        return max(base_rate, 10)  # 최소 10%
    
    def _calculate_sell_price(self) -> int:
        """판매 가격 계산"""
        if self.current_level == 0:
            return 0
        
        total_invested = 0
        for level in range(self.current_level):
            level_cost = int(self.enhancement_cost_base * (self.enhancement_cost_multiplier ** level))
            total_invested += max(level_cost, 10)
        
        sell_price = int(total_invested * self.sell_multiplier)
        level_bonus_amount = self.current_level * self.level_bonus
        sell_price += level_bonus_amount
        
        if self.current_level >= 10:
            sell_price += int(sell_price * 0.2)
        elif self.current_level >= 5:
            sell_price += int(sell_price * 0.1)
        
        return max(sell_price, 10)
    
    def _enhance(self) -> str:
        """강화 시도"""
        cost = self._calculate_cost()
        
        if not self.point_system or not self.point_system.has_points(self.user_id, cost):
            return f"❌ 강화에 필요한 골드가 부족합니다.\n필요 골드: {cost}G\n현재 골드: {self.get_user_points()}G"
        
        self.deduct_points(cost, f"강화 시도 (+{self.current_level} → +{self.current_level + 1})")
        
        self.game_data['attempts'] = self.game_data.get('attempts', 0) + 1
        # DB에 강화 시도 저장
        if self.point_system:
            self.point_system.update_game_stats(
                user_id=self.user_id,
                enhancement_attempts=1
            )
        
        success_rate = self._calculate_success_rate()
        is_success = random.random() * 100 < success_rate
        
        if is_success:
            self.current_level += 1
            self.game_data['level'] = self.current_level
            self.game_data['successes'] = self.game_data.get('successes', 0) + 1
            # DB에 강화 레벨 및 성공 저장
            if self.point_system:
                self.point_system.set_enhancement_level(self.user_id, self.current_level)
                self.point_system.update_game_stats(
                    user_id=self.user_id,
                    enhancement_successes=1
                )
            
            next_cost = self._calculate_cost()
            result = f"""✅ 강화 성공!

+{self.current_level} 강화 완료!
다음 강화 비용: {next_cost}G
현재 골드: {self.get_user_points()}G

💡 강화 레벨이 높을수록 몬스터 사냥 보상이 증가합니다!"""
        else:
            self.game_data['failures'] = self.game_data.get('failures', 0) + 1
            # DB에 강화 실패 저장
            if self.point_system:
                self.point_system.update_game_stats(
                    user_id=self.user_id,
                    enhancement_failures=1
                )
            
            if self.current_level > 0:
                self.current_level -= 1
                self.game_data['level'] = self.current_level
                # DB에 강화 레벨 저장
                if self.point_system:
                    self.point_system.set_enhancement_level(self.user_id, self.current_level)
                result = f"""❌ 강화 실패...

+{self.current_level + 1} → +{self.current_level} (레벨 하락)
현재 골드: {self.get_user_points()}G

다시 시도해보세요!"""
            else:
                result = f"""❌ 강화 실패...

레벨 변화 없음 (+{self.current_level})
현재 골드: {self.get_user_points()}G

다시 시도해보세요!"""
        
        return result
    
    def _sell(self) -> str:
        """아이템 판매"""
        if self.current_level == 0:
            return "❌ 판매할 아이템이 없습니다.\n강화 레벨이 0인 아이템은 판매할 수 없습니다."
        
        sell_price = self._calculate_sell_price()
        sold_level = self.current_level
        
        if self.point_system:
            self.award_points(sell_price, f"강화 아이템 판매 (+{sold_level})")
        
        self.current_level = 0
        self.game_data['level'] = 0
        # DB에 강화 레벨 저장 (0으로 리셋)
        if self.point_system:
            self.point_system.set_enhancement_level(self.user_id, 0)
        
        return f"""💰 아이템 판매 완료!

판매한 아이템: +{sold_level}
판매 가격: {sell_price}P
현재 골드: {self.get_user_points()}G

새로운 아이템으로 다시 시작하세요!"""
    
    # ========== 몬스터 사냥 관련 메서드 ==========
    
    def _get_monster_type(self, name: str) -> Optional[MonsterType]:
        """몬스터 타입 찾기"""
        name_lower = name.lower()
        for mt in self.monster_types:
            if (name_lower == mt.name.lower() or 
                name_lower in ['normal', 'n', '1'] and mt.name == '일반몹' or
                name_lower in ['special', 's', '2'] and mt.name == '특수몹' or
                name_lower in ['boss', 'b', '3'] and mt.name == '보스몹'):
                return mt
        return None
    
    def _get_monster_name(self, monster_type: MonsterType) -> str:
        """몬스터 이름 가져오기 (랜덤 선택)"""
        if monster_type.name not in self.monster_names:
            if monster_type.name_pool:
                self.monster_names[monster_type.name] = random.choice(monster_type.name_pool)
            else:
                self.monster_names[monster_type.name] = monster_type.name
        return self.monster_names[monster_type.name]
    
    def _get_kill_message(self, monster_type: MonsterType, monster_name: str) -> str:
        """처치 메시지 가져오기 (랜덤 선택)"""
        if monster_type.kill_messages:
            message_template = random.choice(monster_type.kill_messages)
            return message_template.format(name=monster_name)
        return f"{monster_name}을(를) 처치했습니다!"
    
    def _calculate_reward(self, monster_type: MonsterType) -> int:
        """강화 레벨에 따른 보상 계산"""
        min_reward, max_reward = monster_type.reward_range
        base_reward = random.randint(min_reward, max_reward)
        
        multiplier = monster_type.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
        reward_multiplier = 1.0 + (self.current_level * multiplier)
        
        final_reward = int(base_reward * reward_multiplier)
        return max(final_reward, base_reward)
    
    def _get_boss_tickets(self) -> int:
        """보스몹 입장권 조회"""
        if self.point_system:
            return self.point_system.get_boss_tickets(self.user_id)
        return 0
    
    def _add_boss_ticket(self, amount: int = 1) -> int:
        """보스몹 입장권 추가"""
        if self.point_system:
            return self.point_system.add_boss_ticket(self.user_id, amount, "특수몹 사냥 보상")
        return 0
    
    def _use_boss_ticket(self, amount: int = 1) -> bool:
        """보스몹 입장권 사용"""
        if self.point_system:
            return self.point_system.use_boss_ticket(self.user_id, amount, "보스몹 사냥")
        return False
    
    def _hunt_monster(self, monster_type_name: str) -> str:
        """몬스터 사냥"""
        monster_type = self._get_monster_type(monster_type_name)
        
        if monster_type is None:
            return f"❌ '{monster_type_name}' 몬스터 타입을 찾을 수 없습니다.\n사용 가능: 일반몹, 특수몹, 보스몹"
        
        # 보스몹은 입장권 확인
        if monster_type.name == '보스몹':
            if not self._use_boss_ticket():
                tickets = self._get_boss_tickets()
                return f"""❌ 보스몹 입장권이 필요합니다!

현재 보유 입장권: {tickets}장
💡 특수몹을 잡으면 입장권을 드랍할 수 있습니다!"""
        
        monster_name = self._get_monster_name(monster_type)
        
        # 강화 레벨이 높을수록 성공 확률 증가
        base_success_rate = 70
        level_bonus = self.current_level * 2
        success_rate = min(base_success_rate + level_bonus, 95)
        
        is_success = random.random() * 100 < success_rate
        
        if is_success:
            reward = self._calculate_reward(monster_type)
            
            if self.point_system:
                self.award_points(reward, f"{monster_type.name} 사냥 성공 ({monster_name})")
            
            self.hunted_count += 1
            self.total_reward += reward
            self.hunt_stats[monster_type.name] = self.hunt_stats.get(monster_type.name, 0) + 1
            self.game_data['hunted_count'] = self.hunted_count
            self.game_data['total_reward'] = self.total_reward
            self.game_data['hunt_stats'] = self.hunt_stats
            
            # DB에 사냥 통계 저장
            if self.point_system:
                hunt_type_map = {
                    '일반몹': 'hunt_normal',
                    '특수몹': 'hunt_special',
                    '보스몹': 'hunt_boss'
                }
                update_params = {
                    'user_id': self.user_id,
                    'total_hunts': 1,
                    'total_hunt_reward': reward
                }
                update_params[hunt_type_map[monster_type.name]] = 1
                self.point_system.update_game_stats(**update_params)
            
            multiplier = monster_type.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
            multiplier_percent = multiplier * 100
            kill_message = self._get_kill_message(monster_type, monster_name)
            
            result_lines = [
                f"✅ 사냥 성공!",
                f"",
                kill_message,
                f"💰 골드 +{reward}G 획득! (강화 레벨 +{self.current_level}, 배율 {multiplier_percent:.1f}%)",
                f""
            ]
            
            # 특수몹 사냥 시 입장권 드랍
            if monster_type.name == '특수몹':
                if random.random() < Config.BOSS_TICKET_DROP_RATE:
                    new_tickets = self._add_boss_ticket()
                    result_lines.append(f"🎫 보스몹 입장권 획득! (현재: {new_tickets}장)")
                    result_lines.append("")
            
            result_lines.extend([
                f"사냥 통계:",
                f"- 일반몹: {self.hunt_stats.get('일반몹', 0)}마리",
                f"- 특수몹: {self.hunt_stats.get('특수몹', 0)}마리",
                f"- 보스몹: {self.hunt_stats.get('보스몹', 0)}마리",
                f"총 사냥: {self.hunted_count}마리",
                f"총 획득 골드: {self.total_reward}G",
                f"현재 골드: {self.get_user_points()}G"
            ])
            
            return "\n".join(result_lines)
        else:
            fail_messages = [
                f"{monster_name}에게 도망쳤습니다.",
                f"{monster_name}이(가) 도망갔습니다.",
                f"{monster_name}을(를) 놓쳤습니다.",
                f"{monster_name}과(와)의 전투에서 후퇴했습니다.",
            ]
            fail_message = random.choice(fail_messages)
            
            return f"""❌ 사냥 실패...

{fail_message}
다시 시도해보세요!

💡 강화 레벨을 높이면 성공 확률이 증가합니다.
현재 성공 확률: {success_rate:.1f}%"""
    
    def _show_tickets(self) -> str:
        """입장권 확인"""
        tickets = self._get_boss_tickets()
        drop_rate_percent = Config.BOSS_TICKET_DROP_RATE * 100
        
        return f"""🎫 보스몹 입장권 현황

보유 입장권: {tickets}장

💡 특수몹을 잡으면 {drop_rate_percent:.0f}% 확률로 입장권을 드랍합니다!
💡 보스몹은 입장권 1장을 소모하여 사냥할 수 있습니다!"""
    
    def _get_status(self) -> str:
        """현재 상태 조회"""
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        tickets = self._get_boss_tickets()
        
        status = f"""📊 현재 상태

🔨 강화 정보:
- 강화 레벨: +{self.current_level}
- 다음 강화 비용: {cost}G
- 성공 확률: {success_rate:.1f}%
- 판매 가격: {sell_price}G

🗡️ 사냥 정보:
- 보상 배율: {1.0 + (self.current_level * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.2f}배
- 보스몹 입장권: {tickets}장

📈 통계:
- 강화 시도: {self.game_data.get('attempts', 0)}회
- 강화 성공: {self.game_data.get('successes', 0)}회
- 강화 실패: {self.game_data.get('failures', 0)}회
- 일반몹: {self.hunt_stats.get('일반몹', 0)}마리
- 특수몹: {self.hunt_stats.get('특수몹', 0)}마리
- 보스몹: {self.hunt_stats.get('보스몹', 0)}마리
- 총 사냥: {self.hunted_count}마리
- 총 획득 골드: {self.total_reward}G
- 현재 골드: {self.get_user_points()}G
"""
        return status
    
    def end(self) -> str:
        """게임 종료"""
        level = self.current_level
        attempts = self.game_data.get('attempts', 0)
        successes = self.game_data.get('successes', 0)
        failures = self.game_data.get('failures', 0)
        hunted = self.hunted_count
        reward = self.total_reward
        stats = self.hunt_stats.copy()
        
        # 게임 종료 시 최종 통계를 DB에 동기화
        if self.point_system:
            self.point_system.set_game_stats(
                user_id=self.user_id,
                enhancement_attempts=attempts,
                enhancement_successes=successes,
                enhancement_failures=failures,
                hunt_normal=stats.get('일반몹', 0),
                hunt_special=stats.get('특수몹', 0),
                hunt_boss=stats.get('보스몹', 0),
                total_hunts=hunted,
                total_hunt_reward=reward
            )
        
        self.is_active = False
        self.game_data.clear()
        
        return f"""게임이 종료되었습니다.

🔨 강화:
- 최종 강화 레벨: +{level}
- 총 시도 횟수: {attempts}
- 성공 횟수: {successes}
- 실패 횟수: {failures}

🗡️ 사냥:
- 일반몹: {stats.get('일반몹', 0)}마리
- 특수몹: {stats.get('특수몹', 0)}마리
- 보스몹: {stats.get('보스몹', 0)}마리
- 총 사냥: {hunted}마리
- 총 획득 골드: {reward}G"""
    
    def get_help(self) -> str:
        """도움말"""
        drop_rate = Config.BOSS_TICKET_DROP_RATE * 100
        return f"""모험 게임 도움말 (강화 + 몬스터 사냥):

🔨 강화 관련:
- 강화 시도: '강화' 또는 'enhance'
- 아이템 판매: '판매' 또는 'sell'
- 상태 확인: '상태' 또는 'status'

🗡️ 사냥 관련:
- 일반몹 사냥: '일반몹', 'normal', 'n', '1'
- 특수몹 사냥: '특수몹', 'special', 's', '2'
- 보스몹 사냥: '보스몹', 'boss', 'b', '3'
- 입장권 확인: '입장권', 'ticket', 't'

규칙:
- 강화 레벨이 높을수록 몬스터 사냥 보상이 증가합니다!
- 일반몹: 기본 보상 20~50G, 레벨당 +8% 증가
- 특수몹: 기본 보상 80~150G, 레벨당 +12% 증가, {drop_rate:.0f}% 확률로 보스몹 입장권 드랍
- 보스몹: 기본 보상 200~350G, 레벨당 +15% 증가, 입장권 1장 필요
- 강화 레벨이 높을수록 사냥 성공 확률이 증가합니다 (레벨당 +2%)"""

