//TODO: check value for all the fields before save.

$(function() {
    
    //Attach dble CLICK handler on table elements to delete the element.
    $('table tr').dblclick(function(event){
        if ($(this).attr("id") != "header"){
            console.log($(this).attr("id"));
            var that = $(this);
            //Updating popup text and link.
            $( "#popupDialog #delExpense").html($(this).children("td.object").html()+ "?");
            $( "#deleteBtn" ).unbind().click(
                function ()
                {
                    console.log("DIsabling:" + that.attr("id"));
                    that.remove();                               //removes it from the html page.
                    $.ajax("/disable?id="+that.attr("id"));      //removes it from DB.
                }
            );         
            $( "#popupDialog" ).popup( "open");
        }
        
    });
        
    //Attach dble TAP handler on table elements to delete the element.   
    $('table tr').on('tap', function() {
        if ($(this).attr("id") != "header"){
            console.log($(this).attr("id"));
            var that = $(this);
            //Updating popup text and link.
            $( "#popupDialog #delExpense").html($(this).children("td.object").html()+ "?");
            $( "#deleteBtn" ).unbind().click(
                function ()
                {
                    console.log("Disabling:" + that.attr("id"));
                    that.remove();                               //removes it from the html page.
                    $.ajax("/disable?id="+that.attr("id"));      //removes it from DB.
                }
            );         
            $( "#popupDialog" ).popup( "open");
        }
    });
        
    
});//end of master function.
//$("input:checkbox").prop('checked', $(this).prop("checked"));

