frappe.ui.form.on('Data Import', {

    refresh: function (frm) {

    },

    download_item_template: function (frm) {
        open_url_post(
            '/api/method/art_collections.controllers.item_import.download_template',
            {
                data_import_name: frm.doc.name
            }
        );
    }

});
