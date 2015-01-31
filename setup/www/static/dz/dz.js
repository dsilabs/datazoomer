
    function toggle_flag(){
        var title = $(this).attr('title'),
            icon = $(this).attr('icon'),
            url = $(this).attr('url');
        $.post('/flags/toggle', {'TITLE': title, 'URL': url, 'ICON': icon } );
        $(this).toggleClass(icon+'_on');
    }

    $(function() {

        $('.date_field').datepicker({ dateFormat: 'M d, yy', changeMonth: true, changeYear: true });

        $('.birthdate_field').datepicker({ dateFormat: 'M d, yy', changeMonth: true, changeYear: true, yearRange: '-120:+00' });

        if ( $('.chosen').length > 0 ) { $('.chosen').chosen(); };

        $('.flag').click(toggle_flag);

        var pb_target = document.getElementById('spinner');
        if (pb_target) {
            var opts = {
              lines: 9, // The number of lines to draw
              length: 11, // The length of each line
              width: 4, // The line thickness
              radius: 12, // The radius of the inner circle
              corners: 1, // Corner roundness (0..1)
              rotate: 0, // The rotation offset
              color: '#000', // #rgb or #rrggbb
              speed: 1, // Rounds per second
              trail: 60, // Afterglow percentage
              shadow: false, // Whether to render a shadow
              hwaccel: false, // Whether to use hardware acceleration
              className: 'spinner', // The CSS class to assign to the spinner
              zIndex: 2e9, // The z-index (defaults to 2000000000)
              top: 'auto', // Top position relative to parent in px
              left: 'auto' // Left position relative to parent in px
            };
           var spinner = new Spinner(opts).spin(pb_target); 
        };

    });


         
