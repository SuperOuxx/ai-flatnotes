<script>
    import { marked } from 'marked';
    import { ref, shallowRef } from 'vue';
    import hljs from 'highlight.js'
    import 'highlight.js/styles/foundation.css'

    const render = new marked.Renderer()
    marked.setOptions({
        renderer: render, // 这是必填项
        gfm: true,	// 启动类似于Github样式的Markdown语法
        pedantic: false, // 只解析符合Markdwon定义的，不修正Markdown的错误
        sanitize: false, // 原始输出，忽略HTML标签（关闭后，可直接渲染HTML标签）

            // 高亮的语法规范
        highlight: (code, lang) => hljs.highlight(code, { language: lang }).value,
    })

    const value = ref('**Hello,World**')
    const markdownToHtml = shallowRef("")
    markdownToHtml.value = marked(value.value)

    export const change = (value) => {
    markdownToHtml.value = marked(value)
    }

export default {
    name: 'ChatBubble',
    props: {
        message: {
            type: Object,
            required: true,
        },
    },
    methods: {
        parseMarkdown(content) {
            return marked(content);
        }
    },
}
</script>

<template>
<div :class="['chat-bubble', message.role]">
    <div class="chat-bubble-avatar">
        {{ message.role }}
    </div>
    <!-- <div class="chat-bubble-content">
        {{ marked(message.content) }}
    </div> -->
    <div class="chat-bubble-content" v-html="parseMarkdown(message.content)" />
</div>
</template>

<style scoped>
.chat-bubble {
    display: flex;
    align-items: center;
    flex-direction: row;
    margin-bottom: 10px;
}

.chat-bubble.assistant {
    flex-direction: row-reverse;
}

.chat-bubble-avatar {
    flex-shrink: 0;
    background-color: #e1e1e1;
    border-radius: 50%;
    color: #000;
    font-weight: bold;
    height: 40px;
    width: 40px;
    line-height: 40px;
    margin-right: 10px;
    text-align: center;
    margin: 0px 10px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
}

.chat-bubble-content {
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
    max-width: 80%;
}

.user .chat-bubble-content {
    background-color: #f6db99;
}

.assistant .chat-bubble-content{
    background-color: #f6f8d0;
}
</style>
    