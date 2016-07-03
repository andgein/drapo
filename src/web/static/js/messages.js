/* Activates bootstrap-notify
 * See documentation at http://bootstrap-notify.remabledesigns.com/
 * */

function show_message(message, type, delay) {
    type = type || 'info';
    delay = delay || 2000;

    $.notify({
        message: message
    }, {
        type: type,
        delay: delay,
        showProgressbar: true,
        mouse_over: 'pause',
        newest_on_top: true,
        template: '<div data-notify="container" class="col-xs-11 col-sm-3 alert alert-message alert-message-{0}" role="alert">' +
            '<button type="button" aria-hidden="true" class="close" data-notify="dismiss">×</button>' +
            '<span data-notify="title">{1}</span>' +
            '<span data-notify="message">{2}</span>' +
        '</div>'
    })
}

$(document).ready(function(){
    $('.messages .message').each(function(){
        var $msg = $(this);
        var type = '';
        if ($msg.hasClass('info')) type = 'info';
        if ($msg.hasClass('error')) type = 'danger';
        if ($msg.hasClass('warning')) type = 'warning';
        if ($msg.hasClass('success')) type = 'success';

        show_message($msg.html(), type);
    })
})