$(function() {
    //Attach dble click handler on table elements.
    $('table tr').dblclick(function(event){
        console.log($(this).attr("id"));
        var that = $(this);
        //Updating popup text and link.
        $( "#popupDialog #delExpense").html($(this).children("td.object").html()+ "?");
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
        
        
    $('table tr').on('tap', function() {
        console.log($(this).attr("id"));
        var that = $(this);
        //Updating popup text and link.
        $( "#popupDialog #delExpense").html($(this).children("td.object").html()+ "?");
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


