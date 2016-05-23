$(function() {
  // Bind an event to window.onhashchange that, when the hash changes, gets the
  // hash and adds the class "selected" to any matching nav link.
  $( window ).hashchange(function() {
        var hash = location.hash.replace( /^#/, "" );
        if(hash=="save")
        {
            // console.log("Save Page");
            
            //Sets span values to input values for the different fields.
            $("#dateDesc").html($("#whenValue").val());
            $("#objectDesc").html($("#whatValue").val());
            $("#priceDesc").html($("#price").val());
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
  $(".autocomplete").click(
        function()
        {
            // console.log("Clicked link: "+$(this).text());
            $("#whatValue").val($(this).text());
            $(this).parent().parent().children().addClass("ui-screen-hidden"); //hide the autocomplete list.
        }
  );
  
  
  
});//end of master function.


