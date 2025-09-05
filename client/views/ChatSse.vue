<template>
  <div class="chat-container"  :class="{ 'dark': isDarkTheme }">
    <!-- 左侧聊天会话列表 -->
    <div class="chat-sessions">
      <div class="chat-header">
        AI聊天机器人
        <button type="primary" style="float: right" @click="openNewSession">+ 新会话</button>
      </div>
      <ul>
        <li v-for="session in sessions" :key="session.sessionId" @click="selectSession(session)" :title="session.sessionName"
          :class="{ 'selected-session': session.sessionId === currentSession?.sessionId }"
        >
          <span class="session-name">{{ session.sessionName }}</span>

          <!-- Edit button -->
          <span class="edit-icon" @click.stop="toggleEditMode(session)">
            <svg v-if="editingSessionId === session.sessionId" viewBox="0 0 24 24" width="16" height="16">
              <path :d="mdiCheckBold" fill="currentColor"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="16" height="16">
              <path :d="mdiPencil" fill="currentColor"/>
            </svg>
          </span>

          <!-- Edit input (only shown in edit mode) -->
          <input 
            v-if="editingSessionId === session.sessionId"
            v-model="tempTitle"
            @keyup.enter="saveTitle(session)"
            @keyup.esc="cancelEdit"
            @blur="saveTitle(session)"
            class="title-edit-input"
            ref="titleInput"
          />

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

      <div class="chat-tools">
        <button title="联网检索" @click="toggleWebSearch" :class="{ 'active': enableWebSearch }">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path :d="mdiWeb" fill="currentColor"/>
          </svg>
        </button>
        <button title="知识库" @click="toggleKbSearch"  :class="{ 'active': enableKbSearch }">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path :d="mdiBookOpenBlankVariantOutline" fill="currentColor"/>
          </svg>
        </button>
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

  import { mdiWeb, mdiCheckBold, mdiPencil, mdiBookOpenBlankVariantOutline } from '@mdi/js'

  import {nextTick, ref, onMounted, watch } from 'vue';
  import { loadTheme, themeState } from '../helpers.js';
  import {
    getMessages,
    getSessions,
    updateSessionTitle,
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

  const isDarkTheme = themeState; //ref(false);

  // Add this watcher to sync theme changes
  watch(() => document.body.classList.contains('dark'), (isDark) => {
    isDarkTheme.value = localStorage.getItem("darkTheme"); //isDark;
  });

  onMounted(() => {
    loadTheme();
    // isDarkTheme.value = document.body.classList.contains('dark');
    
    if (chatMessages.value) {
      chatMessages.value.addEventListener('scroll', () => {
        const currentPosition = chatMessages.value.scrollTop + chatMessages.value.clientHeight;
        const totalHeight = chatMessages.value.scrollHeight;
        const threshold = 50; // Pixels from bottom to consider "at bottom"

        // Update scroll tracking
        isUserScrolledUp.value = (currentPosition + threshold) < totalHeight;
        lastScrollPosition.value = chatMessages.value.scrollTop;
      });
    }
  });

  // Toggle edit mode
  const toggleEditMode = (session) => {
    if (editingSessionId.value === session.sessionId) {
      // Already editing - save changes
      saveTitle(session);
    } else {
      // Start editing
      editingSessionId.value = session.sessionId;
      tempTitle.value = session.sessionName;

      // Focus input after DOM update
      nextTick(() => {
        const input = document.querySelector('.title-edit-input');
        if (input) input.focus();
      });
    }
  };

  // Save edited title
  const saveTitle = (session) => {
    if (editingSessionId.value !== session.sessionId) return;

    // Store original title for potential rollback
    const originalTitle = session.sessionName;
    const newTitle = tempTitle.value.trim() || originalTitle;

    // Optimistically update UI
    session.sessionName = newTitle;
    if (currentSession.value?.sessionId === session.sessionId) {
      currentSession.value.sessionName = newTitle;
    }

    // Call API to save to backend
    updateSessionTitle(session.sessionId, newTitle)
      .then(() => {
        console.log("Session title updated successfully");
      })
      .catch(error => {
        console.error("Failed to update session title:", error);
        // Revert to original title on error
        session.sessionName = originalTitle;
        if (currentSession.value?.sessionId === session.sessionId) {
          currentSession.value.sessionName = originalTitle;
        }
      });

    // Exit edit mode
    editingSessionId.value = null;
  };

  // Cancel editing
  const cancelEdit = () => {
    editingSessionId.value = null;
  };

  // 添加聊天工具的状态变量
  const enableWebSearch = ref(false);
  const enableKbSearch = ref(false);

  // 添加切换方法
  const toggleWebSearch = () => {
    enableWebSearch.value = !enableWebSearch.value;
  };

  const toggleKbSearch = () => {
    enableKbSearch.value = !enableKbSearch.value;
    // 这里可以添加实际功能逻辑
  };

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
  // 滚动标志
  const isUserScrolledUp = ref(false);
  const lastScrollPosition = ref(0);
  // 编辑title
  const editingSessionId = ref(null);
  const tempTitle = ref('');

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
    if (!value) return;

    // 如果当前没有会话，设置一个临时对象（sessionId为null）
    if (!currentSession.value) {
      currentSession.value = {
        sessionName: value.length >= 15 ? value.substring(0, 15) + '...' : value,
        sessionId: null
      };
      sessions.value = [currentSession.value].concat(sessions.value);
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

    isUserScrolledUp.value = false; // Reset when user sends new message

    const apiBaseUrl = "http://127.0.0.1:8000/api/chat/ai/stream";
    const encodedValue = encodeURIComponent(value);
    const encodedSessionId = currentSession.value?.sessionId ? encodeURIComponent(currentSession.value.sessionId) : '';

    eventSource.value = new EventSource(`${apiBaseUrl}?message=${encodedValue}&session_id=${encodedSessionId}&need_web=${enableWebSearch.value}&need_kb=${enableKbSearch.value}`);
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
        
        // refreshSessions();
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
    };
    eventSource.value.addEventListener("reloadTitle", async (event) => {
      const data = JSON.parse(event.data); // Parse the JSON data
      const newSessionId = data.sessionId;
      const newTitle = data.title;

      // Update the current session if it's the temporary one
      if (currentSession.value && !currentSession.value.sessionId) {
          currentSession.value.sessionId = newSessionId;
          currentSession.value.sessionName = newTitle;
      }

      const res = await getSessions(); // 调用后端接口获取会话列表
      sessions.value = res.data.map(session => ({
        sessionId: session.id,
        sessionName: session.title
      }));

    });
  };

  /**
   * 初始化会话列表
   * @param init 是否初次加载
   */
  // const init = (init) => {
  //   let userId = localStorage.getItem('USER_ID');
  //   // 设置一个默认的用户ID，并存储到缓存
  //   if (!userId) {
  //     userId = String(new Date().getTime());
  //     localStorage.setItem('USER_ID', userId);
  //   }
  //   // getSession(userId).then(res => {
  //   //   sessions.value = res.data;
  //   //   currentSession.value = sessions?.value[0];
  //   //   if (sessions.value.length > 0 && init) {
  //   //     // 查询当前会话聊天记录
  //   //     loadMessages();
  //   //   }
  //   // });
  // };

  let isInitializing = false;

  const init = async (isFirstLoad) => {
    if (isInitializing) return;
    isInitializing = true;

    let userId = localStorage.getItem('USER_ID');
    if (!userId) {
      userId = String(new Date().getTime());
      localStorage.setItem('USER_ID', userId);
    }

    try {
      const res = await getSessions(); // 调用后端接口获取会话列表
      sessions.value = res.data.map(session => ({
        sessionId: session.id,
        sessionName: session.title
      }));

      if (sessions.value.length > 0 && isFirstLoad) {
        currentSession.value = sessions.value[0];
        loadMessages();
      }

      // isInitializing = false;
    } catch (error) {
      console.error("获取会话列表失败:", error);
    }
};
  // 初始化会话列表
  init(true)

  // 查询聊天记录
  const loadMessages = () => {

    getMessages(currentSession.value.sessionId).then(res => {
      // 清空当前消息
      messages.value = [];

      // 处理后端返回的数据
      res.data.forEach(item => {
        if (item.role === 'user') {
          messages.value.push({
            msg: item.content,
            type: 1 // 用户消息
          });
        } else if (item.role === 'assistant') {
          // 处理AI回复中的思考标记
          const text = item.content.replaceAll("<think>", "<div class='think'>").replaceAll("</think>", "</div>");
          messages.value.push({
            msg: renderMarkdown(text),
            type: 2 // AI消息
          });
        }
      });

      // 滚动到底部
      scrollToBottom();
    }).catch(error => {
      console.error("加载消息失败:", error);
    });
};

  /**
   * 滚动到聊天框底部
   */
  const scrollToBottom = async () => {
    await nextTick();
    if (chatMessages.value && !isUserScrolledUp.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight;
    }
    // if (chatMessages.value) {
    //   const lastMessage = chatMessages.value?.children[chatMessages.value.children.length - 1];
    //   if (lastMessage) {
    //     lastMessage.scrollIntoView({behavior: 'smooth', block: 'end'});
    //   }
    // } else {
    //   console.error('聊天框不可用');
    // }
  };
