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


class MonsterHuntGame(Game):
    """몬스터 사냥 게임"""
    
    def __init__(self, user_id: str, point_system=None, enhancement_level: int = 0):
        super().__init__(user_id, point_system)
        self.enhancement_level = enhancement_level  # 강화 게임에서 가져온 레벨
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
    
    def _calculate_reward(self, monster_type: MonsterType) -> int:
        """강화 레벨에 따른 보상 계산"""
        # 기본 보상 범위에서 랜덤 선택
        min_reward, max_reward = monster_type.reward_range
        base_reward = random.randint(min_reward, max_reward)
        
        # 강화 레벨에 따른 배율 적용
        multiplier = monster_type.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
        reward_multiplier = 1.0 + (self.enhancement_level * multiplier)
        
        # 최종 보상 계산
        final_reward = int(base_reward * reward_multiplier)
        
        return max(final_reward, base_reward)  # 최소 기본 보상은 보장
    
    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.hunted_count = 0
        self.total_reward = 0
        self.hunt_stats = {'일반몹': 0, '특수몹': 0, '보스몹': 0}
        self.monster_names = {}  # 몬스터 이름 초기화
        self.game_data = {
            'enhancement_level': self.enhancement_level,
            'hunted_count': 0,
            'total_reward': 0,
            'hunt_stats': self.hunt_stats,
            'monster_names': self.monster_names
        }
        
        boss_tickets = self._get_boss_tickets()
        
        return f"""🗡️ 몬스터 사냥 게임 시작!

현재 강화 레벨: +{self.enhancement_level}
보스몹 입장권: {boss_tickets}장

명령어:
- '일반몹' 또는 'normal': 일반몹 사냥
- '특수몹' 또는 'special': 특수몹 사냥 (입장권 드랍 가능!)
- '보스몹' 또는 'boss': 보스몹 사냥 (입장권 필요)
- '입장권' 또는 'ticket': 입장권 확인
- '상태' 또는 'status': 현재 상태 확인
- '강화레벨' 또는 'level': 강화 레벨 확인
- '종료': 게임 종료

💡 강화 레벨이 높을수록 보상이 배율로 증가합니다!
💡 특수몹을 잡으면 보스몹 입장권을 드랍할 수 있습니다!
💡 보스몹은 입장권이 있어야만 사냥할 수 있습니다!
💡 매번 다른 몬스터를 만날 수 있습니다!"""
    
    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '시작' 명령을 사용하세요."
        
        command = command.strip().lower()
        
        if command in ['종료', 'quit', 'exit']:
            return self.end()
        
        if command in ['상태', 'status', 'info']:
            return self._get_status()
        
        if command in ['강화레벨', '레벨', 'level', 'l']:
            return self._show_enhancement_level()
        
        if command in ['입장권', 'ticket', 'tickets', 't']:
            return self._show_tickets()
        
        # 몬스터 타입별 사냥
        if command in ['일반몹', 'normal', 'n', '1']:
            return self._hunt_monster('일반몹')
        if command in ['특수몹', 'special', 's', '2']:
            return self._hunt_monster('특수몹')
        if command in ['보스몹', 'boss', 'b', '3']:
            return self._hunt_monster('보스몹')
        
        return f"알 수 없는 명령입니다.\n사용 가능한 명령: '일반몹', '특수몹', '보스몹', '입장권', '상태', '강화레벨', '종료'"
    
    def _get_available_monster_types(self) -> list:
        """사냥 가능한 몬스터 타입 목록 (모두 가능)"""
        return self.monster_types
    
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
        """몬스터 이름 가져오기 (랜덤 선택, 같은 세션에서는 동일한 이름 유지)"""
        if monster_type.name not in self.monster_names:
            # 새로운 몬스터 타입이면 랜덤 이름 선택
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
        # 몬스터 타입 찾기
        monster_type = self._get_monster_type(monster_type_name)
        
        if monster_type is None:
            return f"❌ '{monster_type_name}' 몬스터 타입을 찾을 수 없습니다.\n사용 가능: 일반몹, 특수몹, 보스몹"
        
        # 보스몹은 입장권 확인
        if monster_type.name == '보스몹':
            if not self._use_boss_ticket():
                tickets = self._get_boss_tickets()
                return f"""❌ 보스몹 입장권이 필요합니다!

현재 보유 입장권: {tickets}장
💡 특수몹을 잡으면 입장권을 드랍할 수 있습니다!
💡 입장권 확인: '입장권' 또는 'ticket'"""
        
        # 몬스터 사냥 시뮬레이션
        # 강화 레벨이 높을수록 성공 확률 증가
        base_success_rate = 70  # 기본 성공률
        level_bonus = self.enhancement_level * 2  # 레벨당 2% 보너스
        success_rate = min(base_success_rate + level_bonus, 95)  # 최대 95%
        
        is_success = random.random() * 100 < success_rate
        
        # 몬스터 이름 가져오기
        monster_name = self._get_monster_name(monster_type)
        
        if is_success:
            # 사냥 성공 - 강화 레벨에 따른 보상 계산
            reward = self._calculate_reward(monster_type)
            
            if self.point_system:
                self.award_gold(reward, f"{monster_type.name} 사냥 성공 ({monster_name})")
            
            self.hunted_count += 1
            self.total_reward += reward
            self.hunt_stats[monster_type.name] = self.hunt_stats.get(monster_type.name, 0) + 1
            self.game_data['hunted_count'] = self.hunted_count
            self.game_data['total_reward'] = self.total_reward
            self.game_data['hunt_stats'] = self.hunt_stats
            
            # 배율 정보 표시
            multiplier = monster_type.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
            multiplier_percent = multiplier * 100
            
            # 처치 메시지 랜덤 선택
            kill_message = self._get_kill_message(monster_type, monster_name)
            
            result_lines = [
                f"✅ 사냥 성공!",
                f"",
                kill_message,
                f"💰 골드 +{reward}G 획득! (강화 레벨 +{self.enhancement_level}, 배율 {multiplier_percent:.1f}%)",
                f""
            ]
            
            # 특수몹 사냥 시 입장권 드랍 체크
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
            # 사냥 실패
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
    
    def _show_enhancement_level(self) -> str:
        """강화 레벨 표시"""
        result = [f"🔨 현재 강화 레벨: +{self.enhancement_level}\n"]
        result.append("몬스터 타입별 예상 보상:")
        
        for mt in self.monster_types:
            # 예상 보상 계산 (최소/최대)
            multiplier = mt.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
            reward_multiplier = 1.0 + (self.enhancement_level * multiplier)
            
            min_base, max_base = mt.reward_range
            min_reward = int(min_base * reward_multiplier)
            max_reward = int(max_base * reward_multiplier)
            
            multiplier_percent = multiplier * 100
            result.append(f"  ✅ {mt.name} - 보상: {min_reward}~{max_reward}G (레벨당 +{multiplier_percent:.1f}%)")
        
        result.append(f"\n💡 강화 레벨이 높을수록 보상이 배율로 증가합니다!")
        result.append(f"💡 현재 레벨 +{self.enhancement_level}에서는 기본 보상의 {1.0 + (self.enhancement_level * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.1f}배를 받습니다!")
        
        return "\n".join(result)
    
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
        tickets = self._get_boss_tickets()
        status = f"""📊 현재 상태

강화 레벨: +{self.enhancement_level}
보상 배율: {1.0 + (self.enhancement_level * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.2f}배
보스몹 입장권: {tickets}장

사냥 통계:
- 일반몹: {self.hunt_stats.get('일반몹', 0)}마리
- 특수몹: {self.hunt_stats.get('특수몹', 0)}마리
- 보스몹: {self.hunt_stats.get('보스몹', 0)}마리
총 사냥: {self.hunted_count}마리
총 획득 골드: {self.total_reward}G
현재 골드: {self.get_user_points()}G
"""
        return status
    
    def end(self) -> str:
        """게임 종료"""
        hunted = self.hunted_count
        reward = self.total_reward
        stats = self.hunt_stats.copy()
        
        self.is_active = False
        self.game_data.clear()
        
        return f"""게임이 종료되었습니다.

사냥 통계:
- 일반몹: {stats.get('일반몹', 0)}마리
- 특수몹: {stats.get('특수몹', 0)}마리
- 보스몹: {stats.get('보스몹', 0)}마리
총 사냥: {hunted}마리
총 획득 골드: {reward}G"""
    
    def get_help(self) -> str:
        """도움말"""
        drop_rate = Config.BOSS_TICKET_DROP_RATE * 100
        return f"""몬스터 사냥 게임 도움말:
- 게임 시작: '시작' 또는 '게임시작 몬스터사냥'
- 일반몹 사냥: '일반몹', 'normal', 'n', '1'
- 특수몹 사냥: '특수몹', 'special', 's', '2'
- 보스몹 사냥: '보스몹', 'boss', 'b', '3'
- 입장권 확인: '입장권', 'ticket', 't'
- 상태 확인: '상태' 또는 'status'
- 강화 레벨 확인: '강화레벨', 'level', 'l'
- 게임 종료: '종료'

규칙:
- 일반몹: 기본 보상 20~50G, 레벨당 +8% 증가
- 특수몹: 기본 보상 80~150G, 레벨당 +12% 증가, {drop_rate:.0f}% 확률로 보스몹 입장권 드랍
- 보스몹: 기본 보상 200~350G, 레벨당 +15% 증가, 입장권 1장 필요
- 강화 레벨이 높을수록 사냥 성공 확률이 증가합니다 (레벨당 +2%)
- 강화 레벨이 높을수록 보상이 배율로 무한정 증가합니다!
- 보스몹은 특수몹을 잡아서 얻은 입장권으로만 사냥할 수 있습니다!"""

