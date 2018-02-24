function showModal(task_id) {
    $('.modal-task[data-id="' + task_id + '"]').css('display', 'flex');
}

function hideModal() {
    $('.modal-task').css('display', 'none');
}

function update_unread_notifications_count() {
    return $.get("/api/unread_notifications_count/", function(data) {
        if (data['unread_count'])
            t = '(' + data['unread_count'] + ')';
        else
            t = '';
        $(".unread-count").html(t);
    });
}

$(function () {
    $('.article, .article-with-image').each(function (_, article) {
        var task_id = $(article).data('id');
        $(article).find('a').click(function () {
            showModal(task_id);
        });
    });
    $('.task-prices th').click(function () {
        var task_id = $(this).data('id');
        showModal(task_id);
    });

    $('.modal').click(function (e) {
        if ($(e.target).is('.modal'))
            hideModal();
    });
    $('button.close').click(hideModal);
    
    update_unread_notifications_count();
    setInterval(update_unread_notifications_count, 3*60*1000);

    $('#hide-other-regions').change(function () {
        $('tbody tr:not(.my-region)').toggle();
        $('tbody tr:visible').each(function (i, el) {
            if (i % 2 === 0)
                $(el).removeClass('odd').addClass('even');
            else
                $(el).removeClass('even').addClass('odd');
        });
    });
});
