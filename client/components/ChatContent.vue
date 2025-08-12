<script>
import ChatBubble from './ChatBubble.vue';

export default {
    name: 'ChatContent',
    components: {
        ChatBubble,
    },
    props: {
        messages: {
            type: Array,
            required: true,
        },
        streamingMessage: {  // 新增prop
            type: Object,
            default: null,
        },
    },
};
</script>

<template>
    <div class="chat-content">
        <ChatBubble
            v-for="(message, index) in messages"
            :key="index"
            :message="message"
        />

        <!-- 新增：显示正在流式传输的消息 -->
        <ChatBubble
            v-if="streamingMessage"
            :message="streamingMessage"
            class="streaming-message"
        />
    </div>
</template>

<style scoped>
.chat-content {
    background-color: #f4f8ff;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    height: 100%;
    padding: 1rem;
    width: 100%;
    margin-bottom: 10px;
    overflow: auto;
}

.streaming-message {
    opacity: 0.8;
    animation: blink 1s infinite;
}

@keyframes blink {
    50% { opacity: 0.5; }
}
</style>
