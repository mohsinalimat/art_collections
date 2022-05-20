frappe.ui.form.on('Data Import', {

    refresh: function (frm) {
    },

    download_item_template: function (frm) {

        frm.data_exporter = new npro.utils.DataExporter(
            frm.doc.reference_doctype,
            frm.doc.import_type
        );
    }

});

