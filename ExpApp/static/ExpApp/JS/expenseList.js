$(function() {
    //Side Nav bar init.
    $(".button-collapse").sideNav();
    
    //Hide comment for small screens.
    if ($(window).width() <= 600) 
    {
        $(".comment").hide();
    }
    
    
    //Modal windows.
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
    
    //Flash messages.
    $('.flash').delay(2000).hide("blind","linear");
    
    //Seach bar.
    $(".searchButton").on("click",function(){
        if ($("#search").is(":visible")) 
        {
            $("#search").hide("blind","linear");
        }
        else
        {
            $("#search").show();
        }
    });
   
});//end of master function.


