frappe.ui.form.on('Data Import', {

    refresh: function (frm) {
    },

    download_item_template: function (frm) {

        frm.data_exporter = new art_collections.utils.DataExporter(
            frm.doc.reference_doctype,
            frm.doc.import_type
        );
    }

});