</script>

<style scoped lang="scss">

/* 添加选中会话的高亮样式 */
li.selected-session {
  background-color: var(--theme-highlight-bg);
  border-left: 3px solid var(--theme-brand);

  .session-name {
    color: var(--text-theme-brand);
    font-weight: bold;
  }
}

.chat-container {
  display: flex;
  height: 100vh;
  padding: 0;
  overflow: hidden; /* 添加这行防止外层滚动条 */
}

// .chat-sessions {
//   width: 25%;
//   background-color: #f4f4f4;
//   padding: 10px;

//   .chat-header {
//     text-align: center;
//     line-height: 30px;
//     width: 100%;
//   }

//   ul {
//     list-style-type: none;
//     padding: 0;

//     li {
//       padding: 10px;
//       cursor: pointer;

//       &:hover {
//         background-color: #ddd;
//       }
//     }
//   }
// }

// li {
//   position: relative;
//   display: flex;
//   align-items: center;
//   padding: 10px 30px 10px 10px; // Extra right padding for icon

//   .edit-icon {
//     position: absolute;
//     right: 5px;
//     top: 50%;
//     transform: translateY(-50%);
//     cursor: pointer;
//     opacity: 0.5;
//     transition: opacity 0.2s;
//     font-size: 14px;
//     width: 20px;
//     height: 20px;
//     display: flex;
//     align-items: center;
//     justify-content: center;
    
