$(document).ready(function() {
    var get_data_starts_with = function ($obj, starts_with) {
        var result = {};
        var starts_with_len = starts_with.length;

        var data = $obj.data();
        for (var name in data)
            if (data.hasOwnProperty(name))
                if (name.substring(0, starts_with_len) == starts_with)
                    result[name.substring(starts_with_len).toLowerCase()] = $obj.data(name);

        return result;
    };

    $.fn.post_link = function () {
        $(this).each(function(){
            var $link = $(this);
            var url = $link.data('url');
            var parameters = get_data_starts_with($link, 'post');

            $link.click(function() {
                $.post(
                    url,
                    parameters
                ).done(function() {
                    /* Refresh on success */
                    window.location.reload(true);
                }).fail(function(xhr, text_status, error_thrown) {
                    show_message(xhr.responseText)
                });

                return false;
            })
        });
    };

    $('.post-link').post_link()
});
