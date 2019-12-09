frappe.ready(function () {
	// bind events here
	frappe.init_client_script = () => {
		try {
			frappe.web_form.on('issue_type_art', (field, value) => {
				frappe.web_form.set_value('subject', value);
			});
			frappe.web_form.validate = () => {
				let data = frappe.web_form.get_value('issue_type_art');
				frappe.web_form.set_value('subject', data);
			};

		} catch (e) {
			console.error('Error in web form client script');
			console.error(e);
		}
	}
})