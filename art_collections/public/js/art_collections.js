
$(document).ready(function () {

    frappe.realtime.on("show_email_dialog", function (args) {
        if (cur_frm) {
            let frm = cur_frm;
            if (args && args.doctype == frm.doctype && args.docname == frm.docname) {
                cur_frm.reload_doc().then(() => {
                    frappe.show_email_dialog(frm);
                });
            }
        }
    });
});



frappe.show_email_dialog = function (frm) {
    // show email dialog with pre-set values for default print format 
    // and email template and attach_print

    let composer = new frappe.views.CommunicationComposer({
        doc: frm.doc,
        frm: frm,
        subject: __(frm.meta.name) + ': ' + frm.docname,
        recipients: frm.doc.email || frm.doc.email_id || frm.doc.contact_email,
        attach_document_print: true,
        real_name: frm.doc.real_name || frm.doc.contact_display || frm.doc.contact_name
    });


    frappe.db.get_single_value('Art Collections Settings', 'sales_order_email_template')
        .then(email_template => {
            setTimeout(() => {
                composer.dialog.fields_dict['select_attachments'].$wrapper.find("input").attr("checked", "checked");
                composer.dialog.fields_dict['content'].set_value("");
                composer.dialog.set_values({
                    "email_template": email_template,
                    // "select_print_format": 'Art Collections Sales Order'
                });
            }, 900);
        });
}



frappe.require('/assets/js/data_import_tools.min.js', () => {
    frappe.provide('art_collections.utils')
    art_collections.utils.DataExporter = class CustomDataExporter {
        constructor(doctype, exporting_for) {
            this.doctype = doctype;
            this.exporting_for = exporting_for;
            frappe.model.with_doctype(doctype, () => {
                this.make_dialog();
            });
        }

        make_dialog() {

            this.dialog = new frappe.ui.Dialog({
                title: __('Export Data'),
                fields: [
                    {
                        fieldtype: 'Select',
                        fieldname: 'export_records',
                        label: __('Export Type'),
                        options: [
                            {
                                label: __('All Records'),
                                value: 'all'
                            },
                            {
                                label: __('Filtered Records'),
                                value: 'by_filter'
                            },
                            {
                                label: __('5 Records'),
                                value: '5_records'
                            },
                            {
                                label: __('Blank Template'),
                                value: 'blank_template'
                            }
                        ],
                        default: this.exporting_for === 'Insert New Records' ? 'blank_template' : 'all',
                        change: () => {
                            this.update_record_count_message();
                        }
                    },
                    {
                        fieldtype: 'HTML',
                        fieldname: 'filter_area',
                        depends_on: doc => doc.export_records === 'by_filter'
                    },],
                primary_action_label: __('Export'),
                primary_action: values => this.export_records(values),
            });

            this.make_filter_area();

            this.dialog.show();

            // end make dialog
        }

        make_filter_area() {
            this.filter_group = new frappe.ui.FilterGroup({
                parent: this.dialog.get_field('filter_area').$wrapper,
                doctype: this.doctype,
                on_change: () => {
                    this.update_record_count_message();
                }
            });
        }

        update_record_count_message() {
            // 
        }

        get_filters() {
            return this.filter_group.get_filters().map(filter => {
                return filter.slice(0, 4);
            });
        }

        export_records() {
            let method = '/api/method/art_collections.controllers.item_import.download_template';

            let multicheck_fields = this.dialog.fields
                .filter(df => df.fieldtype === 'MultiCheck')
                .map(df => df.fieldname);

            let values = this.dialog.get_values();

            let doctype_field_map = Object.assign({}, values);
            for (let key in doctype_field_map) {
                if (!multicheck_fields.includes(key)) {
                    delete doctype_field_map[key];
                }
            }

            let filters = null;
            if (values.export_records === 'by_filter') {
                filters = this.get_filters();
            }

            open_url_post(method, {
                data_import: cur_frm.doc.name,
                doctype: this.doctype,
                file_type: values.file_type,
                export_records: values.export_records,
                export_fields: doctype_field_map,
                export_filters: filters
            });
        }
    }


});


