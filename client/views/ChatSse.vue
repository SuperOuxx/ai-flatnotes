<template>
  <div class="chat-container">
    <!-- 左侧聊天会话列表 -->
    <div class="chat-sessions">
      <div class="chat-header">
        AI聊天机器人
        <button type="primary" style="float: right" @click="openNewSession">开启新会话</button>
      </div>
      <ul>
        <li v-for="session in sessions" :key="session.sessionId" @click="selectSession(session)">
          {{ session.sessionName }}
        </li>
      </ul>
    </div>
    <!-- 右侧聊天窗口 -->
    <div class="chat-window">
      <div class="chat-messages" ref="chatMessages">
        <div v-for="message in messages" :key="message" class="message"
             :class="{'sent': message.type===1}">
          <pre v-html="message.msg"></pre>
        </div>
      </div>
      <!-- 右侧下方聊天内容输入框 -->
      <div class="chat-input">
        <textarea v-model="newMessage" @keydown.enter="sendMessage" placeholder="请输入问题..."></textarea>
        <button @click="sendMessage">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
  import {nextTick, ref} from 'vue';
  import {
    getMessages,
    getSessions,
  } from "../api.js";

  import { marked } from 'marked';
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
  });

  // 创建 Markdown 渲染函数
  const renderMarkdown = (content) => {
    return marked(content);
  };


// import {ElMessage} from "element-plus";

// 初始化MarkdownIt实例
// const md = new MarkdownIt({
//   html: true,
//   linkify: true,
//   typographer: true,
//   highlight: (str, lang) => {
//     if (lang && hljs.getLanguage(lang)) {
//       try {
//         return '<pre class="hljs"><code>' +
//           hljs.highlight(lang, str, true).value +
//           '</code></pre>';
//       } catch (__) {
//       }
//     }

