$(document).on("pagecreate", "#expenseSummary", function(){
    $("#expenseSummary .ui-checkbox label")[2].click();
    $("#expenseSummary .ui-checkbox label")[5].click();
    $("#expenseSummary .ui-checkbox label")[6].click();
    $("#expenseSummary .ui-checkbox label")[7].click();
    $("#expenseSummary .ui-checkbox label")[8].click();
});

$(function() {
    
    //Attach dble CLICK handler on table elements to delete the element.
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
                $.ajax("/remove?id="+that.attr("id"));      //removes it from DB.
            }
        );         
        $( "#popupDialog" ).popup( "open");
        });
        
    //Attach dble TAP handler on table elements to delete the element.   
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
                $.ajax("/remove?id="+that.attr("id"));      //removes it from DB.
            }
        );         
        $( "#popupDialog" ).popup( "open");
        });
  
    
});//end of master function.


