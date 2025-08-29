<template>
  <div class="knowledge-container" :class="{ 'dark': isDarkTheme }">
    <!-- 左侧文件列表 -->
    <div class="file-list">
      <div class="file-header">
        知识库文件
        <button type="primary" style="float: right" @click="triggerFileUpload">+ 上传文件</button>
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileUpload" 
          accept=".md" 
          style="display: none"
        >
      </div>
      <ul>
        <li 
          v-for="file in files" 
          :key="file.name" 
          @click="selectFile(file)"
          :class="{ 'selected': selectedFile?.name === file.name }"
          :title="file.name"
        >
          <span class="file-name">{{ file.name }}</span>
        </li>
      </ul>
    </div>

    <!-- 右侧文件预览 -->
    <div class="preview">
      <Note 
        v-if="selectedFileContent" 
        :note="selectedFileContent" 
        :isPreview="true"
      />
      <div v-else class="empty-preview">
        <p v-if="files.length === 0">知识库为空，请上传Markdown文件</p>
        <p v-else>请从左侧选择文件进行预览</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { themeState } from '../helpers.js';
// import { 
//   getKnowledgeFiles,
//   uploadKnowledgeFile,
//   getKnowledgeFileContent
// } from "../api.js";
import Note from './Note.vue';

const isDarkTheme = themeState;
const fileInput = ref(null);
const files = ref([]);
const selectedFile = ref(null);
const selectedFileContent = ref(null);

// 触发文件选择对话框
const triggerFileUpload = () => {
  fileInput.value.click();
};

// 处理文件上传
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // 检查文件类型
  if (!file.name.endsWith('.md')) {
    alert('仅支持Markdown文件 (.md)');
    return;
  }

  try {
    // 上传文件
    await uploadKnowledgeFile(file);

    // 刷新文件列表
    await fetchFiles();

    // 自动选择新上传的文件
    const newFile = files.value.find(f => f.name === file.name);
    if (newFile) {
      selectFile(newFile);
    }
  } catch (error) {
    console.error('文件上传失败:', error);
    alert('文件上传失败: ' + error.message);
  } finally {
    // 重置input以允许重复上传相同文件
    event.target.value = '';
  }
};

// 获取文件列表
const fetchFiles = async () => {
  try {
    const response = await getKnowledgeFiles();
    files.value = response.data;
  } catch (error) {
    console.error('获取文件列表失败:', error);
  }
};

// 选择文件并加载内容
const selectFile = async (file) => {
  selectedFile.value = file;
  try {
    const response = await getKnowledgeFileContent(file.name);
    selectedFileContent.value = {
      title: file.name,
      content: response.data.content,
      lastModified: file.lastModified
    };
  } catch (error) {
    console.error('加载文件内容失败:', error);
    selectedFileContent.value = null;
  }
};

// 初始化时加载文件列表
onMounted(() => {
  fetchFiles();
});
</script>

<style scoped lang="scss">
.knowledge-container {
  display: flex;
  height: 100vh;
  padding: 0;
  overflow: hidden;
}

.file-list {
  width: 25%;
  background-color: #f4f4f4;
  padding: 10px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;

  .file-header {
    text-align: center;
    line-height: 30px;
    width: 100%;
    flex-shrink: 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
  }

  ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
    overflow-y: auto;
    flex-grow: 1;
    height: calc(100% - 40px);

    li {
      padding: 10px;
      cursor: pointer;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      position: relative;
      display: flex;
      align-items: center;
      border-bottom: 1px solid #eee;
      transition: background-color 0.2s;

      &:hover {
        background-color: #eaeaea;
      }

      &.selected {
        background-color: #d4e6f1;
        font-weight: bold;
      }

      .file-name {
        flex: 1;
        overflow-x: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}

.preview {
  width: 75%;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: #fff;

  .empty-preview {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #999;
    font-size: 1.2em;
  }
}

/* 暗黑模式样式 */
.knowledge-container.dark {
  background-color: #1e1e1e;
  color: #e0e0e0;

  .file-list {
    background-color: #252525;
    border-right: 1px solid #444;

    ul li {
      border-bottom: 1px solid #444;
      color: #e0e0e0;

      &:hover {
        background-color: #333;
      }

      &.selected {
        background-color: #2a3d4d;
      }
    }
  }

  .preview {
    background-color: #1e1e1e;

    .empty-preview {
      color: #888;
    }
  }
}
</style>