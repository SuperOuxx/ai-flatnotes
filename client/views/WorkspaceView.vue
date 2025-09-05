<template>
  <div class="flex h-full">
    <!-- Left Sidebar (25%) -->
    <div class="w-1/4 border-r border-theme-border overflow-auto">
      <!-- Add space type selector -->
      <div class="flex items-center p-2 border-b border-theme-border">
        <select 
          v-model="spaceType" 
          @change="saveSpaceType"
          class="w-1/2 p-2 border rounded mr-2"
        >
          <option value="note">笔记</option>
          <option value="knowledge">知识库</option>
        </select>

        <!-- 新建按钮 -->
        <button 
          @click="createNewNote"
          class="flex items-center justify-center p-2 text-white bg-theme-brand rounded hover:bg-theme-brand-hover"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path :d="mdiPlusBox" fill="currentColor"/>
          </svg>
        </button>

        <!-- 上传按钮 -->
        <button 
          @click="triggerFileUpload"
          class="flex items-center justify-center p-2 text-white bg-theme-brand rounded hover:bg-theme-brand-hover ml-2"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path :d="mdiUploadBox" fill="currentColor"/>
          </svg>
        </button>
      </div>

      
      <div class="p-2 border-b border-theme-border">
        
      </div>
      
      <SearchResults 
        ref="searchResults"
        :searchTerm="searchTerm" 
        :spaceType="spaceType"
        :sortBy="sortBy"
        :selectedNoteTitle="selectedNoteTitle"
        @note-selected="handleNoteSelected"
        @search="handleSearch"
      />

    </div>
    
    <!-- Main Content (75%) -->
    <div class="w-3/4">
      <Note 
        v-if="showNoteEditor" 
        :noteTitle="selectedNoteTitle" 
        :key="selectedNoteTitle"
      />
      <div v-else class="flex items-center justify-center h-full text-theme-text-muted">
        Select a note from the sidebar
      </div>
    </div>

    <!-- 隐藏的文件上传输入 -->
    <input 
      type="file" 
      ref="fileInput" 
      @change="handleFileUpload" 
      accept=".md" 
      multiple
      style="display: none"
    >
  </div>
</template>

<script setup>
import { ref, provide, onMounted, nextTick } from 'vue';
import { mdiPlusBox, mdiUploadBox } from '@mdi/js';
import { useToast } from 'primevue/usetoast';
import { getToastOptions } from '../helpers.js';
import { createNote } from '../api.js';
import SearchResults from './SearchResults.vue';
import Note from './Note.vue';


const emit = defineEmits(['search']);

const spaceType = ref('note');
const searchTerm = ref('');
const sortBy = ref(0); // Default sort option
const selectedNoteTitle = ref(null);

const showNoteEditor = ref(false); // 控制编辑器显示
const noteKey = ref(0); // 用于强制重新创建 Note 组件

const fileInput = ref(null);
const searchResults = ref(null); // 引用SearchResults组件
const toast = useToast();

onMounted(() => {
  const storedType = localStorage.getItem('spaceType');
  if (storedType) spaceType.value = storedType;
});

// 新建笔记
function createNewNote() {
  selectedNoteTitle.value = null; // 设置为 null 表示新建
  showNoteEditor.value = true; // 显示编辑器
  noteKey.value++; // 强制重新创建 Note 组件
}

function saveSpaceType() {
  localStorage.setItem('spaceType', spaceType.value);

  // Clear current selection and search term
  selectedNoteTitle.value = null;
  searchTerm.value = '';

  showNoteEditor.value = false; // 隐藏编辑器

  // Trigger search with empty term to refresh the list
  handleSearch('');
}

// 触发文件上传
function triggerFileUpload() {
  fileInput.value.click();
}

// 处理文件上传
async function handleFileUpload(event) {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;

  // 只处理Markdown文件
  const mdFiles = files.filter(file => file.name.endsWith('.md'));
  if (mdFiles.length === 0) {
    toast.add(
      getToastOptions(
        "请选择Markdown文件（.md）",
        "无效文件类型",
        "error"
      )
    );
    return;
  }

  try {
    // 处理每个文件
    for (const file of mdFiles) {
      const content = await readFileAsText(file);
      const title = file.name.replace(/\.md$/i, '');

      // 创建新笔记
      await createNote(title, content, spaceType.value);
    }

    // 刷新文件列表
    // refreshFileList();
    if (searchResults.value) {
      searchResults.value.refresh();
    }

    // 如果只上传一个文件，自动选中它
    if (mdFiles.length === 1) {
      const title = mdFiles[0].name.replace(/\.md$/i, '');
      selectedNoteTitle.value = title;
      showNoteEditor.value = true;
      noteKey.value++;

      toast.add(
        getToastOptions(
          `文件 "${mdFiles[0].name}" 已成功上传并选中`,
          "上传成功",
          "success"
        )
      );
    } else {
      toast.add(
        getToastOptions(
          `${mdFiles.length} 个文件已成功上传`,
          "批量上传成功",
          "success"
        )
      );
    }
  } catch (error) {
    console.error('文件上传失败:', error);
    toast.add(
      getToastOptions(
        "文件上传失败: " + (error.response?.data?.detail || error.message),
        "错误",
        "error"
      )
    );
  } finally {
    // 重置input以允许重复上传
    event.target.value = null;
  }
}

// 读取文件内容为文本
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file, 'UTF-8');
  });
}

// Provide state to child components
provide('workspaceState', {
  searchTerm,
  sortBy,
  selectedNoteTitle,
  showNoteEditor
});

function handleNoteSelected(title) {
  selectedNoteTitle.value = title;
  showNoteEditor.value = true; // 显示编辑器
}

// 处理搜索事件
function handleSearch(term) {
  searchTerm.value = term;
  emit('search', term);
}
</script>