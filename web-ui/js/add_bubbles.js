$(document).ready(function () {
    $('.ne').tipsy({html: true,
                    fallback: 'Where my tooltip?',
                    opacity: 1,
                    title: function () {
                        var d = $(this).data();
                        res = '<dl>';
                        for (k in d) {
                            if (k == 'tipsy') {
                                continue;
                            }
                            var v = $(this).data(k);
                            res += '<dt>'+k+'</dt><dd>'+v+'</dd>';
                        }
                        res += '</dl>'
                        return res;
                    }});
});
