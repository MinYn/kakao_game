"""
Kafka 이벤트 컨슈머 워커
비동기로 이벤트를 처리하는 워커 프로세스
"""
import json
import logging
from typing import Dict, Any
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from config import Config

logger = logging.getLogger(__name__)


class EventConsumerWorker:
    """Kafka 이벤트 컨슈머 워커"""
    
    def __init__(self, topics: list, group_id: str = 'gamebot-workers'):
        self.topics = topics
        self.group_id = group_id
        self.consumer: KafkaConsumer = None
        self.running = False
    
    def start(self):
        """워커 시작"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,  # 1초 타임아웃
            )
            self.running = True
            logger.info(f"Event consumer started for topics: {self.topics}")
            
            while self.running:
                try:
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            self._process_message(message)
                except Exception as e:
                    logger.error(f"Error processing messages: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
            raise
    
    def _process_message(self, message):
        """메시지 처리"""
        try:
            event = message.value
            event_type = event.get('type')
            
            logger.debug(f"Processing event: {event_type}, key: {message.key}")
            
            # 이벤트 타입별 처리
            if event_type.startswith('gold.'):
                self._handle_gold_event(event)
            elif event_type.startswith('game.'):
                self._handle_game_event(event)
            elif event_type == 'stats.updated':
                self._handle_stats_event(event)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    def _handle_gold_event(self, event: Dict[str, Any]):
        """골드 이벤트 처리"""
        # 여기서 추가적인 비동기 작업 수행 가능
        # 예: 알림 발송, 분석 데이터 수집 등
        logger.debug(f"Gold event processed: {event}")
    
    def _handle_game_event(self, event: Dict[str, Any]):
        """게임 이벤트 처리"""
        # 게임 이벤트 기반 비동기 작업
        logger.debug(f"Game event processed: {event}")
    
    def _handle_stats_event(self, event: Dict[str, Any]):
        """통계 이벤트 처리"""
        # 통계 집계, 분석 등
        logger.debug(f"Stats event processed: {event}")
    
    def stop(self):
        """워커 중지"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Event consumer stopped")


def run_worker():
    """워커 실행 (독립 프로세스용)"""
    import signal
    
    worker = EventConsumerWorker(
        topics=['gold-events', 'game-events', 'stats-events'],
        group_id='gamebot-workers'
    )
    
    def signal_handler(sig, frame):
        logger.info("Shutting down worker...")
        worker.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    worker.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_worker()
