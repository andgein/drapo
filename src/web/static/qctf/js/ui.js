function showModal(task_id) {
    $('.modal-task[data-id="' + task_id + '"]').css('display', 'flex');
}

function hideModal() {
    $('.modal-task').css('display', 'none');
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
});
