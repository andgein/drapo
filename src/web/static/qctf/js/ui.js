$(function () {
    $('.article, .article-with-image').each(function (_, article) {
        var task_id = $(article).data('id');
        $(article).find('a').click(function () {
            $('.modal-task[data-id="' + task_id + '"]').css('display', 'flex');
        });
    });
    $('.task-prices th').click(function () {
        var task_id = $(this).data('id');
        $('.modal-task[data-id="' + task_id + '"]').css('display', 'flex');
    });
});
