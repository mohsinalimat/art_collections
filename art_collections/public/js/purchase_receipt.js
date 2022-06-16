frappe.ui.form.on("Purchase Receipt", {
    refresh: (frm) => {
        if (!frm.doc.is_return && frm.doc.status != "Closed") {
            if (frm.doc.docstatus == 0) {

                frappe.db.get_list('Purchase Receipt Item', {
                    fields: ['ref_supplier_packing_list_art'],
                    filters: {
                        'ref_supplier_packing_list_art': ['!=', ''],
                        'docstatus': ['!=', '2'],
                    },
                }).then(records => {
                    console.log(records);
                    let rec = []
                    records.forEach(element => {
                        if (rec.includes(element.ref_supplier_packing_list_art)) {

                        } else {
                            rec.push(element.ref_supplier_packing_list_art)

                        }
                    })
                    frm.add_custom_button(__('Supplier Packing List'),
                        function () {

                            if (!frm.doc.supplier) {
                                frappe.throw({
                                    title: __("Mandatory"),
                                    message: __("Please Select a Supplier")
                                });
                            }
                            erpnext.utils.map_current_doc({
                                method: "art_collections.art_collections.doctype.supplier_packing_list_art.supplier_packing_list_art.make_purchase_receipt",
                                source_doctype: "Supplier Packing List Art",
                                target: frm,
                                setters: {
                                    supplier: frm.doc.supplier,
                                },
                                get_query_filters: {
                                    docstatus: 1,
                                    name: ["not in", rec],
                                }
                            })
                        }, __("Get Items From"));
                })
            }
        }

		$('div').find('.document-link[data-doctype="Art Shipment"]').remove();
		if (frm.is_new() == undefined) {
			frappe.call('art_collections.purchase_receipt_controller.get_connected_shipment', {
				purchase_receipt: frm.doc.name
			}).then(r => {
				console.log(r,'r')
				if (r.message && r.message != undefined) {
					let count=r.message.length
					let link = $(`
			<div class="document-link" data-doctype="Art Shipment">
				<div class="document-link-badge" data-doctype="Art Shipment"> <span class="count">${count}</span> <a
					class="badge-link">Art Shipment</a> </div> <span class="open-notification hidden"
				title="Open Art Shipment"> </span></div>
			`);

					link.on('click', function () {
						frappe.route_options = {
							'name': ['in', r.message]
						};
						frappe.set_route("List", "Art Shipment", "List");

					})
					$('div').find('.document-link[data-doctype="Supplier Packing List Art"]').after(link);
				}
			})
		}        

    }
})