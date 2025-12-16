import random
from games.base_game import Game
from config import Config


class EnhancementGame(Game):
    """강화 게임"""
    
    def __init__(self, user_id: str, point_system=None):
        super().__init__(user_id, point_system)
        self.max_level = Config.ENHANCEMENT_MAX_LEVEL
        self.current_level = 0
        self.enhancement_cost_base = Config.ENHANCEMENT_BASE_COST
        self.enhancement_cost_multiplier = Config.ENHANCEMENT_COST_MULTIPLIER
        self.sell_multiplier = Config.ENHANCEMENT_SELL_MULTIPLIER
        self.level_bonus = Config.ENHANCEMENT_LEVEL_BONUS
    
    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.current_level = 0
        self.game_data = {
            'level': 0,
            'max_level': self.max_level,
            'attempts': 0,
            'successes': 0,
            'failures': 0
        }
        return f"""🔨 강화 게임 시작!

현재 강화 레벨: +{self.current_level}
최대 레벨: +{self.max_level}

명령어:
- '강화' 또는 'enhance': 강화 시도
- '판매' 또는 'sell': 현재 아이템 판매
- '상태' 또는 'status': 현재 상태 확인
- '종료': 게임 종료

💡 강화 레벨이 높을수록 성공 확률이 낮아집니다!
💡 실패 시 강화 레벨이 떨어질 수 있습니다!
💡 판매 시 강화 레벨에 따라 골드를 받을 수 있습니다!"""
    
    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '시작' 명령을 사용하세요."
        
        command = command.strip().lower()
        
        if command in ['종료', 'quit', 'exit']:
            return self.end()
        
        if command in ['상태', 'status', 'info']:
            return self._get_status()
        
        if command in ['강화', 'enhance', '강화하기']:
            return self._enhance()
        
        if command in ['판매', 'sell', '팔기']:
            return self._sell()
        
        return f"알 수 없는 명령입니다.\n사용 가능한 명령: '강화', '판매', '상태', '종료'"
    
    def _get_status(self) -> str:
        """현재 상태 조회"""
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        
        status = f"""📊 현재 상태

강화 레벨: +{self.current_level} / +{self.max_level}
다음 강화 비용: {cost}G
성공 확률: {success_rate:.1f}%
판매 가격: {sell_price}G
현재 골드: {self.get_user_points()}G

시도 횟수: {self.game_data.get('attempts', 0)}
성공 횟수: {self.game_data.get('successes', 0)}
실패 횟수: {self.game_data.get('failures', 0)}
"""
        return status
    
    def _enhance(self) -> str:
        """강화 시도"""
        # 최대 레벨 체크
        if self.current_level >= self.max_level:
            return f"🎉 이미 최대 레벨(+{self.max_level})입니다!"
        
        # 비용 계산
        cost = self._calculate_cost()
        
        # 골드 확인
        if not self.point_system or not self.point_system.has_points(self.user_id, cost):
            return f"❌ 강화에 필요한 골드가 부족합니다.\n필요 골드: {cost}G\n현재 골드: {self.get_user_points()}G"
        
        # 골드 차감
        self.deduct_points(cost, f"강화 시도 (+{self.current_level} → +{self.current_level + 1})")
        
        # 시도 횟수 증가
        self.game_data['attempts'] = self.game_data.get('attempts', 0) + 1
        
        # 성공 확률 계산
        success_rate = self._calculate_success_rate()
        
        # 강화 시도
        is_success = random.random() * 100 < success_rate
        
        if is_success:
            # 성공
            self.current_level += 1
            self.game_data['level'] = self.current_level
            self.game_data['successes'] = self.game_data.get('successes', 0) + 1
            
            if self.current_level >= self.max_level:
                result = f"""🎉🎉🎉 강화 성공! 🎉🎉🎉

+{self.current_level} 강화 완료! (최대 레벨 달성!)
💰 골드: {self.get_user_points()}G

축하합니다! 최대 레벨을 달성했습니다!"""
            else:
                next_cost = self._calculate_cost()
                result = f"""✅ 강화 성공!

+{self.current_level} 강화 완료!
다음 강화 비용: {next_cost}G
현재 골드: {self.get_user_points()}G"""
        else:
            # 실패
            self.game_data['failures'] = self.game_data.get('failures', 0) + 1
            
            # 실패 시 처리
            if self.current_level > 0:
                # 레벨이 1 이상이면 하락
                self.current_level -= 1
                self.game_data['level'] = self.current_level
                result = f"""❌ 강화 실패...

+{self.current_level + 1} → +{self.current_level} (레벨 하락)
현재 골드: {self.get_user_points()}G

다시 시도해보세요!"""
            else:
                # 레벨 0이면 그대로 유지
                result = f"""❌ 강화 실패...

레벨 변화 없음 (+{self.current_level})
현재 골드: {self.get_user_points()}G

다시 시도해보세요!"""
        
        return result
    
    def _calculate_cost(self) -> int:
        """강화 비용 계산"""
        # 레벨이 높을수록 비용 증가
        cost = int(self.enhancement_cost_base * (self.enhancement_cost_multiplier ** self.current_level))
        return max(cost, 10)  # 최소 10P
    
    def _calculate_success_rate(self) -> float:
        """성공 확률 계산"""
        # 레벨이 높을수록 성공 확률 감소 (완화)
        # +0: 100%, +1: 94%, +2: 88%, ..., +15: 10%
        # 레벨당 6% 감소 (기존 5%에서 완화)
        base_rate = 100 - (self.current_level * 6)
        return max(base_rate, 10)  # 최소 10%
    
    def _calculate_sell_price(self) -> int:
        """판매 가격 계산"""
        if self.current_level == 0:
            return 0
        
        # 레벨에 따라 판매 가격 계산
        # 기본 비용의 누적 합계에 판매 배율 적용
        total_invested = 0
        for level in range(self.current_level):
            level_cost = int(self.enhancement_cost_base * (self.enhancement_cost_multiplier ** level))
            total_invested += max(level_cost, 10)
        
        # 판매 가격 = 투자한 비용의 일정 비율 + 레벨 보너스
        sell_price = int(total_invested * self.sell_multiplier)
        
        # 레벨 보너스 추가 (레벨이 높을수록 더 많은 보너스)
        level_bonus_amount = self.current_level * self.level_bonus
        sell_price += level_bonus_amount
        
        # 추가 보너스: 높은 레벨일수록 더 많은 보너스
        if self.current_level >= 10:
            sell_price += int(sell_price * 0.2)  # +10 이상이면 20% 추가 보너스
        elif self.current_level >= 5:
            sell_price += int(sell_price * 0.1)  # +5 이상이면 10% 추가 보너스
        
        return max(sell_price, 10)  # 최소 10G
    
    def _sell(self) -> str:
        """아이템 판매"""
        if self.current_level == 0:
            return "❌ 판매할 아이템이 없습니다.\n강화 레벨이 0인 아이템은 판매할 수 없습니다."
        
        sell_price = self._calculate_sell_price()
        sold_level = self.current_level
        
        # 골드 지급
        if self.point_system:
            self.award_points(sell_price, f"강화 아이템 판매 (+{sold_level})")
        
        # 판매 통계 업데이트
        if 'sold_items' not in self.game_data:
            self.game_data['sold_items'] = []
        self.game_data['sold_items'].append({
            'level': sold_level,
            'price': sell_price
        })
        
        # 강화 레벨 리셋
        self.current_level = 0
        self.game_data['level'] = 0
        
        return f"""💰 아이템 판매 완료!

판매한 아이템: +{sold_level}
판매 가격: {sell_price}G
현재 골드: {self.get_user_points()}G

새로운 아이템으로 다시 시작하세요!"""
    
    def end(self) -> str:
        """게임 종료"""
        level = self.current_level
        attempts = self.game_data.get('attempts', 0)
        successes = self.game_data.get('successes', 0)
        failures = self.game_data.get('failures', 0)
        
        self.is_active = False
        self.game_data.clear()
        
        return f"""게임이 종료되었습니다.

최종 강화 레벨: +{level}
총 시도 횟수: {attempts}
성공 횟수: {successes}
실패 횟수: {failures}"""
    
    def get_help(self) -> str:
        """도움말"""
        return """강화 게임 도움말:
- 게임 시작: '시작' 또는 '게임시작 강화'
- 강화 시도: '강화' 또는 'enhance'
- 아이템 판매: '판매' 또는 'sell'
- 상태 확인: '상태' 또는 'status'
- 게임 종료: '종료'

규칙:
- 강화 레벨이 높을수록 성공 확률이 낮아집니다
- 실패 시 강화 레벨이 1 하락합니다 (레벨 0 제외)
- 강화 비용은 레벨이 높을수록 증가합니다
- 최대 레벨은 +15입니다
- 판매 시 강화 레벨에 따라 골드를 받을 수 있습니다
- 판매 후 강화 레벨은 0으로 리셋됩니다"""

