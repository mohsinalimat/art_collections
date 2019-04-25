// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('State', {
	refresh: function(frm) {

	},
	state:function(frm){
		if(!frm.doc.__islocal) {
				frm.rename_doc(frm.doctype,frm.docname,frm.state);

		}
	}
});
