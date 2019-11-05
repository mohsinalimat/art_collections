frappe.ui.form.on('Issue', {
    issue_type_category_art: function (frm) {
		if (frm.doc.issue_type_category_art) {
			frappe.db.get_value('Issue Type', {'category_art': frm.doc.issue_type_category_art}, ['name'])
			.then(({ message }) => {
				var issue_type = message.name
				if ( issue_type ) {
					frm.set_value('issue_type', issue_type)	
				}
			});	
		}
    }
 });