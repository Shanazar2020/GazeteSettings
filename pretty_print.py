import json
from bs4 import BeautifulSoup as BS

BASE = ''


def get_settings(set_type='list'):
    global BASE
    with open('specific_settings.json', 'r') as f:
        data = json.load(f)

    BASE = data[0]['url']
    data = json.loads(data[0]['settings'])
    if set_type == 'list':
        data = data['list']
    else:
        data = data['content']
    return data


def get_html(html_type='list'):
    file = 'sample_html.html' if html_type == 'list' else 'sample_content.html'
    with open(file, 'r', encoding='utf-8') as f:
        return f.read()


def pretty_print(obj):
    print(json.dumps(obj, indent=4))


def get_list():
    settings = get_settings()
    html = get_html()
    soup = BS(html, 'lxml')

    if settings.get("TagCheck"):
        yep = soup.select_one(settings['TagCheck'])
        if yep:
            tags = yep.select(settings['TagList'])
            num = min(len(tags), int(settings.get("itemLimit", 0)))

            responses = {'data': list()}

            for i in range(num):
                item = tags[i]
                r = dict()

                r['url'] = item.select(settings['TagUrl'])
                if len(r['url']) > 0:
                    r['url'] = f"{BASE}{r['url'][settings['TagUrlIndex']]['href']}"
                else:
                    continue

                r['title'] = item.select_one(settings['TagTitle'])
                if r['title']:
                    r['title'] = r['title'].get_text()

                if settings['isYazarMust']:
                    r['yazar'] = item.select_one(settings['TagYazar']).get_text()

                r['img'] = item.select_one(settings['TagImg'])
                if r['img']:
                    r['img'] = r['img'].get('data-src')

                if settings['TagDesc']:
                    r['desc'] = item.select_one(settings['TagDesc']).get_text()

                responses['data'].append(r)

            pretty_print(responses)


def get_content():
    settings = get_settings(set_type='content')
    html = get_html(html_type='content')
    soup = BS(markup=html, features='lxml')
    main = soup.select_one(settings['TagHolder'])
    responses = {'data': list()}

    if main:
        r = dict()
        if settings['TagYazar']:
            yazar = main.select_one(settings['TagYazar'])
            if yazar:
                r['yazar'] = yazar.get_text()

        if settings['TagImg']:
            img = main.select_one(settings['TagImg'])
            if img:
                if img.has_attr('src'):
                    img = img.get('src')
                elif img.has_attr('data-src'):
                    img = img.get('data-src')

                r['img'] = img

        if settings['TagTitle']:
            title = soup.select_one(settings['TagTitle'])
            if title:
                r['title'] = title.get_text()

        if settings['TagDesc']:
            desc = soup.select_one(settings['TagDesc'])
            if desc:
                r['desc'] = desc.get_text()

        if not settings["isContentNone"] and settings['TagContent']:
            remove = settings['TagsRemove']
            if remove:
                for removal in main.select(remove):
                    if removal:
                        removal.decompose()

            is_paragraph = settings['isContentParagraph']
            if is_paragraph:
                body = soup.select_one(settings['TagContent'])
                if body:
                    r['content'] = body.get_text()[:100]
            else:
                body_elements = soup.select(settings['TagContent'])

                if body_elements:
                    r['content'] = ''.join([body.get_text()[:10] for body in body_elements if body])
        responses['data'].append(r)

    pretty_print(settings)
    pretty_print(responses)


if __name__ == '__main__':
    get_list()

    get_content()

# print(settings)
# print(soup.is_xml)

# class HtmlContent:
#     data: str
#
#     @staticmethod
#     def get(selector):
#
#         pass
#
#     def get_list(selector):
#
#     pass
#
#
# class Settings:
#     pass
#
#
# class Response:
#     pass
