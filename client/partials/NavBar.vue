<template>
  <nav class="mb-2 flex justify-between align-top md:mb-12">
    <RouterLink :to="{ name: 'home' }" v-if="!hideLogo">
      <Logo responsive></Logo>
    </RouterLink>
    <div class="flex grow items-start justify-end">
      <!-- New Note -->
      <RouterLink v-if="showNewButton" :to="{ name: 'new' }">
        <CustomButton :iconPath="mdiPlusCircle" label="New Note" />
      </RouterLink>
      <!-- Menu -->
      <CustomButton
        class="ml-1"
        :iconPath="mdiMenu"
        label="Menu"
        @click="toggleMenu"
      />
      <PrimeMenu ref="menu" :model="menuItems" :popup="true" />
    </div>
  </nav>
</template>

<script setup>
import {
  mdiLogout,
  mdiMagnify,
  mdiMenu,
  mdiMonitor,
  mdiNoteMultiple,
  mdiPlusCircle,
  mdiMessageProcessing,
  mdiBookPlus,
} from "@mdi/js";
import { computed, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import CustomButton from "../components/CustomButton.vue";
import Logo from "../components/Logo.vue";
import PrimeMenu from "../components/PrimeMenu.vue";
import { authTypes, params, searchSortOptions } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { toggleTheme } from "../helpers.js";
import { clearStoredToken } from "../tokenStorage.js";

const globalStore = useGlobalStore();
const menu = ref();
const router = useRouter();

defineProps({
  hideLogo: Boolean,
});

const emit = defineEmits(["toggleSearchModal"]);

const menuItems = [
  {
    label: "Search",
    icon: mdiMagnify,
    command: () => emit("toggleSearchModal"),
    keyboardShortcut: "/",
  },
  {
    label: "All Notes",
    icon: mdiNoteMultiple,
    command: () =>
      router.push({
        name: "search",
        query: {
          [params.searchTerm]: "",
          [params.sortBy]: searchSortOptions.title,
        },
      }),
  },
  {
    label: "Chat",
    icon: mdiMessageProcessing,
    command: () =>
      router.push({
        name: "chat",
      }),
  },
  {
    label: "Workspace",
    icon: mdiBookPlus,
    command: () =>
      router.push({
        name: "workspace",
      }),
  },
  {
    label: "Toggle Theme",
    icon: mdiMonitor,
    command: toggleTheme,
  },
  {
    separator: true,
    visible: showLogOutButton,
  },
  {
    label: "Log Out",
    icon: mdiLogout,
    command: logOut,
    visible: showLogOutButton,
  },
];

const showNewButton = computed(() => {
  return globalStore.config.authType !== authTypes.readOnly;
});

function logOut() {
  clearStoredToken();
  router.push({ name: "login" });
}

function toggleMenu(event) {
  menu.value.toggle(event);
}

function showLogOutButton() {
  return ![authTypes.none, authTypes.readOnly].includes(globalStore.config.authType);
}
</script>
