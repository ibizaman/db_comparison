var get_json = function(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("get", url, true);
    xhr.responseType = "json";
    xhr.onload = function() {
        var status = xhr.status;
        if (status == 200) {
            callback(null, xhr.response);
        } else {
            callback(status);
        }
    };
    xhr.send();
};


var for_each = function(obj, callback) {
    for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
            callback(key, obj[key]);
        }
    }
};


function make_graphs(data) {
    for_each(data, function(group, subgroups) {
        for_each(subgroups, function(subgroup, timeseries) {
            new Dygraph(
                document.getElementById(group + '-' + subgroup),
                timeseries['data'],
                {
                    title: group + ': ' + subgroup,
                    labels: timeseries['labels'],
                    connectSeparatedPoints: true,
                    drawPoints: true
                }
            );
        })
    })
};

