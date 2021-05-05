frappe.ui.form.on('Item', {
   onload: function (frm) {
      if (frm.doc.item_code && frm.doc.is_pre_item_art == 0) {
         frm.trigger('set_average_daily_outgoing_art')
      }
      if (frm.is_new() == undefined && frm.doc.disabled == 0 && frm.doc.is_pre_item_art == 1 &&
         frm.doc.name.lastIndexOf("P", 1) == 0
      ) {
         frm.set_df_property('is_pre_item_art', 'read_only', 1)
         frm.add_custom_button(__('Convert Pre to Normal Item'), () => {
            frappe.call({
               method: "art_collections.api.convert_pre_to_normal_item",
               args: {
                  item_name: frm.doc.name,
               },
               callback: function (r) {
                  if (!r.exc && r.message != undefined) {
                     console.log(r)
                     let doctype = frm.doc.doctype
                     let docname = frm.doc.name
                     $(document).trigger('rename', [doctype, docname,
                        r.message
                     ]);
                     if (locals[doctype] && locals[doctype][docname])
                        delete locals[doctype][docname];
                  } else if (!r.exc && r.message == undefined) {
                     frappe.msgprint({
                        title: __('Pre Item rename failed.'),
                        message: __('Conversion failed for Pre Item. New id not found.'),
                        indicator: 'red'
                     });
                  }
               }
            });
         });
      }
      if (frm.is_new() == undefined && frm.doc.disabled == 0 && frm.doc.is_pre_item_art == 0 &&
         frm.doc.name.lastIndexOf("P", 1) != 0) {
         frm.set_df_property('is_pre_item_art', 'read_only', 1)
      }
   },
   is_pre_item_art: function (frm) {
      if (frm.doc.is_pre_item_art == 1 && frm.doc.item_name == undefined) {
         frm.set_df_property('item_name', 'reqd', 1)
      } else {
         frm.set_df_property('item_name', 'reqd', 0)
      }
   },
   before_save: function (frm) {
      if (frm.doc.is_pre_item_art == 1) {
         frm.set_value('item_code', 'pre')
      }
      console.log('1', frm.doc.barcodes.length, frm.doc.barcodes[0].barcode, frm.doc.barcodes[0].barcode_type)
      if (frm.doc.barcodes.length == 1) {
         if (frm.doc.barcodes[0].barcode == undefined && frm.doc.barcodes[0].barcode_type != "") {
            console.log('2')
            frm.doc.barcodes = []
         }
      }
   },
   refresh: function (frm) {
      if (frm.doc.__islocal == 1) {
         setTimeout(() => {
            frm.set_value('country_of_origin', 'China')
         }, 100);
      }
   },
   set_average_daily_outgoing_art: function (frm) {
      frappe.call({
         method: "art_collections.api.get_average_daily_outgoing_art",
         args: {
            item_code: frm.doc.item_code,
         },
         callback: function (r) {
            if (!r.exc) {
               console.log(r)
               if (r.message) {
                  if (r.message.average_daily_outgoing_art != null && r.message.average_daily_outgoing_art != 0) {
                     frm.set_value('average_daily_outgoing_art', r.message.average_daily_outgoing_art)
                     frm.save()
                  } else {
                     frm.set_value('average_daily_outgoing_art', 0)
                     frm.save()
                  }
               }
            }
         }
      });
   }
});