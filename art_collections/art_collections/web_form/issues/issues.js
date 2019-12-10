frappe.ready(function () {
	// bind events here
	frappe.init_client_script = () => {
		try {
			frappe.web_form.on('issue_type', (field, value) => {
				frappe.web_form.set_value('subject', value);
			});
			frappe.web_form.validate = () => {
				let data = frappe.web_form.get_value('issue_type');
				frappe.web_form.set_value('subject', data);
			};

			frappe.web_form.on('issue_type_category_art', (field, value) => {
				filterIssueType(value);

				function filterIssueType(value) {
					let url='api/resource/Issue Type?filters=[["Issue Type","Category_Art","=","'+value+'"]]'
					$.ajax({
					url: url,
					success: function (result) {
						frappe.web_form.doc.issue_type=''
						var options = []
						for (var i = 0; i < result.data.length; i++) {
							options.push({
								"label": result.data[i].name,
								"value": result.data[i].name
							})

						}
						var field = frappe.web_form.get_field('issue_type');
						field._data = options;
						field.refresh();

					},
					error:function (opts) {
						console.log(opts,'-------------')
					}
					});
					};				
				});

		} catch (e) {
			console.error('Error in web form client script');
			console.error(e);
		}
	}
})