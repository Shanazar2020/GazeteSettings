import json
from abc import ABC, abstractmethod
from typing import Callable

from bs4 import BeautifulSoup, Tag
from flask import Flask, request, jsonify
from pymongo import MongoClient
import re


def get_source_info_from_db(id_):
    if id_:
        try:
            # TODO Need to change according to the environment
            client = MongoClient("localhost", 27017)
            db = client['news']
            collection = db['source_settings']
            document = collection.find_one({"ID": id_})
            return document
        except Exception as e:
            print(e)
            raise e
    return None


class SettingsParser(object):
    delete_regex = r'\((.*?)\)'
    default_regex = r'"(.*?)"'
    valid_regex = r'"(.*?)"|\((.*?)\)'

    @staticmethod
    def _non_checker(func):
        def wrapper(self, *args, **kwargs):
            dict_result = func(self, *args, **kwargs)
            if any(dict_result.values()):
                return dict_result
            return None

        return wrapper

    @staticmethod
    def __extract_pattern(pattern, text):
        match = re.match(pattern, text)
        if match:
            return match.group(1)

    @classmethod
    def _extract_delete(cls, text):
        all_match = re.findall(cls.delete_regex, text)
        if all_match:
            return ','.join(all_match)

    @classmethod
    def _extract_default(cls, text):
        result = re.search(cls.default_regex, text)
        if result:
            return result.group(1)

    @classmethod
    def _extract_valid(cls, text):
        text = re.sub(cls.valid_regex, '', text)
        return re.sub(r"  ", '', text)

    @classmethod
    def _extract_tag_attr_pairs(cls, text_list: list[str], default_attr):
        result = []
        for text in text_list:
            split = text.split('>')
            if len(split) == 1:
                split.append(default_attr)
            result.append(split)

        return result

    def parse_url_selector(self, selector: str, default_attr: str) -> list[dict]:
        if not selector:
            return []
        pairs = self._extract_tag_attr_pairs(selector.split(','), default_attr)
        result = []
        for pair in pairs:
            parsed_pair = {
                "tag": pair[0],
                "attr": pair[1]
            }
            result.append(parsed_pair)
        return result

    @_non_checker
    def parse_text_selector(self, css_selector: str) -> dict:
        parsed = {
            "delete": self._extract_delete(css_selector),
            "default": self._extract_default(css_selector),
            "select": self._extract_valid(css_selector)
        }
        return parsed

    def parse_article_url_selector(self, css_selector: str) -> list[dict]:
        return self.parse_url_selector(css_selector, 'href')

    def parse_img_url_selector(self, css_selector: str) -> list[dict]:
        return self.parse_url_selector(css_selector, 'src')


class Settings(ABC):
    class Keys:
        check = 'c'
        title = 't'
        yazar = 'y'
        img = 'i'
        desc = 'd'

    def __init__(self, _id):
        self._id = _id
        self.parser = SettingsParser()
        source = self.__get_source_info()

        self._gazete = source.get('gazete')
        self._base_url = source.get('url')
        self._country = source.get('country')
        self._settings = self._get_settings(source)

        print(f"{self._base_url}  Before Parsing:")
        self.print_parsers()

        self._parse_settings()

        print(f"After Parsing: ")
        self.print_parsers()

    def print_parsers(self):
        # print(f"{self.title}, {self.yazar}, {self.desc}, {self.img}")
        pass

    def __get_source_info(self) -> dict:
        return get_source_info_from_db(self._id)

    @abstractmethod
    def _get_settings(self, sources) -> dict:
        pass

    def _parse_settings(self):
        self.title = self.parser.parse_text_selector(self.title)
        self.yazar = self.parser.parse_text_selector(self.yazar)
        self.desc = self.parser.parse_text_selector(self.desc)
        self.img = self.parser.parse_img_url_selector(self.img)

    @property
    def check(self):
        return self._settings[self.Keys.check]

    @property
    def img(self):
        return self._settings[self.Keys.img]

    @img.setter
    def img(self, value):
        self._settings[self.Keys.img] = value

    @property
    def title(self):
        return self._settings[self.Keys.title]

    @title.setter
    def title(self, value):
        self._settings[self.Keys.title] = value

    @property
    def yazar(self):
        return self._settings[self.Keys.yazar]

    @yazar.setter
    def yazar(self, value):
        self._settings[self.Keys.yazar] = value

    @property
    def desc(self):
        return self._settings[self.Keys.desc]

    @desc.setter
    def desc(self, value):
        self._settings[self.Keys.desc] = value

    @property
    def settings(self):
        return self._settings


