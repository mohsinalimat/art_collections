frappe.ui.form.on('Item', {
   validate:function (frm) {
      if (frm.doc.nb_selling_packs_in_outer_art!=0 && frm.doc.nb_selling_packs_in_inner_art!=0) {
         frm.doc.nb_inner_in_outer_art=flt(frm.doc.nb_selling_packs_in_outer_art/frm.doc.nb_selling_packs_in_inner_art)
      }else{
         frm.doc.nb_inner_in_outer_art=flt(0.0)
      }
      frm.doc.cbm_per_outer_art=flt(frm.doc.outer_heigth_art*frm.doc.outer_width_art*frm.doc.outer_length_art)
   },
   onload: function (frm) {
      if (frm.doc.item_code && frm.doc.is_pre_item_art == 0) {
      //  temp disable
         // frm.trigger('set_average_values')
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
      // if (frm.doc.is_pre_item_art == 1) {
      //    frm.set_value('item_code', 'pre')
      // }
      if (frm.doc.barcodes && frm.doc.barcodes.length == 1) {
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
      if (frm.doc.__islocal == undefined && frm.doc.has_variants==0 && frm.doc.variant_of==undefined && frm.doc.is_fixed_asset==0 && frm.doc.is_stock_item==1) {
         frappe.call({
            method: "art_collections.item_controller.get_item_art_dashboard_data",
            args: {
               item_code: frm.doc.name,
            },
            callback: function (r) {
               if (!r.exc) {
                  console.log(r)
                  if (r.message) {
                     frm.set_intro(r.message,false)
                  }}}})
      }      
   },
   set_average_values: function (frm) {
      frappe.call({
         method: "art_collections.api.get_average_values_for_item",
         args: {
            item_code: frm.doc.item_code,
         },
         callback: function (r) {
            if (!r.exc) {
               console.log(r)
               let dirty = false
               if (r.message) {
                  if (r.message.average_delivery_days != null && r.message.average_delivery_days != 0) {
                     frm.set_value('average_delivery_days_art', r.message.average_delivery_days)
                     dirty = true
                  } else {
                     frm.set_value('average_delivery_days_art', 0)
                     dirty = true
                  }
                  if (r.message.average_daily_outgoing_art != null && r.message.average_daily_outgoing_art != 0) {
                     frm.set_value('average_daily_outgoing_art', r.message.average_daily_outgoing_art)
                     dirty = true
                  } else {
                     frm.set_value('average_daily_outgoing_art', 0)
                     dirty = true
                  }
                  if (dirty == true) {
                     frm.save()
                  }
               }
            }
         }
      });
   },
   populate_website_specifications_art: function (frm) {
      let row1_desc,row2_desc,row3_desc=undefined

      if (frm.doc.qty_in_selling_pack_art) {
            row1_desc=frm.doc.qty_in_selling_pack_art+__(' qty per pack for this item in ')+ frm.doc.item_group + __(' group')
      }
      if (frm.doc.main_design_color_art) {
            row2_desc=frm.doc.main_design_color_art+__(' is the main color')
      }
      if (frm.doc.length_art) {
            row3_desc=(frm.doc.length_art || 0 )+ __('L x ') + (frm.doc.width_art || 0 )+ __('W x ') +(frm.doc.thickness_art || 0 ) +__('T')
      }
      if(row1_desc){
         let row1=frm.add_child('website_specifications')
         row1.label=__('Qty per pack')
         row1.description=row1_desc
      }
      if(row2_desc){
         let row2=frm.add_child('website_specifications')
         row2.label=__('Main Color')
         row2.description=row2_desc
      }
      if(row3_desc){
         let row3=frm.add_child('website_specifications')
         row3.label=__('Product Dimension')
         row3.description=row3_desc
      }    
      frm.refresh_field('website_specifications')        
   }
});