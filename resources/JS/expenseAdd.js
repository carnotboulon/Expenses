//TODO: check value for all the fields before save.

$(function() {
  //Update summary page with form values.
  $( window ).hashchange(function() {
        var hash = location.hash.replace( /^#/, "" );
        if(hash=="save")
        {
            // console.log("Save Page");
            
            //Sets span values to input values for the different fields.
            $("#dateDesc").html($("#whenValue").val());
            $("#objectDesc").html($("#whatValue").val());
            $("#priceDesc").html($("#priceValue").val());
            // $("#shopDesc").html($("#shopSelector label[for='shop-"+$('#shopSelector :checked').val()+"']").text());
            $("#accountDesc").html($("select[name='account'] :selected").text());
            
            $("#benefDesc").html("");
            $("#benefValue :checked").each(
                function(index, element)
                {
                    var p = $("#benefValue label[for='person-"+$(this).val()+"']").text();
                    if (index == $("#benefValue :checked").length - 1) $("#benefDesc").append(p);
                    else $("#benefDesc").append(p+", ");
                }
            );   
        }    
  });
  // Since the event is only triggered when the hash changes, we need to trigger
  // the event now, to handle the hash the page may have loaded with.
  $( window ).hashchange();
  
  //OBJECT INPUT
  //Autocomplete expense object field.
  //Add the selected option to the text input
  //and hides the autocomplete list when option selected.
  $(".autocomplete").click(
        function()
        {
            //console.log("Clicked link: "+$(this).text());
            $("#whatValue").val($(this).text());
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
  //SHOP SELECTION. Add the selected option to the text input
  // $("input:radio[name='shopValue']").click(
        // function()
        // {
            // $("#filterShops").val($(this).siblings("label").text());
        // }
  // );
  
  //Button to check all persons in the Person tab.
  
    $('#menageSelect').change(function(){
        console.log($(this).is("checked"));
        $("input:checkbox[name='benefsValue']").prop('checked',$(this).prop("checked"));
        $("input:checkbox[name='benefsValue']").checkboxradio('refresh');        
    });
    
    //
    
    
    
    $('#submitForm').click(function(event){
        msg = "";
        if ($("#whatValue").val() == ""){
                
                msg += "Object, ";
        }
        if ($("#priceValue").val() == ""){
            msg += "Price, ";
        }
        if ($("input:checkbox[name='catValues']:checked").length == 0){
            msg += "Categories, ";
        }
        if ($("#whenValue").val() == ""){
            msg += "Date, ";
        }
        // if ($("input:radio[name='shopValue']:checked").length == 0){
            // msg += "Shop, ";
        // }
        if ($("input:checkbox[name='benefsValue']:checked").length == 0){
            msg += "Beneficiaries, ";
        }       
        
        // Updating popup text and link.
        if (msg == ""){
            $('#AddExpenseForm').submit();           
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