class ArticleListSettings(Settings):
    class ListKeys:
        list = 'l'
        url = 'u'
        url_index = 'u_i'
        item_limit = 'i_l'

    def _parse_settings(self):
        super()._parse_settings()
        self.url = self.parser.parse_article_url_selector(self.url)

    def print_parsers(self):
        # super().print_parsers()
        print(f"{self.img} {self.url}")

    @property
    def list(self):
        return self._settings[self.ListKeys.list]

    @property
    def url(self):
        return self._settings[self.ListKeys.url]

    @url.setter
    def url(self, value):
        self._settings[self.ListKeys.url] = value

    @property
    def url_index(self):
        return self._settings[self.ListKeys.url_index]

    @property
    def item_limit(self):
        return int(self.settings[self.ListKeys.item_limit])

    def __init__(self, s_id):
        self.mappings = {
            self.Keys.check: 'TagCheck',
            self.Keys.img: 'TagImg',
            self.Keys.yazar: 'TagYazar',
            self.Keys.title: 'TagTitle',
            self.Keys.desc: 'TagDesc',
            self.ListKeys.list: 'TagList',
            self.ListKeys.url: 'TagUrl',
            self.ListKeys.url_index: 'TagUrlIndex',
            self.ListKeys.item_limit: 'itemLimit'
        }
        super().__init__(s_id)

    def _get_settings(self, sources) -> dict:
        new_settings = {}
        if sources:
            prev_settings = json.loads(sources.get('settings', '{}')).get('list', {})
            for new_key, old_key in self.mappings.items():
                new_settings[new_key] = prev_settings.get(old_key)

        return new_settings


class ArticleContentSettings(Settings):
    class ContentKeys:
        content = 'con'
        is_content_p = 'is_c_p'
        is_content_none = 'is_c_n'
        remove_tags = 'r_t'

    def __init__(self, s_id):
        self.mappings = {
            self.Keys.check: 'TagHolder',
            self.Keys.img: 'TagImg',
            self.Keys.yazar: 'TagYazar',
            self.Keys.title: 'TagTitle',
            self.Keys.desc: 'TagDesc',
            self.ContentKeys.content: 'TagContent',
            self.ContentKeys.is_content_p: 'isContentParagraph',
            self.ContentKeys.is_content_none: 'isContentNone',
            self.ContentKeys.remove_tags: 'TagsRemove'
        }
        super().__init__(s_id)

    @property
    def content(self):
        return self._settings[self.ContentKeys.content]

    @property
    def is_content_p(self):
        return self._settings[self.ContentKeys.is_content_p]

    @property
    def is_content_none(self):
        return self._settings[self.ContentKeys.is_content_none]

    @property
    def remove_tags(self):
        return self._settings[self.ContentKeys.remove_tags]

    def _get_settings(self, sources) -> dict:
        new_settings = {}
        if sources:
            prev_settings = json.loads(sources.get('settings', {})).get('content', {})
            for new_key, old_key in self.mappings.items():
                new_settings[new_key] = prev_settings.get(old_key)

        return new_settings


class Cleaner:

    def __init__(self):
        self.patterns = ['\n', '  ']  # patterns to replace with corresponding replacements in text
        self.replacements = ['', ' ']  # replacements to use
        self.cleaning_functions = [self.remove_by_prefix, self.remove, self.strip_whitespace]

    def clean_text(self, text):
        cleaning_function: Callable
        for cleaning_function in self.cleaning_functions:
            text = cleaning_function(text)
        return text

    def strip_whitespace(self, text):
        return text.strip()

    def remove(self, text):
        for pattern, replacement in zip(self.patterns, self.replacements):
            text = re.sub(pattern, replacement, text)
        return text

    def remove_by_prefix(self, text: str):
        if text.startswith('By'):
            return self.strip_whitespace(text[2:])
        return text


class HTMLContent(ABC):
    cleaner = Cleaner()

    def __init__(self, content, settings: Settings | ArticleListSettings | ArticleContentSettings):
        self.settings = settings
        self.content = BeautifulSoup(markup=content, features='lxml')

    def checked(self) -> bool:
        checked_content = self.content.select_one(self.settings.check)
        if checked_content:
            self.content = checked_content
            return True
        return False

    @staticmethod
    def apply_cleaner(text_extract_func):
        def wrapper(self, *args, **kwargs):
            text = text_extract_func(self, *args, **kwargs)
            return self.cleaner.clean_text(text)

        return wrapper

    def __remove(self, selector, content=None):
        if not content:
            content = self.content
        for removal in content.select(selector):
            if removal:
                removal.decompose()

    @apply_cleaner
    def __extract_single_text(self, selector):
        def delete_unwanted_elements():
            if text_holder and selector['delete']:
                self.__remove(selector['delete'], text_holder)

        def get_text_or_default():
            return text_holder.get_text() if text_holder and text_holder.get_text() else selector['default']

        try:
            if selector['select']:
                text_holder = self.content.select_one(selector['select'])
                delete_unwanted_elements()
                return get_text_or_default()
            else:
                return selector['default']
        except Exception as e:
            print(e)

    def __extract_single_url(self, selectors: list[dict]):
        try:
            for selector in selectors:
                url_holder = self.content.select_one(selector['tag'])
                if url_holder:
                    url = url_holder.get(selector['attr'])
                    return url

        except Exception as e:
            print(e)
        return None

    def get_title(self) -> str:
        if self.settings.title:
            return self.__extract_single_text(self.settings.title)
        return ""

    def get_yazar(self) -> str:
        if self.settings.yazar:
            # print("yazar exists")
            return self.__extract_single_text(self.settings.yazar)
        return ""

    def get_desc(self):
        if self.settings.desc:
            return self.__extract_single_text(self.settings.desc)

    def get_img(self) -> str:
        if self.settings.img:
            return self.__extract_single_url(self.settings.img)

    @abstractmethod
    def get_main_content(self):
        pass


