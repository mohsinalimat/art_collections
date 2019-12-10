frappe.ui.form.on('Issue', {
	validate: function (frm) {
		frm.set_value('subject', frm.doc.issue_type)
	},
    issue_type_category_art: function (frm) {

		frm.set_query('issue_type', function(doc) {
			return {
				filters: {
					"category_art": frm.doc.issue_type_category_art
				}
			};
		});
	},
		issue_type: function (frm) {
			frm.set_value('subject', frm.doc.issue_type)	
		}
 });