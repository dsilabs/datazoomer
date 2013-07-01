
    function select_apps(selected){
        $('div#selected ul li').hide();
        $('div#selected ul li.select-' + selected).fadeIn('fast');
    };

    function select_item(){
        $('div.selector ul li').removeClass('current');
        $(this).addClass('current');

        select_apps($(this).attr('id'));

        return false;
    };

    $(function() {
        select_apps('your-apps');
        $('div.selector ul li').click(select_item);
    });

