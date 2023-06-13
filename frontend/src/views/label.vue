<template>
	<header class="w-full h-auto flex justify-start items-center bg-indigo-500">
		<button @click.prevent="goBack" class="py-4 ml-8 pr-3 outline-none">
			<svg fill="#ffffff" height="20px" width="20px" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 219.151 219.151" xml:space="preserve" stroke="#ffffff">
				<g id="SVGRepo_bgCarrier" stroke-width="0"></g>
				<g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
				<g id="SVGRepo_iconCarrier">
					<g>
						<path
							d="M109.576,219.151c60.419,0,109.573-49.156,109.573-109.576C219.149,49.156,169.995,0,109.576,0S0.002,49.156,0.002,109.575 C0.002,169.995,49.157,219.151,109.576,219.151z M109.576,15c52.148,0,94.573,42.426,94.574,94.575 c0,52.149-42.425,94.575-94.574,94.576c-52.148-0.001-94.573-42.427-94.573-94.577C15.003,57.427,57.428,15,109.576,15z"
						></path>
						<path
							d="M94.861,156.507c2.929,2.928,7.678,2.927,10.606,0c2.93-2.93,2.93-7.678-0.001-10.608l-28.82-28.819l83.457-0.008 c4.142-0.001,7.499-3.358,7.499-7.502c-0.001-4.142-3.358-7.498-7.5-7.498l-83.46,0.008l28.827-28.825 c2.929-2.929,2.929-7.679,0-10.607c-1.465-1.464-3.384-2.197-5.304-2.197c-1.919,0-3.838,0.733-5.303,2.196l-41.629,41.628 c-1.407,1.406-2.197,3.313-2.197,5.303c0.001,1.99,0.791,3.896,2.198,5.305L94.861,156.507z"
						></path>
					</g>
				</g>
			</svg>
		</button>
		<div class="text-white">Manage Label Data</div>
	</header>
	<main>
		<div class="bg-white">
			<div class="px-4 sm:px-6 lg:px-8">
				<div class="sm:flex sm:justify-end">
					<div class="mt-4 sm:mt-5 sm:flex sm:w-full sm:space-x-4 space-x-0 space-y-3 sm:space-y-0">
						<input
							v-model="searchQuery"
							type="text"
							name="label"
							id="label"
							class="block w-full rounded-md border-0 py-2 bg-white text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 outline-none pl-3"
							placeholder="Search Label Name"
						/>
						<button
							@click.prevent="showAddModal"
							type="button"
							class="lg:w-1/6 w-full block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
						>
							Add Data
						</button>
					</div>
				</div>
				<div class="mt-8 flow-root bg-indigo-200 p-4 rounded-lg">
					<div class="-mx-4 -my-2 sm:-mx-6 lg:-mx-8">
						<div class="w-full py-2 align-middle">
							<table class="w-full border-separate border-spacing-0 table-fixed border-white">
								<thead>
									<tr>
										<th scope="col" class="sticky top-0 z-10 border-b border-white py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6 lg:pl-8">Label Id</th>
										<th scope="col" class="sticky top-0 z-10 border-b border-white py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6 lg:pl-8">Label Name</th>
										<th scope="col" class="sticky top-0 z-10 border-b border-white py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6 lg:pl-8">Label Keywords</th>
										<th scope="col" class="sticky top-0 z-10 border-b border-white py-3.5 pl-3 pr-4 sm:pr-6 lg:pr-8">
											<span class="sr-only">Delete</span>
										</th>
										<th scope="col" class="sticky top-0 z-10 border-b border-white py-3.5 pl-3 pr-4 sm:pr-6 lg:pr-8">
											<span class="sr-only">Edit</span>
										</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="data in filteredTableData" :key="data.label">
										<td class="border-b border-white py-4 pl-4 pr-3 text-sm font-medium text-gray-500 sm:pl-6 lg:pl-8 text-left">{{ data.label }}</td>
										<td class="break-words text-justify border-b border-white py-4 pl-4 pr-3 text-sm font-medium text-gray-500 sm:pl-6 lg:pl-8">{{ data.type }}</td>
										<div class="inline-grid grid-cols-2 gap-4 w-full border-b border-white pl-4 py-4">
											<span v-for="label in data.Keywords" :key="label" class="text-xs font-semibold rounded-md bg-indigo-600 text-white py-2 col-span-1">{{ label }}</span>
										</div>

										<td class="border-b border-white relative whitespace-nowrap py-4 pr-4 pl-3 text-center text-sm font-medium sm:pr-8 lg:pr-8">
											<button class="text-indigo-600 hover:text-indigo-900" @click.prevent="handlePost('d', [data.label])">Delete</button>
										</td>
										<td class="border-b border-white relative whitespace-nowrap py-4 pr-4 pl-3 text-center text-sm font-medium sm:pr-8 lg:pr-8">
											<button @click.prevent="showEditModal([data.label, data.type, data.Keywords])" class="text-indigo-600 hover:text-indigo-900">Edit</button>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</div>
			</div>
		</div>
		<modal v-if="showModal" :title="modalTitle">
			<form @submit.prevent="submitLabel">
				<div class="grid grid-cols-1 gap-2">
					<div class="grid grid-cols-3 space-y-3">
						<div class="flex justify-left items-center px-3"><label for="labels">Label Name</label></div>
						<input type="text" class="h-[50px] col-span-2 outline-none active:outline-none bg-transparent border border-gray-400 p-2 rounded-lg" v-model="labelName" />
						<div class="flex justify-left items-center px-3"><label for="labels">Keywords</label></div>
						<div class="relative mt-2 flex items-center col-span-2">
							<input type="text" class="h-[50px] col-span-2 outline-none active:outline-none bg-transparent border border-gray-400 p-2 rounded-lg w-full" v-model="newKeyword" />
							<div class="absolute inset-y-0 right-0 flex py-1.5 pr-1.5">
								<button class="inline-flex items-center rounded border border-gray-200 px-2 hover:bg-indigo-600 hover:text-white font-sans text-xs text-gray-400" @click="addKeyword(newKeyword)">Add</button>
							</div>
						</div>
						<div class="inline-grid grid-cols-3 gap-4 w-full border-b border-white pl-4 py-4 col-span-3">
							<span v-for="(keyword, index) in labelKeywords" :key="index" class="text-xs font-semibold rounded-md bg-indigo-600 text-white py-2 col-span-1 hover:bg-red-200 hover:text-red-600 hover:border-transparent transition cursor-pointer" @click="removeKeyword(index)">{{
								keyword
							}}</span>
						</div>
					</div>
				</div>
				<div class="mt-10 flex justify-end w-full gap-2">
					<button class="p-2 px-4 text-indigo-600 rounded-lg font-bold border border-indigo-600 hover:bg-red-200 hover:text-red-600 hover:border-transparent transition" @click.prevent="cancelSubmit">Cancel</button>
					<button class="p-2 px-4 text-white rounded-lg font-bold bg-indigo-600" @click="handlePost(this.mode)" type="submit">Submit</button>
				</div>
			</form>
		</modal>
	</main>