//     return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
//   }
// });

  // 引用聊天消息容器
  const chatMessages = ref(null);
  // 聊天会话列表
  const sessions = ref([]);
  // 当前选中的会话
  const currentSession = ref({});
  // 新消息输入框内容
  const newMessage = ref('');
  // 聊天记录
  const messages = ref([]);
  // 定义事件源的引用，用于实时通信
  const eventSource = ref(null);

  // 选择会话
  const selectSession = (session) => {
    currentSession.value = session;
    messages.value = [];
    // 查询当前会话聊天记录
    loadMessages();
  };


  // 创建新会话
  const openNewSession = () => {
    newMessage.value = '';
    messages.value = [];
    currentSession.value = {};
  };

  // 发送消息
  const sendMessage = () => {
    const value = newMessage.value;
    if (!value) {
      return ;// ElMessage.warning('请输入问题');
    }
    if (!currentSession.value) {
      // 添加一个模拟的新Session
      const sessionId = '';
      const sessionName = value.length >= 15 ? String(value).substring(0, 15) + '...' : value;
      sessions.value = [{
        sessionName,
        sessionId
      }].concat(sessions.value);
    }
    if (eventSource.value != null) {
      eventSource.value.close();
    }
    // 将用户输入的消息添加到消息列表中，并设置消息类型为用户发送
    messages.value.push({
      msg: newMessage.value,
      type: 1
    });
    messages.value.push({
      msg: '',
      type: 2
    });
    const aiMessageIndex = messages.value.length - 1; // 记录AI消息索引

    newMessage.value = '';

    // 新增：累积消息的变量
    let fullResponse = '';
    let messageOrigin = '';

    const apiBaseUrl = "http://127.0.0.1:8000/api/chat/ai/stream";
    const encodedValue = encodeURIComponent(value);
    const encodedSessionId = currentSession.value?.sessionId ? encodeURIComponent(currentSession.value.sessionId) : '';
    const userId = localStorage.getItem('USER_ID') || '';

    eventSource.value = new EventSource(`${apiBaseUrl}?message=${encodedValue}&session_id=${encodedSessionId}&user_id=${userId}`);
    eventSource.value.onmessage = function (event) {
      try {
        let chunk = event.data.replace("data:", "");
        fullResponse += chunk; // 累积片段

        // 更新消息对象：存储原始文本和渲染后的内容
        messages.value[aiMessageIndex].raw = fullResponse;
        messages.value[aiMessageIndex].msg = renderMarkdown(fullResponse);

        // let substring = event.data.replaceAll("data:", "");
        // messages.value[messages.value.length - 1].msg += renderMarkdown(substring)
        
        // let parse = JSON.parse(substring);
        // messageOrigin += parse.result?.output?.text;
        // if (parse.result?.metadata?.finishReason === "stop") {
        //   messageOrigin = messageOrigin.replace("<think>", "<div class='think'>").replace("</think>", "</div>");
        //   eventSource.value.close();
        // }
        // messages.value[messages   .value.length - 1].msg = renderMarkdown(messageOrigin) //md.render(messageOrigin);
        // 调用滚动方法
        scrollToBottom();
        if (!currentSession.value.sessionId) {
          init(false);
        }
      } catch (error) {
        console.error("消息异常:", error);
      }
    };
    eventSource.value.onerror = function (event) {
      eventSource.value.close();
    };
    eventSource.value.onclose = function (event) {
      console.log("事件关闭:", event);
      if (currentSession.value.sessionId) {
        // 保存完整对话（需要实现对应API）
        saveMessage(currentSession.value.sessionId, fullResponse);
      }
    };
  };

  /**
   * 初始化会话列表
   * @param init 是否初次加载
   */
  const init = (init) => {
    let userId = localStorage.getItem('USER_ID');
    // 设置一个默认的用户ID，并存储到缓存
    if (!userId) {
      userId = String(new Date().getTime());
      localStorage.setItem('USER_ID', userId);
    }
    // getSession(userId).then(res => {
    //   sessions.value = res.data;
    //   currentSession.value = sessions?.value[0];
    //   if (sessions.value.length > 0 && init) {
    //     // 查询当前会话聊天记录
    //     loadMessages();
    //   }
    // });
  };
  // 初始化会话列表
  init(true)

  // 查询聊天记录
  const loadMessages = () => {
    getMessages(currentSession.value.sessionId).then(res => {
      res.data.forEach(item => {
        if (item.messageType === 'USER') {
          messages.value.push({
            msg: item.text,
            type: 1
          });
        } else {
          const text = item.text.replaceAll("<think>", "<div class='think'>").replaceAll("</think>", "</div>");
          messages.value.push({
            msg: renderMarkdown(messageOrigin), //md.render(text),
            type: 2
          });
        }
      });
    });
    setTimeout(() => {
      scrollToBottom();
    }, 200);
  };

  /**
   * 滚动到聊天框底部
   */
  const scrollToBottom = async () => {
    await nextTick();
    if (chatMessages.value) {
      const lastMessage = chatMessages.value?.children[chatMessages.value.children.length - 1];
      if (lastMessage) {
        lastMessage.scrollIntoView({behavior: 'smooth', block: 'end'});
      }
    } else {
      console.error('聊天框不可用');
    }
  };
</script>

<style scoped lang="scss">
.chat-container {
  display: flex;
  height: 100vh;
  padding: 0;
}

.chat-sessions {
  width: 25%;
  background-color: #f4f4f4;
  padding: 10px;

  .chat-header {
    text-align: center;
    line-height: 30px;
    width: 100%;
  }

  ul {
    list-style-type: none;
    padding: 0;

    li {
      padding: 10px;
      cursor: pointer;

      &:hover {
        background-color: #ddd;
      }
    }
  }
}

.chat-window {
  width: 75%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #fff;

  .message {
    margin-bottom: 10px;

    pre {
      background-color: #f9f9f9;
      padding: 10px;
      border-radius: 5px;
      white-space: pre-wrap;
    }
    :deep(.think){
      display: inline-block;
      padding: 0 10px;
      color: #999999;
      font-size: 13px;
      background-color: #efecec;
      border-radius: 5px;
    }

    &.sent {
      text-align: right;

      pre {
        background-color: #e1ffc7;
      }
    }
  }
}

.chat-input {
  display: flex;
  padding: 10px;

  textarea {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    resize: none;
  }

  button {
    margin-left: 10px;
    padding: 10px 20px;
    border: none;
    background-color: #007bff;
    color: #fff;
    border-radius: 5px;
    cursor: pointer;

    &:hover {
      background-color: #0056b3;
    }
  }
}
</style>
