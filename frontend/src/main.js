import { createApp } from "vue"; // in Vue 3
import App from "./App.vue";
import "./tailwind.css";
import router from "./router";

const app = createApp(App).use(router);

app.mount("#app");
