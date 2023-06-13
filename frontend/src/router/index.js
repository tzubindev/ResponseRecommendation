import { createWebHistory, createRouter } from "vue-router";
import App from "@/App.vue";
import Manage from "@/views/manage.vue";
import Context from "@/views/context.vue";
import Label from "@/views/label.vue";

const routes = [
	{
		path: "/",
		name: "App",
		component: App,
	},
	{
		path: "/manage",
		name: "Manage",
		component: Manage,
	},
	{
		path: "/context",
		name: "Context",
		component: Context,
	},
	{
		path: "/label",
		name: "Label",
		component: Label,
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

export default router;
