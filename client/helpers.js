import { ref } from 'vue';

export const themeState = ref(false);

export function getToastOptions(description, title, severity) {
  return {
    summary: title,
    detail: description,
    severity: severity,
    closable: false,
    life: 5000,
  };
}

export function setDarkThemeOn(save = true) {
  document.body.classList.add("dark");
  if (save) localStorage.setItem("darkTheme", "true");
  themeState.value = true;
}

export function setDarkThemeOff(save = true) {
  document.body.classList.remove("dark");
  if (save) localStorage.setItem("darkTheme", "false");
  themeState.value = false;
}

export function toggleTheme() {
  if (themeState.value) {
    setDarkThemeOff();
  } else {
    setDarkThemeOn();
  }
  // document.body.classList.contains("dark")
  //   ? setDarkThemeOff()
  //   : setDarkThemeOn();
}

export function loadTheme() {
  const storedTheme = localStorage.getItem("darkTheme");
  if (storedTheme === "true") {
    setDarkThemeOn(false);
  } else if (
    storedTheme === null &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    setDarkThemeOn(false);
  } else {
    setDarkThemeOff(false);
  }
}

// export function loadTheme() {
//   const storedTheme = localStorage.getItem("darkTheme");
//   if (storedTheme === "true") {
//     setDarkThemeOn();
//   } else if (
//     storedTheme === null &&
//     window.matchMedia("(prefers-color-scheme: dark)").matches
//   ) {
//     setDarkThemeOn(false);
//   }
// }
