frappe.ui.form.on("Purchase Receipt", {
    refresh: (frm) => {
        if (!frm.doc.is_return && frm.doc.status != "Closed") {
            if (frm.doc.docstatus == 0) {

                frappe.db.get_list('Purchase Receipt Item', {
                    fields: ['ref_supplier_packing_list_art'],
                    filters: {
                        'ref_supplier_packing_list_art': ['!=', '']
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
    }
})