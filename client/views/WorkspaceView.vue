<template>
  <div class="flex h-full">
    <!-- Left Sidebar (25%) -->
    <div class="w-1/4 border-r border-theme-border overflow-auto">
      <!-- Add space type selector -->
      <div class="p-2 border-b border-theme-border">
        <select 
          v-model="spaceType" 
          @change="saveSpaceType"
          class="w-full p-2 border rounded"
        >
          <option value="note">笔记</option>
          <option value="knowledge">知识库</option>
        </select>
      </div>

      <SearchResults 
        :searchTerm="searchTerm" 
        :spaceType="spaceType"
        :sortBy="sortBy"
        @note-selected="handleNoteSelected"
        @search="handleSearch"
      />
    </div>
    
    <!-- Main Content (75%) -->
    <div class="w-3/4">
      <Note 
        v-if="selectedNoteTitle" 
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

const emit = defineEmits(['search']);

const spaceType = ref('note');
const searchTerm = ref('');
const sortBy = ref(0); // Default sort option
const selectedNoteTitle = ref(null);

onMounted(() => {
  const storedType = localStorage.getItem('spaceType');
  if (storedType) spaceType.value = storedType;
});

function saveSpaceType() {
  localStorage.setItem('spaceType', spaceType.value);

  // Clear current selection and search term
  selectedNoteTitle.value = null;
  searchTerm.value = '';

  // Trigger search with empty term to refresh the list
  handleSearch('');
}

// Provide state to child components
provide('workspaceState', {
  searchTerm,
  sortBy,
  selectedNoteTitle
});

function handleNoteSelected(title) {
  selectedNoteTitle.value = title;
}

// 处理搜索事件
function handleSearch(term) {
  searchTerm.value = term;
  emit('search', term);
}
</script>