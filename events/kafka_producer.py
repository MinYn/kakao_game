"""
Kafka 이벤트 프로듀서
"""
import json
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from config import Config
import logging

logger = logging.getLogger(__name__)


class EventProducer:
    """Kafka 이벤트 프로듀서"""
    
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self._init_producer()
    
    def _init_producer(self):
        """Kafka 프로듀서 초기화"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # 모든 리플리카에 쓰기 확인
                retries=3,
                max_in_flight_requests_per_connection=1,  # 순서 보장
            )
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def publish(self, topic: str, event: Dict[str, Any], key: Optional[str] = None):
        """이벤트 발행
        
        Args:
            topic: Kafka 토픽
            event: 이벤트 데이터
            key: 파티션 키 (None이면 라운드로빈)
        """
        if not self.producer:
            logger.warning("Kafka producer not initialized, event not published")
            return
        
        try:
            future = self.producer.send(topic, value=event, key=key)
            # 비동기로 발행 (블로킹 안 함)
            future.add_callback(self._on_success)
            future.add_errback(self._on_error)
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
    
    def _on_success(self, record_metadata):
        """발행 성공 콜백"""
        logger.debug(
            f"Event published: topic={record_metadata.topic}, "
            f"partition={record_metadata.partition}, "
            f"offset={record_metadata.offset}"
        )
    
    def _on_error(self, exception):
        """발행 실패 콜백"""
        logger.error(f"Failed to publish event: {exception}")
    
    def flush(self):
        """대기 중인 모든 메시지 전송"""
        if self.producer:
            self.producer.flush()
    
    def close(self):
        """프로듀서 종료"""
        if self.producer:
            self.producer.close()
            self.producer = None


# 싱글톤 인스턴스
_event_producer: Optional[EventProducer] = None


def get_event_producer() -> EventProducer:
    """이벤트 프로듀서 싱글톤 반환"""
    global _event_producer
    if _event_producer is None:
        _event_producer = EventProducer()
    return _event_producer


def publish_event(topic: str, event: Dict[str, Any], key: Optional[str] = None):
    """이벤트 발행 헬퍼 함수"""
    producer = get_event_producer()
    producer.publish(topic, event, key)
