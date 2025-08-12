<script>
import ChatContent from '../components/ChatContent.vue';
import InputRow from '../components/InputRow.vue';
import ReconnectingWebSocket from 'reconnecting-websocket';

export default {
    name: 'Chat',
    components: {
        ChatContent,
        InputRow,
    },
    data() {
        return {
            messages: [],
            socket: null,
        };
    },
    mounted() {
        this.socket = new ReconnectingWebSocket('ws://localhost:8000/ws');
        this.socket.onmessage = this.handleSocketMessage;
        this.getMessages();
    },
    beforeDestroy() {
        this.socket.close();
    },
    methods: {
        handleSocketMessage(event) {
            const data = JSON.parse(event.data);
            // console.log(data);
            if (data.hasOwnProperty("msg_arr")) {
                this.messages = data.msg_arr
            }
            // if (data.type === 'message_update') {
            //     this.messages.push({
            //         role: data.role,
            //         content: data.content
            //     });
            // }
            if (data.type === 'message_part') {
                if (!this.tempStreamingMessage) {
                    this.tempStreamingMessage = {
                        role: data.role, 
                        content: data.content 
                    };
                    // this.$set(this, 'tempStreamingMessage', { 
                    //     role: data.role, 
                    //     content: data.content 
                    // });
                } else {
                    this.tempStreamingMessage.content += data.content;
                }
            } else if (data.type === 'message_complete') {
                // 创建新对象触发响应式更新
                this.tempStreamingMessage = {
                    ...this.tempStreamingMessage,
                    content: this.tempStreamingMessage.content + data.content
                };
                this.messages.push(this.tempStreamingMessage);
                this.tempStreamingMessage = null;
            }
        },
        getMessages() {
            const newMessage = {
                type: 'get_messages',
            };
            this.sendSocketMessage(newMessage);

        },
        sendSocketMessage(message) {
            // 针对用户发送的新消息先本地添加
            if (message.type === 'new_message') {
                this.messages.push({
                    role: 'user',
                    content: message.content
                });
            }
            this.socket.send(JSON.stringify(message));
        },
    },
};
</script>

<template>
    <div class="app">
        <div class="app-content">
            
            <!-- 传递streamingMessage -->
            <ChatContent 
                :messages="messages"
                :streaming-message="tempStreamingMessage"
            />
            <InputRow :sendSocketMessage="this.sendSocketMessage" :messages="this.messages"/>
        </div>
    </div>
</template>

<style scoped>
.app {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100vh;
    width: 100vw;
    margin: 0;
    padding: 0;
}

.app-content {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    padding: 1rem;
    width: 100%;
    max-width: 1000px;
    overflow: auto;
}
</style>
