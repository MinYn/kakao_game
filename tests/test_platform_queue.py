import time

from events.platform_queue import PlatformMessage, PlatformMessageQueue


def test_in_memory_message_flow():
    queue = PlatformMessageQueue(use_kafka=False)
    received = []

    def handle_outgoing(msg: PlatformMessage):
        received.append(msg)

    def handle_incoming(msg: PlatformMessage):
        queue.publish_outgoing(
            PlatformMessage(
                platform=msg.platform,
                user_id=msg.user_id,
                content=msg.content.upper(),
                correlation_id=msg.correlation_id,
            )
        )

    queue.start_outgoing_consumer(handle_outgoing)
    queue.start_incoming_consumer(handle_incoming)

    queue.publish_incoming(PlatformMessage(platform="discord", user_id="u1", content="hello"))

    # 간단한 대기 (인메모리 큐 처리용)
    time.sleep(0.3)

    queue.stop()

    assert received, "Outgoing message should be processed"
    assert received[0].content == "HELLO"
    assert received[0].platform == "discord"
    assert received[0].user_id == "u1"

