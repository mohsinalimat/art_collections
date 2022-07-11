frappe.ui.form.on("Request for Quotation", {

    refresh: function (frm) {

        add_custom_buttons(frm);

        frm.add_custom_button(__('Download RFQ Art PDF'), () => {
            var suppliers = [];
            const fields = [{
                fieldtype: 'Link',
                label: __('Select a Supplier'),
                fieldname: 'supplier',
                options: 'Supplier',
                reqd: 1,
                get_query: () => {
                    return {
                        filters: [
                            ["Supplier", "name", "in", frm.doc.suppliers.map((row) => { return row.supplier; })]
                        ]
                    }
                }
            }];

            frappe.prompt(fields, data => {
                var w = window.open(
                    frappe.urllib.get_full_url("/api/method/art_collections.request_for_quotation_controller.get_pdf?"
                        + "doctype=" + encodeURIComponent(frm.doc.doctype)
                        + "&name=" + encodeURIComponent(frm.doc.name)
                        + "&supplier=" + encodeURIComponent(data.supplier)
                        + "&no_letterhead=0"));
                if (!w) {
                    frappe.msgprint(__("Please enable pop-ups")); return;
                }
            },
                'Download RQF Art PDF for Supplier',
                'Download');
        },
            __("Tools"));

    }
    // 	item_code: function(frm, cdt, cdn) {
    // 		var row = locals[cdt][cdn];
    // 		if (row.item_code) {

    // 			frappe.call('art_collections.item_controller.get_qty_of_inner_cartoon', {
    // 			    item_code: row.item_code
    // 			}).then(r => {
    // 			    if (r.message) {
    // 			    	row.nb_selling_packs_in_inner_art=r.message
    // 			    }
    // 			})	

    // 			frappe.call('art_collections.item_controller.get_qty_of_outer_cartoon', {
    // 			    item_code: row.item_code
    // 			}).then(r => {
    // 			    if (r.message) {
    // 			    	row.nb_selling_packs_in_outer_art=r.message
    // 			    }
    // 			})

    // 		}

    // 	}

});

function add_custom_buttons(frm) {
    frappe.add_product_excel_button(frm, "art_collections.controllers.excel.request_for_quotation_excel._make_excel_attachment", "Download RFQ Excel", true)

}