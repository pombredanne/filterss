# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, make_response, abort
from filterss import app
from forms import FilterForm
from helpers import get_url, url_vars, set_filter, connect_n_parse
from helpers import remove_tags, test_cond, word_wrap, format_date, test_url
import sys
import urllib

reload(sys)
sys.setdefaultencoding('utf-8')


@app.route('/')
@app.route('/index')
def index():
    form = FilterForm()
    return render_template('form.html', form=form)


@app.route('/filter', methods=('GET', 'POST'))
def filter():
    form = FilterForm()
    if form.validate_on_submit():
        url = get_url(form.rss_url.data)
        url_query = url_vars(
            url,
            form.title_inc.data,
            form.title_exc.data,
            form.link_inc.data,
            form.link_exc.data)
        return redirect('/info?' + url_query)
    return render_template('form.html', form=form)


@app.route('/rss')
def rss():

    # load GET vars
    url = set_filter(request.args.get("url"))
    t_inc = set_filter(request.args.get("title_inc"))
    t_exc = set_filter(request.args.get("title_exc"))
    l_inc = set_filter(request.args.get("link_inc"))
    l_exc = set_filter(request.args.get("link_exc"))

    # load orginal RSS (xml)
    try:
        dom = connect_n_parse(url)
    except:
        return abort(500)

    # loop items
    for item in dom.getElementsByTagName('item'):

        # get title & link
        title = item.getElementsByTagName('title')[0].toxml()
        link = item.getElementsByTagName('link')[0].toxml()
        title = remove_tags(title)
        link = remove_tags(link)

        # test conditions
        cond1 = test_cond(t_inc, title, True)
        cond2 = test_cond(t_exc, title, False)
        cond3 = test_cond(l_inc, link, True)
        cond4 = test_cond(l_exc, link, False)

        # delete undesired nodes
        if not cond1 or not cond2 or not cond3 or not cond4:
            item.parentNode.removeChild(item)

    # print RSS (xml)
    filtered = dom.toxml()
    response = make_response(filtered)
    response.headers["Content-Type"] = "application/xml"
    return response


@app.route('/info')
def info():

    # load GET vars
    url = set_filter(request.args.get("url"))
    t_inc = set_filter(request.args.get("title_inc"))
    t_exc = set_filter(request.args.get("title_exc"))
    l_inc = set_filter(request.args.get("link_inc"))
    l_exc = set_filter(request.args.get("link_exc"))
    rss_url = request.url_root + 'rss?'
    rss_url = rss_url + url_vars(url, t_inc, t_exc, l_inc, l_exc)
    rss_url_encoded = urllib.quote(rss_url)

    # load orginal RSS (xml)
    try:
        dom = connect_n_parse(url)
    except:
        url_query = url_vars(url, t_inc, t_exc, l_inc, l_exc)
        return redirect('/error?' + url_query)

    # get title
    rss_title = dom.getElementsByTagName('title')[0].toxml()
    rss_title = remove_tags(rss_title)

    # loop items
    all_items = []
    filtered_items = []
    for item in dom.getElementsByTagName('item'):

        # get title & link
        title = item.getElementsByTagName('title')[0].toxml()
        link = item.getElementsByTagName('link')[0].toxml()
        date = item.getElementsByTagName('pubDate')[0].toxml()
        title = remove_tags(title)
        link = remove_tags(link)
        date = remove_tags(date)

        # test conditions
        cond1 = test_cond(t_inc, title, True)
        cond2 = test_cond(t_exc, title, False)
        cond3 = test_cond(l_inc, link, True)
        cond4 = test_cond(l_exc, link, False)

        # sort nodes
        item_class = 'skip'
        item = {'title': title,
                'title_wrap': word_wrap(title),
                'url': link,
                'date': format_date(date),
                'css_class': item_class}
        if cond1 and cond2 and cond3 and cond4:
            filtered_items.append(item)
            item['css_class'] = ''
        all_items.append(item)

    return render_template(
        'info.html',
        url=url,
        rss_title=rss_title,
        rss_url=rss_url,
        rss_url_encoded=rss_url_encoded,
        all_items=all_items,
        filtered_items=filtered_items)


@app.route('/check_url', methods=['GET'])
def check_url():
    url = request.args.get('url')
    return str(test_url(url))


@app.route('/robots.txt', methods=['GET'])
def sitemap():
    response = make_response(open('robots.txt').read())
    response.headers["Content-type"] = "text/plain"
    return response


@app.route('/error')
def error():
    url = str(request.args.get("url"))
    return render_template('error.html', url=url)


@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html'), 500
