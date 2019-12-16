frappe.ui.form.on("POS Profile", "onload", function(frm) {

	frm.call({
		method: "art_collections.api.pos_so_get_series",
		callback: function(r) {
			if(!r.exc) {
				set_field_options("pos_so_naming_series_art", r.message);
			}
		}
	});
});