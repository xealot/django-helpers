from models import FormDef, SavedValue, Field
from utilities import dbform_factory

"""
//Reference JS implementation for Radio Groups
//Radio Group Handlers
    (function(){
        function updateTabs(){
            $('div.radiogroup input[type=radio]').each(function(i, ele){
                var e = $(ele);
                var name = e.attr('id').match(/^id_(.*)_.+$/)[1];
                var tabname = '#rgtab_' + name + '_' + e.attr('value');
                var tab = $(tabname);
                if (tab) {
                    if (e.is(':checked') === true) {
                        //Show Tab
                        tab.show(200);
                        e.parentsUntil('li').parent().addClass('selected');
                    } else {
                        //Hide Tab
                        tab.hide();
                        e.parentsUntil('li').parent().removeClass('selected');
                    }
                }
            });
        }
    
        $('div.radiogroup input[type=radio]').change(function(e){updateTabs();});
        updateTabs();
    })();


//Reference JS implementation for IMAGE FIELD in form.
//Advanced Image Widget Handlers
    (function(){
        //Create click handlers
        function updateDBFI(elem) {
            var elem = $(elem);
            var container = elem.parentsUntil('.dbfi').parent();

            container.find('.dbfi_display .dbfi_action').each(function(i, e){
                var e = $(e);
                if (e.is(elem.attr('href'))) {
                    e.show();
                    e.find(':input').removeAttr('disabled');
                    
                    if (elem.parent().is('.dbfi_choices')) {
                        container.find('.dbfi_cancel').show();
                        container.find('.dbfi_choices').hide();
                    } else {
                        container.find('.dbfi_cancel').hide();
                        container.find('.dbfi_choices').show();
                    }

                } else {
                    e.hide();
                    e.find(':input').attr('disabled', 'disabled');                    
                }
                
            });
        }
        
        $('.dbfi .dbfi_choices a, .dbfi .dbfi_cancel a').click(function(e){
            e.preventDefault();
            updateDBFI(e.target);
        });
    })()
"""