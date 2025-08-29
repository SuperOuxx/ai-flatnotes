<template>
  <div class="flex h-full">
    <!-- Left Sidebar (25%) -->
    <div class="w-1/4 border-r border-theme-border overflow-auto">
      <SearchResults 
        :searchTerm="searchTerm" 
        :sortBy="sortBy"
        @note-selected="handleNoteSelected"
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
import { ref, provide } from 'vue';
import SearchResults from './SearchResults.vue';
import Note from './Note.vue';

const searchTerm = ref('');
const sortBy = ref(0); // Default sort option
const selectedNoteTitle = ref(null);

// Provide state to child components
provide('workspaceState', {
  searchTerm,
  sortBy,
  selectedNoteTitle
});

function handleNoteSelected(title) {
  selectedNoteTitle.value = title;
}
</script>