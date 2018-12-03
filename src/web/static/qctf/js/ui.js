function showModal(task_id) {
    $('.modal-task[data-id="' + task_id + '"]').css('display', 'flex');
}

function hideModal() {
    $('.modal-task').css('display', 'none');
    $('.modal-task .alert').hide();
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

function markAsSolved(task_id) {
    $('.task-info-container[data-id="' + task_id + '"] .solved-label').show();
    $('.card.task-info-container[data-id="' + task_id + '"]').addClass('solved');
}

function submitFlag(modal_task, task_id, form) {
    var alert = $(modal_task).find('.alert');
    alert.removeClass('alert-danger').removeClass('alert-success').addClass('alert-dismissible')
         .html('Проверка...')
         .show();
    var button = $(modal_task).find('button');
    button.attr('disabled', true);

    $.post("/api/submit_flag/" + task_id + "/", form.serialize())
        .done(function (response) {
            if (response.status === 'success') {
                markAsSolved(task_id);
                alert.removeClass('alert-dismissible').removeClass('alert-danger').addClass('alert-success');
            } else
                alert.removeClass('alert-dismissible').removeClass('alert-success').addClass('alert-danger');

            alert.html(response.message)
                 .show();
        })
        .fail(function () {
            alert.removeClass('alert-dismissible').removeClass('alert-success').addClass('alert-danger')
                 .html('Не удалось подключиться к серверу. Попробуйте ещё раз через некоторое время.')
                 .show();
        })
        .always(function () {
            button.removeAttr('disabled');
        });
}

function padLeft(number, length) {
    number = number.toString();
    for (var i = number.length; i < length; i++)
        number = '0' + number;
    return number;
}

function updateRemainingTime() {
    var finishTime = parseInt($('#contest-finish-time').text());
    var now = Math.round(new Date().getTime() / 1000);
    var remainingTimeSpan = $('#remaining-time');

    if (finishTime <= now) {
        remainingTimeSpan.text('Соревнование закончено');
        return;
    }
    var totalSeconds = finishTime - now;

    var seconds = totalSeconds % 60;
    var totalMinutes = Math.floor(totalSeconds / 60);
    var minutes = totalMinutes % 60;
    var hours = Math.floor(totalMinutes / 60);

    var timeRepr = padLeft(hours, 2) + ':' + padLeft(minutes, 2) + ':' + padLeft(seconds, 2);
    remainingTimeSpan.text('Осталось: ' + timeRepr);
}

function toggleHideOtherRegions() {
    $('tbody tr:not(.my-region)').toggle();
    $('tbody tr:visible').each(function (i, el) {
        if (i % 2 === 0)
            $(el).removeClass('odd').addClass('even');
        else
            $(el).removeClass('even').addClass('odd');
    });

    localStorage['hide-other-regions'] = $('#hide-other-regions').is(':checked');
}

$(function () {
    $('.article, .article-with-image').each(function (_, article) {
        var task_id = $(article).data('id');
        $(article).find('a').click(function (event) {
            showModal(task_id);
            event.preventDefault();
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

    var toggle = $('#hide-other-regions');
    if (localStorage['hide-other-regions'] === "true") {
        toggle.attr('checked', true);
        toggleHideOtherRegions();
    }
    toggle.change(toggleHideOtherRegions);

    $('.modal-task').each(function (_, el) {
        var task_id = $(this).data('id');
        var form = $(el).find('.submit-flag-form');
        form.submit(function (event) {
            submitFlag(el, task_id, form);
            event.preventDefault();
        });
    });

    updateRemainingTime();
    setInterval(updateRemainingTime, 1000);
});
