"""Platform message queue using Kafka (with in-memory fallback).

플랫폼 어댑터가 수신/발신하는 메시지를 Kafka 토픽을 통해 전달하도록 돕는다.
Kafka가 비활성화되었거나 테스트 환경에서는 간단한 인메모리 큐로 대체된다.
"""

from __future__ import annotations

import json
import threading
import queue
import uuid
from dataclasses import dataclass, asdict
from typing import Callable, Optional

from kafka import KafkaConsumer, KafkaProducer

from config import Config


@dataclass
class PlatformMessage:
    """플랫폼 간 주고받는 메시지 모델."""

    platform: str
    user_id: str
    content: str
    correlation_id: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        if not data.get("correlation_id"):
            data["correlation_id"] = str(uuid.uuid4())
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PlatformMessage":
        return cls(
            platform=data.get("platform", ""),
            user_id=data.get("user_id", ""),
            content=data.get("content", ""),
            correlation_id=data.get("correlation_id", ""),
        )


class PlatformMessageQueue:
    """Kafka 기반 플랫폼 메시지 큐.

    Kafka를 우선 사용하지만, 설정 또는 테스트 환경에서 Kafka가 없는 경우
    인메모리 큐로 대체된다.
    """

    def __init__(
        self,
        *,
        use_kafka: bool = Config.USE_KAFKA,
        bootstrap_servers: str = Config.KAFKA_BOOTSTRAP_SERVERS,
        incoming_topic: str = getattr(Config, "KAFKA_INCOMING_TOPIC", "platform.incoming"),
        outgoing_topic: str = getattr(Config, "KAFKA_OUTGOING_TOPIC", "platform.outgoing"),
        consumer_group: str = getattr(Config, "KAFKA_PLATFORM_GROUP", "platform-router"),
    ) -> None:
        self.use_kafka = use_kafka
        self.bootstrap_servers = bootstrap_servers
        self.incoming_topic = incoming_topic
        self.outgoing_topic = outgoing_topic
        self.consumer_group = consumer_group

        self._producer: Optional[KafkaProducer] = None
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        # 인메모리 대체 큐
        self._incoming_queue: "queue.Queue[dict]" = queue.Queue()
        self._outgoing_queue: "queue.Queue[dict]" = queue.Queue()

        if self.use_kafka:
            self._init_producer()

    @property
    def enabled(self) -> bool:
        return self.use_kafka

    def _init_producer(self) -> None:
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
        except Exception:
            # Kafka가 없으면 자동으로 인메모리 모드로 전환
            self.use_kafka = False
            self._producer = None

    def publish_incoming(self, message: PlatformMessage) -> None:
        payload = message.to_dict()
        if self.use_kafka and self._producer:
            self._producer.send(
                self.incoming_topic,
                value=payload,
                key=payload.get("user_id"),
            )
            return

        self._incoming_queue.put(payload)

    def publish_outgoing(self, message: PlatformMessage) -> None:
        payload = message.to_dict()
        if self.use_kafka and self._producer:
            self._producer.send(
                self.outgoing_topic,
                value=payload,
                key=payload.get("user_id"),
            )
            return

        self._outgoing_queue.put(payload)

    def start_incoming_consumer(
        self,
        handler: Callable[[PlatformMessage], None],
        *,
        group_id: Optional[str] = None,
    ) -> None:
        if self.use_kafka:
            thread = threading.Thread(
                target=self._consume_kafka,
                args=(self.incoming_topic, handler, group_id or f"{self.consumer_group}-engine"),
                daemon=True,
            )
        else:
            thread = threading.Thread(
                target=self._consume_in_memory,
                args=(self._incoming_queue, handler),
                daemon=True,
            )
        thread.start()
        self._threads.append(thread)

    def start_outgoing_consumer(
        self,
        handler: Callable[[PlatformMessage], None],
        *,
        group_id: Optional[str] = None,
    ) -> None:
        if self.use_kafka:
            thread = threading.Thread(
                target=self._consume_kafka,
                args=(self.outgoing_topic, handler, group_id or f"{self.consumer_group}-adapter"),
                daemon=True,
            )
        else:
            thread = threading.Thread(
                target=self._consume_in_memory,
                args=(self._outgoing_queue, handler),
                daemon=True,
            )
        thread.start()
        self._threads.append(thread)

    def _consume_kafka(
        self,
        topic: str,
        handler: Callable[[PlatformMessage], None],
        group_id: str,
    ) -> None:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            consumer_timeout_ms=1000,
        )

        while not self._stop_event.is_set():
            message_pack = consumer.poll(timeout_ms=500)
            for _, messages in message_pack.items():
                for record in messages:
                    handler(PlatformMessage.from_dict(record.value))
        consumer.close()

    def _consume_in_memory(
        self,
        q: "queue.Queue[dict]",
        handler: Callable[[PlatformMessage], None],
    ) -> None:
        while not self._stop_event.is_set():
            try:
                payload = q.get(timeout=0.2)
            except queue.Empty:
                continue
            handler(PlatformMessage.from_dict(payload))

    def stop(self) -> None:
        self._stop_event.set()
        if self._producer:
            try:
                self._producer.flush()
            finally:
                self._producer.close()

        # 인메모리 모드에서 쓰레드 종료 대기
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=1.0)

