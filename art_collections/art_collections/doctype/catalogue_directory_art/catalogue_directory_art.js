// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Catalogue Directory Art', {
	// refresh: function(frm) {

	// }

	refresh: function() {
		frm.set_value("show_in_website", "1");
		console.log("ref")
	},

	onload: function (frm) {
		
	},	
});

//get query select territory
cur_frm.fields_dict['parent_catalogue_directory_art'].get_query = function(doc,cdt,cdn) {
	return{
		filters:[
			['Catalogue Directory Art', 'is_group', '=', 1],
			['Catalogue Directory Art', 'name', '!=', doc.node_name]
		]
	}
}