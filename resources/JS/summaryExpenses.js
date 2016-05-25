$(function() {
    //Attach dble click handler on table elements.
    $('table tr').dblclick(function(event){
        var that = $(this);
        console.log($(this).attr("id"));
        //Updating popup text and link.
        $( "#popupdialog #delExpense").html($(this).children("td.object").html()+ "?");
        $( "#deleteBtn" ).unbind().click(
            function ()
            {
                console.log("Removing:" + that.attr("id"));
                that.remove();                               //removes it from the html page.
                $.ajax("/remove?exp="+that.attr("id"));      //removes it from DB.
            }
        );         
        $( "#popupDialog" ).popup( "open");
        });
    
});//end of master function.


