<template>
	<div class="modal-container">
		<div class="modal-overlay"></div>
		<div class="modal">
			<div class="modal-header">
				<h3>{{ title }}</h3>
			</div>
			<div class="modal-body">
				<slot></slot>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "Modal",
	props: {
		title: String,
	},
};
</script>

<style scoped>
.modal-container {
	position: fixed;
	top: 0;
	left: 0;
	height: 100%;
	width: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 999;
}

.modal-overlay {
	position: absolute;
	top: 0;
	left: 0;
	height: 100%;
	width: 100%;
	background-color: rgba(0, 0, 0, 0.5);
}

.modal {
	background-color: white;
	padding: 1rem;
	width: 50%;
	min-width: 300px;
	max-width: 600px;
	border-radius: 4px;
	box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.5);
	z-index: 10;
}

.modal-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.modal-header h3 {
	margin: 0;
}

.modal-header button {
	background-color: transparent;
	border: none;
	font-size: 1.5rem;
	cursor: pointer;
}

.modal-body {
	margin-top: 1rem;
}
</style>
