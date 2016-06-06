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
            $("#shopDesc").html($("#shopSelector label[for='shop-"+$('#shopSelector :checked').val()+"']").text());
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
  
  //Autocomplete expense object field.
  //Add the selected option to the text input
  //and hides the autocomplete list when option selected.
  $(".autocomplete").click(
        function()
        {
            // console.log("Clicked link: "+$(this).text());
            $("#whatValue").val($(this).text());
            $(this).parent().parent().children().addClass("ui-screen-hidden"); //hide the autocomplete list.
        }
  );
  
  //Button to check all persons in the Person tab.
  
    $('#menageSelect').change(function(){
        console.log($(this).is("checked"));
        $("input:checkbox[name='benefsValue']").prop('checked',$(this).prop("checked"));
        $("input:checkbox[name='benefsValue']").checkboxradio('refresh');        
    });
  
});//end of master function.
//$("input:checkbox").prop('checked', $(this).prop("checked"));