</template>

<script>
import modal from "../components/modal.vue";
export default {
	components: { modal },
	name: "Label",
	data() {
		return {
			showModal: false,
			isModalCancelled: false,
			modalTitle: null,
			searchQuery: "",
			labelData: [],
			labelNo: null,
			labelName: null,
			newKeyword: "",
			labelKeywords: [],
			mode: null,
		};
	},
	methods: {
		addKeyword(keyword) {
			if (this.newKeyword !== this.labelName) {
				keyword = keyword.replace(" ", "_").toLowerCase();
				this.labelKeywords.push(keyword);
				this.newKeyword = null;
			}
		},
		removeKeyword(index) {
			this.labelKeywords.splice(index, 1);
		},
		showEditModal(d) {
			this.showModal = !this.showModal;
			this.modalTitle = "Edit Details";
			this.mode = "m";
			this.labelNo = d[0];
			this.labelName = d[1];
			this.labelKeywords = d[2];
		},
		showAddModal() {
			this.showModal = !this.showModal;
			this.modalTitle = "Add Details";
			this.mode = "a";
		},
		cancelSubmit() {
			this.showModal = false;
			this.isModalCancelled = true;
			this.labelName = null;
			this.newKeyword = null;
			this.labelKeywords = null;
			this.mode = "";
			this.modalTitle = "";
		},
		goBack() {
			this.$router.go(-1);
		},
		async handlePost(mode, d = null) {
			if (mode === "a") {
				const data = {
					mode: mode,
					data: [this.labelName, this.labelKeywords],
				};
				try {
					const response = await fetch("http://127.0.0.1:5000/label_data/update", {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
						},
						body: JSON.stringify(data),
					});
					const responseData = await response.json();
					console.log(responseData);
				} catch (error) {
					console.error(error);
				}
			} else if (mode === "d") {
				const data = {
					mode: mode,
					data: d,
				};
				console.log(data);
				try {
					const response = await fetch("http://127.0.0.1:5000/label_data/update", {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
						},
						body: JSON.stringify(data),
					});
					const responseData = await response.json();
					console.log(responseData);
				} catch (error) {
					console.error(error);
				}
			} else if (mode === "m") {
				const data = {
					mode: mode,
					data: [this.labelNo, this.labelName, this.labelKeywords],
				};
				try {
					const response = await fetch("http://127.0.0.1:5000/label_data/update", {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
						},
						body: JSON.stringify(data),
					});

					const responseData = await response.json();

					console.log(responseData);
				} catch (error) {
					console.error(error);
				}
			}
			this.labelKeywords = null;
			this.newKeyword = null;
			this.labelName = null;
			this.showModal = false;
			this.GetData();
		},
		GetData() {
			const API_BASE = "http://127.0.0.1:5000/label_data";
			const requestOptions = {
				method: "GET",
				headers: { "Content-Type": "application/json" },
			};
			fetch(API_BASE, requestOptions)
				.then((response) => response.json())
				.then((data) => {
					const jsonLabelData = data.response.map((row) => {
						return {
							label: row.label,
							type: row.type,
							Keywords: row.keywords,
						};
					});
					this.labelData = jsonLabelData;
				})
				.catch((error) => {
					console.error(error);
				});
		},
	},
	computed: {
		filteredTableData() {
			return this.labelData.filter((labelData) => {
				if (labelData.type !== undefined && labelData.type.toLowerCase().includes(this.searchQuery.toLowerCase())) {
					return true;
				}
				return false;
			});
		},
	},
	mounted() {
		this.GetData();
	},
};
</script>
