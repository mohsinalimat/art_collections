frappe.provide("frappe.treeview_settings")

frappe.treeview_settings["Catalogue Directory Art"] = {
	
	fields: [
		{fieldtype:'Check', fieldname:'is_group', label:__('Is A Group'), 
			description: __(''),reqd:1,	default:1},		
		{fieldtype:'Select', fieldname:'node_type', label:__('Node Type'),
		options: "Universe\nCatalogue",reqd:true,default:"Universe"},
		{fieldtype:'Data', fieldname:'catalogue_directory_art_name', label:__('Node Name'),reqd:true},
		{fieldtype:'Data', fieldname:'title', label:__('Website Name'),
		depends_on: "eval:in_list(['Universe','Catalogue','Root'], doc.node_type)"},
		{fieldtype:'Int', fieldname:'universe_page_range_start', label:__('Universe Page Start #'),
		depends_on: "eval:doc.node_type=='Universe'"},
		{fieldtype:'Int', fieldname:'universe_page_range_end', label:__('Universe Page End #'),
		depends_on: "eval:doc.node_type=='Universe'"},								
		{fieldtype:'Select', fieldname:'catalogue_type', label:__('Catalogue Type'),
		options: "\nPermanant\nFestif\nNo\u00ebl",depends_on:"eval:doc.node_type=='Catalogue'" },
		{fieldtype:'Check', fieldname:'show_in_website', label:__('Show In Website'),
			depends_on: "eval:in_list(['Universe','Catalogue','Root'], doc.node_type)",default:1},
		{fieldtype:'Int', fieldname:'year', label:__('Year'),
			depends_on: "eval:doc.node_type =='Catalogue'",description: __('Ex 2019')}			

	],	
	ignore_fields:["parent_catalogue_directory_art"],
	onload: function(treeview) {
		frappe.treeview_settings["Catalogue Directory Art"].treeview = {};
		$.extend(
		  frappe.treeview_settings["Catalogue Directory Art"].treeview,
		  treeview
		);
	  },
	toolbar: [
	  {
		label: __("Add Child"),
		condition: function(node) {
		  var me = frappe.treeview_settings["Catalogue Directory Art"].treeview;
		  return me.can_create && node.expandable && !node.hide_add;
		},
		click: function(node) {
		  custom_new_node(node);
		},
		btnClass: "hidden-xs"
	  }
	],
  
	extend_toolbar: true
  };
  
  var custom_new_node = function(node) {
	var me = frappe.treeview_settings["Catalogue Directory Art"].treeview;
	if (!(node && node.expandable)) {
	  frappe.msgprint(__("Select a group node first."));
	  return;
	}
  
	me.prepare_fields();
  
	// the dialog
	var d = new frappe.ui.Dialog({
	  title: __("New {0}", [__(me.doctype)]),
	  fields: me.fields
	});
  
	var args = $.extend({}, me.args);
	args["parent_" + me.doctype.toLowerCase().replace(/ /g, "_")] =
	  me.args["parent"];
  
	//   d.set_value("is_group", 0);
	d.set_values(args);
  
	// create
	d.set_primary_action(__("Create New"), function() {
	  var btn = this;
	  var v = d.get_values();
	  if (!v) return;
  
	  v.parent = node.label;
	  v.doctype = me.doctype;
  
	  if (node.is_root) {
		v["is_root"] = node.is_root;
	  } else {
		v["is_root"] = false;
	  }
  
	  d.hide();
	  frappe.dom.freeze(__("Creating {0}", [me.doctype]));
  
	  $.extend(args, v);
	  return frappe.call({
		method: me.opts.add_tree_node || "frappe.desk.treeview.add_node",
		args: args,
		callback: function(r) {
		  if (!r.exc) {
			if (node.expanded) {
			  me.tree.toggle_node(node);
			}
			me.tree.load_children(node, true);
		  }
		},
		always: function() {
		  frappe.dom.unfreeze();
		}
	  });
	});
	d.show();
  };
  
  