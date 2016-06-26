//TODO: check value for all the fields before save.

$(function() {
  
    //OBJECT INPUT
    //Autocomplete to buy object field.
    //Add the selected option to the text input
    //and hides the autocomplete list when option selected.
    $(".autocomplete").click(
        function()
        {
            //console.log("Clicked link: "+$(this).text());
            $("#articleValue").val($(this).text());
            $(this).parent().parent().children().addClass("ui-screen-hidden"); //hide the autocomplete list.
        }
    );
    //CATEGORIES SELECTION. Add the selected option to the text input
    $("input:checkbox[name='catValues']").click(
        function()
        {
            $("#catValue").val($(this).siblings("label").text());
        }
    );
  
    $('#submitForm').click(function(event){
        msg = "";
        if ($("#articleValue").val() == ""){
                msg += "Object, ";
        }        
        // Updating popup text and link.
        if (msg == ""){
            $('#AddToBuyForm').submit();           
        }
        else{
            msg = msg.substring(0,msg.length - 2) + "."
            $( "#popupError #ErrorInput").html(msg);
            $('#popupError').popup("open");
        }
        console.log(msg);
        
        
        
        
    });
    
});//end of master function.
//$("input:checkbox").prop('checked', $(this).prop("checked"));

