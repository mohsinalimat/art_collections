frappe.treeview_settings["Catalogue Directory Art"] = {
	fields: [
		{fieldtype:'Check', fieldname:'is_group', label:__('Is Group'),default:'1', reqd:true,
			description: __('')},		
		{fieldtype:'Check', fieldname:'show_in_website', label:__('Show In Website'),
			depends_on: "eval:in_list(['Universe','Catalogue','Catalogue Year'], doc.node_type)"},
			{fieldtype:'Int', fieldname:'year', label:__('Year'),
			depends_on: "eval:doc.node_type =='Catalogue Year'"}			

	],	
	ignore_fields:["parent_catalogue_directory_art"],
	refresh: function(treeview) {
		frm.set_value("show_in_website", "1");
		console.log("ref")
	},	
	onload: function (treeview) {
		treeview.make_tree();
	}
}