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
      </div>

      
      <div class="p-2 border-b border-theme-border">
        
      </div>
      
      <SearchResults 
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
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue';
import SearchResults from './SearchResults.vue';
import Note from './Note.vue';
import { mdiPlusBox } from '@mdi/js';

const emit = defineEmits(['search']);

const spaceType = ref('note');
const searchTerm = ref('');
const sortBy = ref(0); // Default sort option
const selectedNoteTitle = ref(null);

const showNoteEditor = ref(false); // 控制编辑器显示
const noteKey = ref(0); // 用于强制重新创建 Note 组件

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