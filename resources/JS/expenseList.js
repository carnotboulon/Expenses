/*
$(document).on("pagecreate", "#expenseSummary", function(){
    $("#expenseSummary .ui-checkbox label")[1].click();     //Category
    $("#expenseSummary .ui-checkbox label")[5].click();     //Paid with
    $("#expenseSummary .ui-checkbox label")[6].click();     //Recorded By
    $("#expenseSummary .ui-checkbox label")[7].click();     //Recorded On
});
*/


$(function() {
    //Side Nav bar init.
    $(".button-collapse").sideNav();
    
    //Modal initialisation and options.
    //('.modal').modal();
    
    
    
    function openModal()
    {
        $('#modal1').modal('open');
        
    }
    
    
    $('.modal').modal({
        dismissible: true, // Modal can be dismissed by clicking outside of the modal
        opacity: .5, // Opacity of modal background
        in_duration: 300, // Transition in duration
        out_duration: 200, // Transition out duration
        starting_top: '80%', // Starting top style attribute
        ending_top: '20%', // Ending top style attribute
        //ready: function(modal, trigger) { // Callback for Modal open. Modal and trigger parameters available.
        //    alert("Ready");
        //    console.log(modal, trigger);
        //},
        //complete: function() { alert('Closed'); } // Callback for Modal close
        }
    );

    
    $('.confirmation').on('click', function () {
        return confirm('Are you sure you want to delete this expense?');
    });
    
    
    
    
    
/*
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
*/
    
});//end of master function.


