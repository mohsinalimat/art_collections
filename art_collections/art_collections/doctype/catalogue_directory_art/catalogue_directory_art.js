// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Catalogue Directory Art', {
	setup: function (frm) {
		frm.set_value('is_group', 1)
		frm.set_df_property('parent_catalogue_directory_art', 'reqd', 1)
	},
	onload_post_render: function(frm) {
		frm.get_field("items_in_universe").grid.set_multiple_add("item");
	},
	onload: function (frm) {
		frm.list_route = "Tree/Catalogue Directory Art";
		frm.fields_dict['parent_catalogue_directory_art'].get_query = function (doc, cdt, cdn) {
			return {
				filters: [
					['Catalogue Directory Art', 'is_group', '=', 1],
					['Catalogue Directory Art', 'name', '!=', doc.catalogue_directory_art_name]
				]
			}
		}
	},
	validate: function (frm) {
		frm.set_value('is_group', 1)
	},
	node_type: function (frm) {
		if (frm.doc.node_type == 'Root') {
			frm.set_df_property('parent_catalogue_directory_art', 'reqd', 0)
			frm.set_value('catalogue_directory_art_name', 'Catalogues')
			frm.set_value('route', 'catalogues')
		} else {
			frm.set_df_property('parent_catalogue_directory_art', 'reqd', 1)
		}
	},
	refresh: function (frm) {
		frm.trigger("set_root_readonly");
		frm.add_custom_button(__("Catalogue Directory Art Tree"), function () {
			frappe.set_route("Tree", "Catalogue Directory Art");
		});

	},
	set_root_readonly: function (frm) {
		// read-only for root item group
		frm.set_intro("");
		if (!frm.doc.parent_catalogue_directory_art) {
			frm.set_read_only();
			frm.set_intro(__("This is a root item group and cannot be edited."), true);
		}
	},

	page_name: frappe.utils.warn_page_name_change
});
frappe.ui.form.on('Item Universe Page Art', {
	// check page no is in universe page range
	item_page_no: function (frm, cdt, cdn) {
		console.log('in')
		let row = frappe.get_doc(cdt, cdn);
		let from = frm.doc.universe_page_range_start
		let to = frm.doc.universe_page_range_end
		if (row.item_page_no && from != null && to != null) {
			if ((row.item_page_no < from || row.item_page_no > to)) {
				frappe.throw(__('Item Page # {0} is not between {1} - {2}', [row.item_page_no, from, to]))

			}
		} else {
			frappe.msgprint({
				title: __('Missing universe page number'),
				indicator: 'yellow',
				message: __('Please set Universe start and end page number')
			})
		}

	}
});