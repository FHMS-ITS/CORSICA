var intervals = {};

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


function refresh_job_table() {
    $.ajax({
        url: '/api/jobs/',
        method: 'GET',
        data: {'humanize': true, 'limit': 3},
        dataType: 'json',
        success: function (data) {
            $('#tbl_job tbody').empty();

            $.each(data['data'], function (i, item) {

                var tr = $('<tr>');

                switch (item.status) {
                    case -1:
                        tr.addClass("table-danger");
                        break;
                    case 5:
                        tr.addClass("table-success");
                        break;
                    default:
                        tr.addClass("table-warning");
                }
                tr.append(
                    $('<td>').text(item.id),
                    $('<td>').text(item.creation),
                    $('<td>').text(item.service),
                    $('<td>').text(item.action),
                    $('<td>').text(item.status)
                );

                var btn_details = $('<a>');
                btn_details.html("&nbsp;<i style=\"color:#fff;\" class=\"fas fa-info\"></i>&nbsp;");
                btn_details.addClass('btn btn-dark btn-sm');
                btn_details.attr("data-toggle", "modal");
                btn_details.attr("data-target", "#job-detail-modal");
                btn_details.attr("data-job-id", item.id);


                var btn_del = $('<button>');
                btn_del.html("&nbsp;<i class=\"fas fa-trash\"></i>&nbsp;");
                btn_del.addClass('btn btn-sm');
                if (item.status === 0) {
                    btn_del.click(function () {
                        delete_job($(this).data('job-id'));
                    });
                    btn_del.attr('data-job-id', item.id);
                    btn_del.addClass('btn-danger');
                } else {
                    btn_del.addClass('disabled');
                }

                tr.append($('<td>').append(btn_details).append('&nbsp;&nbsp;').append(btn_del));
                $('#tbl_job tbody').append(tr);

            });
        }
    });
};

function add_job(service, action, in_data={}) {
    $.ajax({
        url: '/api/jobs/',
        method: 'POST',
        data: {
            'service': service,
            'action': action,
            'in_data': JSON.stringify(in_data)
        },
        dataType: 'json',
        success: function (data) {
            $.notify({
                message: 'Job Created'
            },{
                type: 'success',
                placement: {'from': 'top'},
                offset: {'x': 20, 'y':60},
                delay: 2000
            });
            refresh_job_table()
        }
    });
}

function delete_job(job_id) {
    $.ajax({
        url: '/api/jobs/' + job_id,
        method: 'DELETE',
        data: {
            'job_id': job_id
        },
        dataType: 'json',
        success: function (data) {
            refresh_job_table()
        }
    });
}

function add_shodan_query(query) {
    $.ajax({
        url: '/api/shodan/query/',
        method: 'POST',
        data: {
            'query': query
        },
        dataType: 'json',
        success: function (data) {
            location.reload();
        }
    });
}

function delete_shodan_query(query_id) {
    $.ajax({
        url: '/api/shodan/query/' + query_id,
        method: 'DELETE',
        data: {
            'job_id': query_id
        },
        dataType: 'json',
        success: function (data) {
            location.reload();
        }
    });
}

function get_log_content(log_file) {
    $.ajax({
        url: '/api/log_view/',
        method: 'GET',
        data: {
            'log_file': log_file
        },
        dataType: 'json',
        success: function (data) {
            var log_content_pre = $('#log_content');
            log_content_pre.text(data['data']);
            log_content_pre.scrollTop(log_content_pre.prop("scrollHeight"));

        }
    });
}

function register_ajax_interval(id, func, timeout) {
    clear_ajax_interval(id);
    intervals[id] = setInterval(func, timeout);
    eval(func);
}

function clear_ajax_interval(id) {
    if (id in intervals) {
        window.clearInterval(intervals[id]);
        delete intervals[id];
    }
}

function get_ajax_interval_status(id) {
    if (id in intervals)
        return true;
    return false
}



function refresh_cpu_info() {
    $.ajax({
        url: '/api/cpu_mem_info_view/',
        method: 'GET',
        data: {'humanize': true, 'limit': 3},
        dataType: 'json',
        success: function (data) {

        }
    });
};