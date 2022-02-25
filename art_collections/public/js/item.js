frappe.ui.form.on('Item', {
   qty_in_selling_pack_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   item_group:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   main_design_color_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },      
   length_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   width_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   thickness_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   product_size_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },
   product_size_group_art:function (frm) {
      if (frm.is_new() == 1) {
      frm.set_value("item_name", new_item_name(frm))
      }
   },         
   validate:function (frm) {

      for (let index = 0; index < frm.doc.existing_product_art_work_cf.length; index++) {
         const row = frm.doc.existing_product_art_work_cf[index];
         if (row.art_work_attachment==undefined){
            frappe.throw(__("Art Work Attachment is required on row # <b>{0}</b>", [row.idx]));
         }
         
      }

      frm.doc.cbm_per_outer_art=flt(frm.doc.outer_heigth_art*frm.doc.outer_width_art*frm.doc.outer_length_art)

      // if (frm.is_new() == 1) {
      //    let custom_item_name = []
      //    if (frm.doc.qty_in_selling_pack_art) {
      //       custom_item_name.push(frm.doc.qty_in_selling_pack_art)
      //    }
      //    if (frm.doc.item_group) {
      //       custom_item_name.push(frm.doc.item_group)
      //    }
      //    if (frm.doc.main_design_color_art) {
      //       custom_item_name.push(frm.doc.main_design_color_art)
      //    }
      //    if (frm.doc.length_art) {
      //       custom_item_name.push(frm.doc.length_art)
      //    }
      //    if (frm.doc.width_art) {
      //       custom_item_name.push(frm.doc.width_art)
      //    }
      //    if (frm.doc.thickness_art) {
      //       custom_item_name.push(frm.doc.thickness_art)
      //    }
      //    custom_item_name = custom_item_name.join(" ")
      //    if (custom_item_name) {
      //       return new Promise((resolve) => {
      //          return frappe.confirm(
      //             __(
      //                "Are you sure you want change item name? <br>Existing : <b>{0}</b> <br>New      : <b>{1}</b>",
      //                [frm.doc.item_name,custom_item_name]
      //             ),
      //             () => {
      //                // ok
      //                frm.doc.item_name = custom_item_name
      //                resolve("ok");
      //             },
      //             () => {
      //                // not ok
      //                resolve("not ok");
      //             }
      //          );
      //       });
      //    }
      // }

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
      if (frm.doc.__islocal == undefined && frm.doc.is_stock_item){
			frm.add_custom_button(__("Purchase History"), function() {
				frappe.route_options = {
					"item_code": frm.doc.name
				}
				frappe.set_route("query-report", "Item-wise Purchase History with-filter");
			}, __("View"));         
      }

   },
   is_existing_product_cf: function (frm) {
      if (frm.doc.is_existing_product_cf==1) {
         let row1 = frm.add_child('existing_product_art_work_cf')
         row1.art_work_name = __('Inner')
         let row2 = frm.add_child('existing_product_art_work_cf')
         row2.art_work_name = __('Outer')
         let row3 = frm.add_child('existing_product_art_work_cf')
         row3.art_work_name = __('Selling Pack')
         frm.refresh_field('existing_product_art_work_cf')         
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

});

frappe.ui.form.on('Product Packing Dimensions', {
	uom: function(frm, cdt, cdn) {
      let row=locals[cdt][cdn]
      console.log(row.weight)
      if (row.uom==frm.doc.stock_uom && frm.doc.weight_per_unit && row.weight==undefined) {
		   frappe.model.set_value(cdt, cdn, 'weight', frm.doc.weight_per_unit);
      }
	}
});

function new_item_name(frm) {
   
   let custom_item_name=[]
   if (frm.doc.qty_in_selling_pack_art) {
      custom_item_name.push(frm.doc.qty_in_selling_pack_art)
   }
   if (frm.doc.item_group) {
      custom_item_name.push(frm.doc.item_group)
   }
   if (frm.doc.main_design_color_art) {
      custom_item_name.push(frm.doc.main_design_color_art)
   }
   if (frm.doc.length_art) {
      custom_item_name.push(frm.doc.length_art)
   }
   if (frm.doc.width_art) {
      custom_item_name.push(frm.doc.width_art)
   }         
   if (frm.doc.thickness_art) {
      custom_item_name.push(frm.doc.thickness_art)
   } 
   if (frm.doc.product_size_art) {
      custom_item_name.push(frm.doc.product_size_art)
   }
   if (frm.doc.product_size_group_art) {
      custom_item_name.push(frm.doc.product_size_group_art)
   }       
   custom_item_name=custom_item_name.join(" ")
   return custom_item_name
}