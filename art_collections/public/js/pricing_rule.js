frappe.ui.form.on('Pricing Rule', {
    item_flag_icon_art: function (frm) {
		frm.toggle_reqd("valid_from", frm.doc.item_flag_icon_art);
		frm.toggle_reqd("valid_upto", frm.doc.item_flag_icon_art);
	},
    validate: function (frm) {
		frm.toggle_reqd("valid_from", frm.doc.item_flag_icon_art!=undefined);
		frm.toggle_reqd("valid_upto", frm.doc.item_flag_icon_art!=undefined);
	},	

 });