class ArticleListHtml(HTMLContent):

    def __init__(self, content, settings: ArticleListSettings):
        super().__init__(content, settings)

    def __get_list(self, selector) -> list:
        try:
            elements = self.content.select(selector)
            return elements or []
        except Exception as e:
            print(e)
        return []

    def get_item_list(self) -> list['ArticleListHtml']:
        self.settings: ArticleListSettings
        results = []
        if self.settings.list:
            items = self.__get_list(self.settings.list)
            limit = min(len(items), self.settings.item_limit)

            results = [ArticleListHtml(str(items[i]), self.settings) for i in range(limit) if items[i]]

        return results

    def __get_url_at_index(self, selectors: list[dict], index: int = 0) -> str | None:
        try:
            for selector in selectors:
                url_holders = self.content.select(selector['tag'])
                if url_holders and len(url_holders) > index:
                    url_holder = url_holders[index]
                    if url_holder:
                        url = url_holder.get(selector['attr'])
                        if url:
                            return url
        except Exception as e:
            print(e)
        return None

    def get_main_content(self):
        self.settings: ArticleListSettings
        if self.settings.url:
            return self.__get_url_at_index(self.settings.url, self.settings.url_index)


class ArticleContentHtml(HTMLContent):

    def __init__(self, content, settings: ArticleContentSettings):
        super().__init__(content, settings)

    def __get_content(self):
        self.settings: ArticleContentSettings
        if self.settings.remove_tags:
            self.__remove(self.settings.remove_tags)

        content_holders = self.content.select(self.settings.content)
        if content_holders:
            content = ''.join(holder.get_text() for holder in content_holders if holder)
            return content

    def get_main_content(self):
        try:
            self.settings: ArticleContentSettings
            if not self.settings.is_content_none and self.settings.content:
                return self.__get_content()
            return ""

        except Exception as e:
            print(e)


class Response(ABC):
    title_key = "title"
    yazar_key = "yazar"
    img_key = "img"
    desc_key = "desc"

    def __init__(self):
        self.data = list()
        self.content_key = self.get_main_content_key()
        self._built_data = dict()

    def add_data(self, title, yazar, img, desc, content):
        data = {
            self.title_key: title,
            self.yazar_key: yazar,
            self.img_key: img,
            self.desc_key: desc,
            self.content_key: content
        }
        self.data.append(data)

    def get_response(self):
        return [{'data': self.data}]

    @abstractmethod
    def get_main_content_key(self):
        pass


class ArticleListResponse(Response):
    key = 'url'

    def __init__(self):
        super().__init__()

    def get_main_content_key(self):
        return self.key


class ArticleContentResponse(Response):
    key = 'content'

    def __init__(self):
        super().__init__()

    def get_main_content_key(self):
        return self.key


class Builder:
    @staticmethod
    def build_article_list_request(html: str, source_id: int):
        settings = ArticleListSettings(source_id)
        content = ArticleListHtml(content=html, settings=settings)
        response = ArticleListResponse()
        return content, response

    @staticmethod
    def build_article_content_request(html: str, source_id: int):
        print("Content builder")
        settings = ArticleContentSettings(source_id)
        print(settings.settings)
        content = ArticleContentHtml(content=html, settings=settings)
        response = ArticleContentResponse()
        return content, response


def process_request_common(content: HTMLContent | ArticleContentHtml | ArticleListHtml, response: Response):
    if True and content.checked():
        items = content.get_item_list() if hasattr(content, 'get_item_list') else [content]
        for item in items:
            title = item.get_title()
            yazar = item.get_yazar()
            img = item.get_img()
            desc = item.get_desc()
            content = item.get_main_content()
            response.add_data(title, yazar, img, desc, content)

    return response.get_response()


def process_list_request(html: str, source_id: int):
    content, response = Builder.build_article_list_request(html, source_id=source_id)
    return process_request_common(content, response)


def process_content_request(html: str, source_id: int):
    content, response = Builder.build_article_content_request(html, source_id)
    return process_request_common(content, response)


def process_request(r_type: str, content: str, source_id: int):
    if r_type == 'list':
        result = process_list_request(content, source_id)
    else:
        result = process_content_request(content, source_id)

    return result


if __name__ == '__main__':
    app = Flask(__name__)

    # TODO need to change url
    @app.route('/content', methods=['POST'])
    def my_route():
        data = request.get_json()
        type_ = data.get('type')
        content = data.get('content')
        s_id = data.get('s_id')

        response = process_request(type_, content, s_id)
        return jsonify(response)

    # TODO need to change port number, debug=True => changes applied while running
    app.run(host='localhost', port=5000, debug=True)