//     &:hover {
//       opacity: 1;
//       background: rgba(0,0,0,0.1);
//       border-radius: 3px;
//     }
//   }
  
//   .title-edit-input {
//     position: absolute;
//     top: 0;
//     left: 0;
//     width: calc(100% - 30px);
//     height: 100%;
//     border: 1px solid #007bff;
//     border-radius: 4px;
//     padding: 0 8px;
//     font-size: inherit;
//     background: white;
//     box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
//     z-index: 10;
//   }
// }

li {
  position: relative;
  padding: 10px;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  .session-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }

  .session-name {
    flex: 1;
    overflow-x: hidden;
    overflow-y: hidden;
    padding-bottom: 2px;
    scrollbar-width: thin;
    scrollbar-color: #888 #f0f0f0;
    transition: all 0.3s ease;
  }

  .edit-icon {
    margin-left: 8px;
    opacity: 0.5;
    transition: opacity 0.2s;
    font-size: 14px;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &:hover {
      opacity: 1;
      background: rgba(0,0,0,0.1);
      border-radius: 3px;
    }
  }
}

.chat-sessions {
  width: 25%;
  background-color: #f4f4f4;
  padding: 10px;
  display: flex;          // Add flex container
  flex-direction: column; // Stack children vertically
  height: 100%; /* 确保高度100% */
  overflow: hidden;       // Hide overflow

  .chat-header {
    text-align: center;
    line-height: 30px;
    width: 100%;
    flex-shrink: 0;       // Prevent header from shrinking
  }

  ul {
    list-style-type: none;
    padding: 0;
    margin: 0;            // Remove default margin
    overflow-y: auto;     // Vertical scrolling
    overflow-x: hidden;   // Hide horizontal scroll by default
    flex-grow: 1;         // Take remaining space
    white-space: nowrap;  // Prevent text wrapping
    height: calc(100% - 40px); /* 减去header高度 */

    li {
      padding: 10px;
      cursor: pointer;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      position: relative;
      display: flex;
      align-items: center;
      transition: background-color 0.2s; /* 添加过渡效果 */

      /* 添加这个样式确保高亮边框可见 */
      border-left: 3px solid transparent;

      // Container for the session name
      .session-name {
        flex: 1;
        overflow-x: hidden; // Hide scrollbar by default
        overflow-y: hidden;
        padding-bottom: 2px;
        scrollbar-width: thin;
        scrollbar-color: #888 #f0f0f0;
        transition: all 0.3s ease;

        // Custom scrollbar styling (hidden by default)
        &::-webkit-scrollbar {
          height: 4px;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        &::-webkit-scrollbar-thumb {
          background-color: #888;
          border-radius: 2px;
          opacity: 0;
          transition: opacity 0.3s ease;
        }
      }

      // Show scrollbar on hover
      &:hover .session-name {
        overflow-x: auto; // Show scrollbar on hover

        &::-webkit-scrollbar,
        &::-webkit-scrollbar-thumb {
          opacity: 1; // Fade in scrollbar
        }
      }

      // Tooltip for full title
      &::after {
        content: attr(title);
        position: absolute;
        top: 100%;
        left: 0;
        background: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        white-space: nowrap;
        z-index: 100;
        font-size: 14px;
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none;
      }

      &:hover::after {
        opacity: 1; // Show tooltip on hover
      }
    }
  }
}

.chat-window {
  width: 75%;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保高度100% */
  overflow: hidden; /* 移除滚动条 */
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #fff;
  height: calc(100% - 62px); /* 减去输入框高度 */

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
  flex-shrink: 0; /* 防止输入框被压缩 */

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

.chat-tools {
  display: flex;
  padding: 8px 10px;
  background-color: #f8f8f8;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  gap: 16px;

  button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    display: flex;
    align-items: center;

    &:hover {
      background-color: #eaeaea;
    }

    svg {
      margin-right: 4px;
    }

     &.active {
      background-color: #e0e0e0;
      box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.5);

      svg {
        color: #007bff;
      }
    }
  }
}


// Dark 模式
/* 暗黑模式样式 */

.dark li.selected-session {
  background-color: var(--theme-highlight-bg-dark);
  border-left-color: var(--theme-brand-dark);

  .session-name {
    color: var(--text-theme-brand-dark); /* 暗黑模式下的品牌色 */
  }
}

.chat-container.dark {
  background-color: #1e1e1e;
  color: #e0e0e0;

  .chat-sessions {
    background-color: #252525;
    border-right: 1px solid #444;

    ul li {
      color: #e0e0e0;

      &:hover {
        background-color: #333;
      }
    }
  }

  .chat-messages {
    background-color: #1e1e1e;

    .message pre {
      background-color: #2d2d2d;
      color: #e0e0e0;
    }

    .message.sent pre {
      background-color: #2a3d2a;
    }
  }

  .chat-input textarea {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-color: #444;
  }

  .chat-tools {
    background-color: #2d2d2d;
    border-color: #444;

    button:hover {
      background-color: #3a3a3a;
    }

    button {
      &.active {
        background-color: #3a3a3a;
        box-shadow: 0 0 0 2px rgba(100, 149, 237, 0.5);

        svg {
          color: #6495ed;
        }
      }
    }
  }
}

</style>