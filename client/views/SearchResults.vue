<template>
  <div class="flex h-full max-w-[700px] flex-col">
    <!-- Search Input -->
    <SearchInput 
        :initialSearchTerm="props.searchTerm" 
        class="mb-2" 
        @search="handleSearchInSearchResults"
    
    />

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Sort By -->
      <div class="flex justify-end">
        <CustomButton
          :label="`Sort By: ${sortByName}`"
          :iconPath="mdiSort"
          class="mb-1"
          @click="toggleSortMenu"
        />
        <PrimeMenu ref="sortMenu" :model="menuItems" :popup="true" />
      </div>

      <!-- Search Results -->
      <div
        v-for="result in results"
        class="mb-4 cursor-pointer rounded px-2 py-1 hover:bg-theme-background-elevated"
        @click="handleNoteClick(result.title)"
      >
        <!-- Title and Tags -->
        <div>
        <span v-html="result.titleHighlightsOrTitle" class="mr-2"></span>
        <Tag v-for="tag in result.tagMatches" :tag="tag" class="mr-1" />
        </div>
        <!-- Last Modified and Content Highlights -->
        <div>
        <span class="text-theme-text-muted">{{
            result.lastModifiedAsString
        }}</span>
        <span v-if="result.contentHighlights"> - </span>
        <span
            v-html="result.contentHighlights"
            class="text-theme-text-muted"
        ></span>
        </div>
      </div>
    </LoadingIndicator>
  </div>
</template>

<script setup>
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref, watch } from "vue";
// import { useRouter } from "vue-router";

import { mdiMagnify, mdiSort } from "@mdi/js";
import { apiErrorHandler, getNotes } from "../api.js";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import PrimeMenu from "../components/PrimeMenu.vue";
import Tag from "../components/Tag.vue";
import { params, searchSortOptions } from "../constants.js";
import SearchInput from "../partials/SearchInput.vue";

const emit = defineEmits(['note-selected', 'search']);

function handleSearchInSearchResults(term) {
  emit('search', term);
}

const props = defineProps({
  searchTerm: String,
  spaceType: String,
  sortBy: {
    type: Number,
    default: searchSortOptions.score,
  },
});

const loadingIndicator = ref();
const results = ref([]);
// const router = useRouter();
const sortMenu = ref();
const toast = useToast();

const sortByName = computed(() => {
  const sortOptionNames = {
    [searchSortOptions.title]: "Title",
    [searchSortOptions.lastModified]: "Last Modified",
    [searchSortOptions.score]: "Score",
  };
  return sortOptionNames[props.sortBy];
});

function init() {
  loadingIndicator.value.setLoading();
  // Map numeric sort to string value
  // const sortString = sortMapping[props.sortBy] || 'score';

  getNotes(props.searchTerm, 'score', 'desc', null, props.spaceType)
  // getNotes(props.searchTerm)
    .then((data) => {
      results.value = sortResults(data);
      if (results.value.length > 0) {
        loadingIndicator.value.setLoaded();
      } else {
        loadingIndicator.value.setFailed("No Results", mdiMagnify);
      }
    })
    .catch((error) => {
      loadingIndicator.value.setFailed();
      apiErrorHandler(error, toast);
    });
}

function sortResults(results) {
  if (props.sortBy === searchSortOptions.title) {
    return results.sort((a, b) => a.title.localeCompare(b.title));
  } else if (props.sortBy === searchSortOptions.lastModified) {
    return results.sort((a, b) => b.lastModified - a.lastModified);
  } else {
    return results.sort((a, b) => b.score - a.score);
  }
}

function reSortResults() {
  results.value = sortResults(results.value);
}

// function updateSortByParam(sortBy) {
//   router.push({
//     name: "search",
//     query: {
//       [params.searchTerm]: props.searchTerm,
//       [params.sortBy]: sortBy,
//     },
//   });
// }

const menuItems = [
  {
    label: "Sort By: Score",
    command: () => {
      // 直接更新 sortBy 值
      sortBy.value = searchSortOptions.score;
    },
  },
  {
    label: "Sort By: Title",
    command: () => {
      sortBy.value = searchSortOptions.title;
    },
  },
  {
    label: "Sort By: Last Modified",
    command: () => {
      sortBy.value = searchSortOptions.lastModified;
    },
  },
];

function toggleSortMenu(event) {
  sortMenu.value.toggle(event);
}

watch(() => props.searchTerm, init);
watch(() => props.sortBy, reSortResults);
// 2. 添加 spaceType 的 watch
watch(() => props.spaceType, init);
onMounted(init);

function handleNoteClick(title) {
  emit('note-selected', title);
}

</script>

<style>
.match {
  @apply text-theme-brand;
}
</style>
